"""
retrieval.reranker — async client for the NVIDIA NeMo Reranking NIM.

Given a query and a list of candidate chunks (the fused output of BM25 + dense
retrieval), the reranker re-scores every (query, passage) pair with a
cross-encoder model and returns the top-n chunks sorted by relevance.

WHY a separate reranking step (not just dense retrieval):
    Bi-encoder embedding models (like nv-embedqa-e5-v5) encode query and passage
    independently — fast, but they miss nuanced query-passage interactions.
    A cross-encoder reranker (nv-rerankqa-mistral-4b-v3) sees both at once and
    produces much more accurate relevance scores at the cost of latency.  The
    standard pattern is: cheap bi-encoder retrieves a large candidate set (top_k),
    expensive cross-encoder reranks the shortlist (rerank_n) → best of both worlds.

NIM endpoint contract (NeMo Retriever Reranking):
    POST {NIM_RERANK_BASE_URL}/reranking
    Body:
        {"model": "<model>",
         "query": {"text": "<query_text>"},
         "passages": [{"text": "<chunk_text>"}, ...]}
    Response:
        {"rankings": [{"index": <int>, "logit": <float>}, ...]}
    Rankings are sorted by logit descending; `index` maps back to the passages array.

All config is env-driven (NIM_RERANK_BASE_URL, NIM_RERANK_MODEL) so swapping
rerank models is a one-line env change with zero code edits.

Retry strategy mirrors nim_client.py: 429 / 5xx → exponential backoff up to
_MAX_RETRIES attempts; non-retryable 4xx → raise immediately.

Public API
----------
    rerank(query, chunks, top_n) -> list[Chunk]
        Re-scores chunks against query, returns top_n sorted by logit desc.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, TypedDict

import httpx
import structlog

from config.settings import get_settings
from ingest.models import Chunk
from retrieval.errors import RerankError

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_MAX_RETRIES = 3
_RETRY_BASE_S = 1.0


# ---------------------------------------------------------------------------
# Response types
# ---------------------------------------------------------------------------


class _RankingItem(TypedDict):
    index: int
    logit: float


class _RerankResponse(TypedDict):
    rankings: list[_RankingItem]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def rerank(
    query: str,
    chunks: list[Chunk],
    top_n: int,
) -> list[Chunk]:
    """Re-score candidate chunks with the NVIDIA reranking NIM.

    Sends the query and all candidate chunk texts to the NIM reranking endpoint
    in a single request, receives per-passage logit scores, and returns the
    top_n chunks sorted by score descending.

    Args:
        query:  The user query string.
        chunks: Candidate chunks from hybrid retrieval (dense + BM25 + RRF).
                Order does not matter — the NIM scores all passages independently.
        top_n:  Number of chunks to return after reranking.  Clamped to
                len(chunks) if top_n > len(chunks).

    Returns:
        Up to top_n chunks, ordered by rerank score descending (most relevant first).
        Returns [] if chunks is empty.

    Raises:
        RerankError: After exhausting _MAX_RETRIES retries, on a non-retryable
                     HTTP error, or if the response shape is unexpected.
    """
    if not chunks:
        return []

    effective_top_n = min(top_n, len(chunks))
    settings = get_settings()
    api_key = settings.nim_api_key.get_secret_value()
    base_url = settings.nim_rerank_base_url
    model = settings.nim_rerank_model

    url = f"{base_url}/reranking"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "query": {"text": query},
        "passages": [{"text": c.text} for c in chunks],
    }

    log = logger.bind(
        model=model,
        candidate_count=len(chunks),
        top_n=effective_top_n,
    )
    log.info("reranker.rerank_start")
    t0 = time.monotonic()

    rankings = await _rerank_with_retry(
        url=url,
        headers=headers,
        payload=payload,
        log=log,
    )

    # rankings is sorted by logit desc; index maps back to chunks[]
    top_rankings = rankings[:effective_top_n]
    try:
        reranked = [chunks[r["index"]] for r in top_rankings]
    except IndexError as exc:
        raise RerankError(
            f"Reranker returned index {exc} out of range for {len(chunks)} passages"
        ) from exc

    elapsed = time.monotonic() - t0
    log.info(
        "reranker.rerank_done",
        returned=len(reranked),
        elapsed_s=round(elapsed, 3),
        nim_cost_log=True,
    )
    return reranked


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _rerank_with_retry(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    log: structlog.BoundLogger,
) -> list[_RankingItem]:
    """POST to the rerank endpoint with exponential-backoff retry.

    Retries on 429 and 5xx.  Raises RerankError on permanent failure or
    non-retryable 4xx.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(_MAX_RETRIES):
            try:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    resp_data: _RerankResponse = response.json()
                    rankings = resp_data.get("rankings", [])
                    log.info("reranker.batch_ok", attempt=attempt, ranking_count=len(rankings))
                    return rankings

                if response.status_code == 429 or response.status_code >= 500:
                    wait_s = _RETRY_BASE_S * (2**attempt)
                    log.warning(
                        "reranker.retry",
                        status=response.status_code,
                        attempt=attempt,
                        wait_s=wait_s,
                    )
                    await asyncio.sleep(wait_s)
                    continue

                # Non-retryable (400, 401, 403, …)
                raise RerankError(
                    f"Reranker returned non-retryable status {response.status_code}: "
                    f"{response.text[:200]}"
                )

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                wait_s = _RETRY_BASE_S * (2**attempt)
                log.warning(
                    "reranker.network_error",
                    error=str(exc),
                    attempt=attempt,
                    wait_s=wait_s,
                )
                await asyncio.sleep(wait_s)

    raise RerankError(f"Reranker failed permanently after {_MAX_RETRIES} retries")
