"""
Tests for ingest.nim_client — NeMo Embedding NIM async HTTP client.

Fast tests: mock httpx with respx so no network is required.  These run in CI.
Slow test:  one live NIM call — requires NIM_API_KEY in env and a real network.
            Excluded from default CI run; run manually with:
              pytest ingest/test_nim_client.py -m slow

Test coverage:
  - Batching: N texts at batch_size B → ceil(N/B) HTTP requests
  - 429 retry: first request returns 429, second returns 200 → succeeds
  - Permanent failure: all retries return 429 → raises EmbeddingError
  - input_type forwarded: request body contains the caller-supplied input_type
  - Empty input: returns [] without making any HTTP requests
  - Order preservation: vectors are returned in input order even if response
    index fields arrive out of order
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from ingest.errors import EmbeddingError
from ingest.nim_client import _DEFAULT_BATCH_SIZE, embed_texts

# The URL that the nim_client will call (matches the default settings)
_EMBED_URL = "https://integrate.api.nvidia.com/v1/embeddings"


def _make_response(n: int, dim: int = 2) -> dict[str, object]:
    """Build a well-formed /embeddings response for *n* texts."""
    return {
        "object": "list",
        "data": [
            {"object": "embedding", "index": i, "embedding": [float(i), float(i + 0.1)]}
            for i in range(n)
        ],
        "model": "nvidia/nv-embedqa-e5-v5",
        "usage": {"prompt_tokens": n * 5, "total_tokens": n * 5},
    }


# ---------------------------------------------------------------------------
# Fast unit tests — no network
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_input_returns_empty_list() -> None:
    """embed_texts([]) must return [] without hitting the network."""
    with respx.mock:
        result = await embed_texts([])
    assert result == []


@pytest.mark.asyncio
async def test_batching_makes_correct_request_count() -> None:
    """120 texts at batch_size=50 must produce exactly 3 HTTP requests (50+50+20)."""
    texts = [f"doc text {i}" for i in range(120)]
    request_bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        request_bodies.append(body)
        n = len(body["input"])
        return httpx.Response(200, json=_make_response(n))

    with respx.mock:
        respx.post(_EMBED_URL).mock(side_effect=handler)
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            result = await embed_texts(texts, batch_size=50)

    assert len(request_bodies) == 3
    assert len(request_bodies[0]["input"]) == 50
    assert len(request_bodies[1]["input"]) == 50
    assert len(request_bodies[2]["input"]) == 20
    assert len(result) == 120


@pytest.mark.asyncio
async def test_batching_preserves_order() -> None:
    """Vector i must correspond to text i even across batch boundaries."""
    texts = [f"text {i}" for i in range(5)]

    # Each batch's response has index-tagged vectors: embedding[i] = [float(i), ...]
    # With batch_size=2, batches are [0,1], [2,3], [4] → vectors from different requests
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        body = json.loads(request.content)
        batch_texts: list[str] = body["input"]
        # Produce vectors whose first element encodes the text index
        data = []
        for local_i, text in enumerate(batch_texts):
            global_i = int(text.split()[-1])
            data.append({"object": "embedding", "index": local_i, "embedding": [float(global_i)]})
        call_count += 1
        return httpx.Response(200, json={"object": "list", "data": data, "model": "m"})

    with respx.mock:
        respx.post(_EMBED_URL).mock(side_effect=handler)
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            result = await embed_texts(texts, batch_size=2)

    assert call_count == 3  # batches: [0,1], [2,3], [4]
    for i, vec in enumerate(result):
        assert vec[0] == float(i), f"text {i} got vector {vec}, expected first elem {float(i)}"


@pytest.mark.asyncio
async def test_response_index_reordering_preserved() -> None:
    """If the NIM response returns items in reversed index order, output must still match input."""
    texts = ["alpha", "beta", "gamma"]

    def handler(request: httpx.Request) -> httpx.Response:
        # Return items in reverse index order to exercise the sort
        data = [
            {"object": "embedding", "index": 2, "embedding": [2.0]},
            {"object": "embedding", "index": 0, "embedding": [0.0]},
            {"object": "embedding", "index": 1, "embedding": [1.0]},
        ]
        return httpx.Response(200, json={"object": "list", "data": data, "model": "m"})

    with respx.mock:
        respx.post(_EMBED_URL).mock(side_effect=handler)
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            result = await embed_texts(texts, batch_size=_DEFAULT_BATCH_SIZE)

    assert result[0] == [0.0]
    assert result[1] == [1.0]
    assert result[2] == [2.0]


@pytest.mark.asyncio
async def test_429_triggers_retry_then_succeeds() -> None:
    """A single 429 response must cause one retry and ultimately succeed."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429)
        return httpx.Response(200, json=_make_response(1))

    with respx.mock:
        respx.post(_EMBED_URL).mock(side_effect=handler)
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            result = await embed_texts(["hello"])

    assert call_count == 2
    assert len(result) == 1


