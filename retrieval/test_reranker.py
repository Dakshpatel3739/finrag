"""
Tests for retrieval.reranker — NIM reranking client.

Fast tests mock the HTTP layer with respx.  No network required.
One @pytest.mark.slow live test hits the real NIM endpoint.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import Response

from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
from retrieval.errors import RerankError
from retrieval.reranker import rerank

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(idx: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id("doc_rerank", 0, idx),
        doc_id="doc_rerank",
        doc_name="rerank_test.pdf",
        page_number=idx,
        section="Test",
        text=text,
        content_type=ContentType.TEXT,
        sensitivity_level=SensitivityLevel.INTERNAL,
    )


_CHUNKS = [
    _make_chunk(0, "Revenue for Q1 was 4.2 billion dollars."),
    _make_chunk(1, "Operating expenses increased by 12 percent."),
    _make_chunk(2, "Net income declined due to higher interest."),
]

# Fabricated rerank response: NIM says passage 2 is most relevant, then 0, then 1
_FAKE_RANKINGS = [
    {"index": 2, "logit": 5.1},
    {"index": 0, "logit": 3.8},
    {"index": 1, "logit": 1.2},
]


def _rerank_url() -> str:
    from config.settings import get_settings

    return f"{get_settings().nim_rerank_base_url}/ranking"


# ---------------------------------------------------------------------------
# Fast tests (mocked HTTP)
# ---------------------------------------------------------------------------


@respx.mock
async def test_rerank_returns_top_n_chunks() -> None:
    """rerank must return exactly top_n chunks (not more)."""
    respx.post(_rerank_url()).mock(return_value=Response(200, json={"rankings": _FAKE_RANKINGS}))
    result = await rerank("What is net income?", _CHUNKS, top_n=2)
    assert len(result) == 2


@respx.mock
async def test_rerank_sorted_by_score_descending() -> None:
    """Returned chunks must be ordered by NIM logit score, highest first."""
    respx.post(_rerank_url()).mock(return_value=Response(200, json={"rankings": _FAKE_RANKINGS}))
    result = await rerank("What is net income?", _CHUNKS, top_n=3)
    # _FAKE_RANKINGS has index 2 first (logit 5.1), then 0 (3.8), then 1 (1.2)
    assert result[0].chunk_id == _CHUNKS[2].chunk_id
    assert result[1].chunk_id == _CHUNKS[0].chunk_id
    assert result[2].chunk_id == _CHUNKS[1].chunk_id


@respx.mock
async def test_rerank_top_n_larger_than_chunks_returns_all() -> None:
    """top_n > len(chunks) must return all chunks without error."""
    respx.post(_rerank_url()).mock(return_value=Response(200, json={"rankings": _FAKE_RANKINGS}))
    result = await rerank("query", _CHUNKS, top_n=100)
    assert len(result) == len(_CHUNKS)


@respx.mock
async def test_rerank_empty_chunks_returns_empty() -> None:
    """Empty chunk list must return empty list without calling the NIM."""
    result = await rerank("query", [], top_n=5)
    assert result == []
    # NIM should not be called
    assert not respx.calls


@respx.mock
async def test_rerank_uses_env_driven_url() -> None:
    """The reranker must use NIM_RERANK_BASE_URL from settings (not a hardcoded URL)."""
    from config.settings import get_settings

    settings = get_settings()
    expected_url = f"{settings.nim_rerank_base_url}/ranking"

    route = respx.post(expected_url).mock(
        return_value=Response(200, json={"rankings": _FAKE_RANKINGS})
    )
    await rerank("query", _CHUNKS, top_n=3)
    assert route.called


@respx.mock
async def test_rerank_uses_env_driven_model() -> None:
    """Request body must include the model name from settings."""
    route = respx.post(_rerank_url()).mock(
        return_value=Response(200, json={"rankings": _FAKE_RANKINGS})
    )
    from config.settings import get_settings

    expected_model = get_settings().nim_rerank_model

    await rerank("query", _CHUNKS, top_n=3)

    assert route.called
    request = route.calls[0].request
    import json

    body = json.loads(request.content)
    assert body["model"] == expected_model


@respx.mock
async def test_rerank_raises_on_non_retryable_error() -> None:
    """A 400 response must raise RerankError immediately without retrying."""
    respx.post(_rerank_url()).mock(return_value=Response(400, text="Bad Request"))
    with pytest.raises(RerankError, match="400"):
        await rerank("query", _CHUNKS, top_n=2)


@respx.mock
async def test_rerank_retries_on_429_then_succeeds() -> None:
    """A 429 followed by a 200 must succeed after one retry."""
    with patch("retrieval.reranker.asyncio.sleep", new_callable=AsyncMock):
        respx.post(_rerank_url()).mock(
            side_effect=[
                Response(429, text="Too Many Requests"),
                Response(200, json={"rankings": _FAKE_RANKINGS}),
            ]
        )
        result = await rerank("query", _CHUNKS, top_n=2)
    assert len(result) == 2


@respx.mock
async def test_rerank_raises_after_exhausting_retries() -> None:
    """Permanent 500 must raise RerankError after all retries are exhausted."""
    with patch("retrieval.reranker.asyncio.sleep", new_callable=AsyncMock):
        respx.post(_rerank_url()).mock(return_value=Response(500, text="Server Error"))
        with pytest.raises(RerankError, match="failed permanently"):
            await rerank("query", _CHUNKS, top_n=2)


# ---------------------------------------------------------------------------
# Slow live test
# ---------------------------------------------------------------------------


@pytest.mark.slow
async def test_live_rerank_returns_sensible_ranking() -> None:
    """Real NIM reranking: chunks about 'revenue' should rank above unrelated ones.

    Requires NIM_API_KEY in environment.  Run with: pytest -m slow
    """
    chunks = [
        _make_chunk(0, "Total revenue for fiscal year 2024 was $12.5 billion."),
        _make_chunk(1, "The company operates data centres in 15 countries."),
        _make_chunk(2, "Annual revenue grew 18% compared to prior year."),
    ]
    result = await rerank("What was the annual revenue?", chunks, top_n=3)

    assert len(result) == 3
    # The two revenue chunks (0 and 2) must both rank above the data-centre chunk (1)
    data_centre_chunk = chunks[1]
    revenue_chunks = {chunks[0].chunk_id, chunks[2].chunk_id}
    result_ids = [c.chunk_id for c in result]
    data_centre_pos = result_ids.index(data_centre_chunk.chunk_id)
    # At least one revenue chunk must be ranked above the data-centre chunk
    revenue_positions = [result_ids.index(cid) for cid in revenue_chunks]
    assert min(revenue_positions) < data_centre_pos, (
        f"Revenue chunks should rank above data-centre chunk. "
        f"Got order: {[c.text[:40] for c in result]}"
    )
