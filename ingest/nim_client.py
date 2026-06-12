"""
ingest.nim_client — thin async httpx client for the NVIDIA NeMo Embedding NIM.

Handles batching, per-request rate limiting, and exponential-backoff retry so
callers never need to think about NIM API quotas.

Public API
----------
    embed_texts(texts, input_type, batch_size) -> list[list[float]]

Design notes (see also ADR-003):
  - nv-embedqa-e5-v5 is an asymmetric QA model.  Passage vectors and query
    vectors are produced by different projection heads.  Mixing them silently
    degrades recall, so ``input_type`` is an explicit parameter — never inferred.
  - Batching: the NVIDIA free tier accepts up to 50 texts per request.
    ``embed_texts`` splits large inputs into ``batch_size``-sized batches.
  - Throttle: the free tier is capped at 40 RPM.  We budget 36 RPM (10%
    headroom) and sleep ``_MIN_INTERVAL_S`` between consecutive requests.
    Proactive throttling is cheaper than burning retry budget on self-inflicted
    429s.
  - Retry: 429 and 5xx trigger exponential backoff (1 s, 2 s, 4 s) up to
    ``_MAX_RETRIES`` attempts, then raise ``EmbeddingError``.
  - Order guarantee: a pre-allocated result list is indexed by original position;
    each batch's response is sorted by the NIM-returned ``index`` field before
    being slotted back.  chunk[i] always gets vector[i].
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Final, Literal, TypedDict

import httpx
import structlog

from config.settings import get_settings
from ingest.errors import EmbeddingError

logger: structlog.BoundLogger = structlog.get_logger(__name__)

InputType = Literal["passage", "query"]

# WHY: the free-tier NIM API is capped at 40 RPM.  We budget 36 RPM (10% headroom)
# so occasional clock skew or pipelining jitter never pushes us over the limit.
# One request per _MIN_INTERVAL_S = 60 / 36 ≈ 1.667 s keeps us safely at 36 RPM.
_RPM_BUDGET: Final[int] = 36
_MIN_INTERVAL_S: Final[float] = 60.0 / _RPM_BUDGET  # ≈ 1.667 s

_DEFAULT_BATCH_SIZE: Final[int] = 50  # NVIDIA free tier: max ~50 texts per request
_MAX_RETRIES: Final[int] = 3
_RETRY_BASE_S: Final[float] = 1.0


# ---------------------------------------------------------------------------
# Response shape (OpenAI-compatible /embeddings endpoint)
# ---------------------------------------------------------------------------


class _EmbeddingItem(TypedDict):
    index: int
    embedding: list[float]
    object: str


class _EmbeddingsResponse(TypedDict):
    data: list[_EmbeddingItem]
    model: str
    object: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def embed_texts(
    texts: list[str],
    input_type: InputType = "passage",
    batch_size: int = _DEFAULT_BATCH_SIZE,
) -> list[list[float]]:
    """Embed a list of texts using the NVIDIA NeMo Embedding NIM.

    Texts are split into batches of ``batch_size``, sent as separate HTTP
    requests, and rate-limited to stay within the free-tier 40 RPM cap.

    WHY input_type is explicit: nv-embedqa-e5-v5 is an asymmetric model with
    separate projection heads for "passage" (documents) and "query" (search
    queries).  Passage vectors and query vectors live in different subspaces —
    mixing them silently breaks cosine similarity and degrades retrieval.
    Callers MUST pass "passage" when embedding document chunks and "query"
    when embedding a user search query.

    Args:
        texts:      Strings to embed.  Empty list returns [].
        input_type: "passage" for document chunks; "query" for search queries.
        batch_size: Max texts per HTTP request (default 50 for the free tier).

    Returns:
        A list of float vectors with len == len(texts), in the same order as
        the input.  chunk[i] always gets vector[i].

    Raises:
        EmbeddingError: On permanent failure after ``_MAX_RETRIES`` retries, or
                        on an unexpected response shape from the NIM.
    """
    if not texts:
        return []

    settings = get_settings()
    api_key = settings.nim_api_key.get_secret_value()
    base_url = settings.nim_embed_base_url
    model = settings.nim_embed_model

    batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
    total_batches = len(batches)

    log = logger.bind(
        model=model,
        input_type=input_type,
        total_texts=len(texts),
        total_batches=total_batches,
    )
    log.info("nim_client.embed_start")
    t0 = time.monotonic()

    # Collect each batch's result list in order, then flatten.
    # WHY sequential append (not pre-allocated slots): batches are processed one-at-a-time
    # so order is guaranteed by append sequence; each batch's response is additionally
    # sorted by its own index field before appending.
    batched_vectors: list[list[list[float]]] = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for batch_idx, batch in enumerate(batches):
            vectors = await _embed_batch_with_retry(
                client=client,
                base_url=base_url,
                api_key=api_key,
                model=model,
                batch=batch,
                input_type=input_type,
                batch_idx=batch_idx,
                total_batches=total_batches,
            )
            batched_vectors.append(vectors)

            # Throttle between batches to stay within _RPM_BUDGET.
            # WHY: sleep AFTER processing (not before) so the first request fires immediately.
            # No sleep after the final batch — callers shouldn't pay for idle time.
            if batch_idx < total_batches - 1:
                await asyncio.sleep(_MIN_INTERVAL_S)

    # Flatten in input order — sequential processing guarantees batch i precedes batch i+1
    final: list[list[float]] = [vec for batch in batched_vectors for vec in batch]

    elapsed = time.monotonic() - t0
    # nim_cost_log hook: log texts_embedded + model so cost-accounting tooling can
    # aggregate NIM usage across calls without parsing arbitrary log lines.
    log.info(
        "nim_client.embed_done",
        texts_embedded=len(texts),
        elapsed_s=round(elapsed, 3),
        nim_cost_log=True,
    )
    return final


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _embed_batch_with_retry(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    model: str,
    batch: list[str],
    input_type: InputType,
    batch_idx: int,
    total_batches: int,
) -> list[list[float]]:
    """POST one batch to /embeddings and retry on 429 / 5xx.

    Retries up to ``_MAX_RETRIES`` times with exponential backoff starting at
    ``_RETRY_BASE_S`` seconds.  Non-retryable status codes (4xx except 429)
    raise immediately.

    Args:
        client:        Shared httpx.AsyncClient (connection pool reuse).
        base_url:      NIM base URL (no trailing slash).
        api_key:       NVIDIA NIM bearer token.
        model:         Embedding model identifier.
        batch:         Texts in this batch.
        input_type:    Passed verbatim in the request body.
        batch_idx:     Zero-based batch index (for logging).
        total_batches: Total batch count (for logging).

    Returns:
        Ordered list of float vectors matching ``batch`` positions.

    Raises:
        EmbeddingError: After exhausting retries, or on a non-retryable error.
    """
    url = f"{base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "input": batch,
        "input_type": input_type,
    }

    log = logger.bind(
        batch_idx=batch_idx,
        total_batches=total_batches,
        batch_size=len(batch),
    )

    for attempt in range(_MAX_RETRIES):
        try:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                resp_data: _EmbeddingsResponse = response.json()
                items = resp_data["data"]
                # Sort by index — defensive against any future NIM reordering
                items.sort(key=lambda x: x["index"])
                vectors: list[list[float]] = [item["embedding"] for item in items]
                log.info("nim_client.batch_ok", attempt=attempt)
                return vectors

            if response.status_code == 429 or response.status_code >= 500:
                wait_s = _RETRY_BASE_S * (2**attempt)
                log.warning(
                    "nim_client.retry",
                    status=response.status_code,
                    attempt=attempt,
                    wait_s=wait_s,
                )
                await asyncio.sleep(wait_s)
                continue

            # Non-retryable HTTP error (e.g. 400, 401, 403)
            raise EmbeddingError(
                f"NIM returned non-retryable status {response.status_code} "
                f"on batch {batch_idx}: {response.text[:200]}"
            )

        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            wait_s = _RETRY_BASE_S * (2**attempt)
            log.warning(
                "nim_client.network_error",
                error=str(exc),
                attempt=attempt,
                wait_s=wait_s,
            )
            await asyncio.sleep(wait_s)

    raise EmbeddingError(f"NIM batch {batch_idx} failed permanently after {_MAX_RETRIES} retries")