@pytest.mark.asyncio
async def test_5xx_triggers_retry_then_succeeds() -> None:
    """A 503 response must be retried the same as 429."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(503)
        return httpx.Response(200, json=_make_response(1))

    with respx.mock:
        respx.post(_EMBED_URL).mock(side_effect=handler)
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            result = await embed_texts(["hello"])

    assert call_count == 2
    assert len(result) == 1


@pytest.mark.asyncio
async def test_permanent_failure_raises_embedding_error() -> None:
    """After _MAX_RETRIES consecutive 429s, EmbeddingError must be raised."""
    with respx.mock:
        respx.post(_EMBED_URL).mock(return_value=httpx.Response(429))
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            with pytest.raises(EmbeddingError):
                await embed_texts(["hello"])


@pytest.mark.asyncio
async def test_non_retryable_status_raises_immediately() -> None:
    """A 401 response must raise EmbeddingError immediately without retrying."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(401, text="Unauthorized")

    with respx.mock:
        respx.post(_EMBED_URL).mock(side_effect=handler)
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            with pytest.raises(EmbeddingError, match="401"):
                await embed_texts(["hello"])

    assert call_count == 1  # no retries for 401


@pytest.mark.asyncio
async def test_input_type_passage_sent_in_request_body() -> None:
    """input_type='passage' must appear verbatim in the JSON request body."""
    bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=_make_response(1))

    with respx.mock:
        respx.post(_EMBED_URL).mock(side_effect=handler)
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            await embed_texts(["doc chunk"], input_type="passage")

    assert bodies[0]["input_type"] == "passage"


@pytest.mark.asyncio
async def test_input_type_query_sent_in_request_body() -> None:
    """input_type='query' must appear verbatim — retrieval slice will use this."""
    bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=_make_response(1))

    with respx.mock:
        respx.post(_EMBED_URL).mock(side_effect=handler)
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            await embed_texts(["what is revenue?"], input_type="query")

    assert bodies[0]["input_type"] == "query"


@pytest.mark.asyncio
async def test_model_name_sent_in_request_body() -> None:
    """The model identifier from settings must be forwarded to the NIM."""
    bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=_make_response(1))

    with respx.mock:
        respx.post(_EMBED_URL).mock(side_effect=handler)
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            await embed_texts(["hello"])

    assert bodies[0]["model"] == "nvidia/nv-embedqa-e5-v5"


@pytest.mark.asyncio
async def test_single_text_returns_single_vector() -> None:
    """embed_texts with one text must return a list of one vector."""
    with respx.mock:
        respx.post(_EMBED_URL).mock(return_value=httpx.Response(200, json=_make_response(1)))
        with patch("asyncio.sleep", new=AsyncMock(return_value=None)):
            result = await embed_texts(["hello world"])

    assert len(result) == 1
    assert isinstance(result[0], list)
    assert all(isinstance(v, float) for v in result[0])


# ---------------------------------------------------------------------------
# Slow live test — requires NIM_API_KEY env var, excluded from default CI
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.asyncio
async def test_live_embed_returns_float_vectors() -> None:
    """Live NIM call: embed 2 short financial strings and verify vector shape.

    Run with:
        pytest ingest/test_nim_client.py -m slow

    Requires NIM_API_KEY in the environment (or .env file).
    """
    texts = [
        "Net revenue for Q3 2024 increased 12% year-over-year to $4.2 billion.",
        "Operating income reached $1.1 billion, representing a 26.2% margin.",
    ]
    result = await embed_texts(texts, input_type="passage")

    assert len(result) == 2, f"Expected 2 vectors, got {len(result)}"
    assert len(result[0]) > 0, "Vectors must be non-empty"
    assert len(result[0]) == len(result[1]), "Both vectors must have the same dimension"
    assert all(isinstance(v, float) for v in result[0]), "Vector elements must be floats"
    assert all(isinstance(v, float) for v in result[1]), "Vector elements must be floats"
