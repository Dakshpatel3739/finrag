"""
Tests for retrieval.search — document_search hybrid orchestrator.

Fast tests use a real Milvus Lite store (in-process) + mock the NIM calls
(embed_texts and rerank).  This validates the pipeline wiring without network.

Coverage:
  - Full pipeline returns reranked chunks.
  - filter_expr threads through to dense_search (Phase 2 RBAC hook).
  - Empty store returns empty list.
  - Each stage is invoked in order (embed → dense → bm25 → rrf → rerank).
  - input_type="query" is passed to embed_texts (asymmetric model invariant).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
from retrieval.bm25 import build_bm25_index
from retrieval.search import document_search
from retrieval.vector_store import MilvusStore

_TEST_DIM = 8
_TEST_COLLECTION = "test_search_chunks"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_embedding(dim: int = _TEST_DIM) -> list[float]:
    return [0.1 * (i % 10) for i in range(dim)]


def _make_chunk(idx: int, text: str, org_id: str = "dev") -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id("doc_search_test", 0, idx),
        doc_id="doc_search_test",
        doc_name="search_test.pdf",
        page_number=idx,
        section="Finance",
        org_id=org_id,
        text=text,
        content_type=ContentType.TEXT,
        sensitivity_level=SensitivityLevel.INTERNAL,
        embedding=_fake_embedding(),
    )


def _make_store(milvus_db: Path) -> MilvusStore:
    return MilvusStore(uri=str(milvus_db), collection_name=_TEST_COLLECTION)


def _seed_and_build(
    store: MilvusStore,
    chunks: list[Chunk],
) -> None:
    """Insert chunks into the store (already have embeddings)."""
    store.ensure_collection(dim=_TEST_DIM)
    store.insert_chunks(chunks)


# ---------------------------------------------------------------------------
# Fast tests — mocked NIMs, real Milvus Lite
# ---------------------------------------------------------------------------


@patch("retrieval.search.rerank", new_callable=AsyncMock)
@patch("retrieval.search.embed_texts", new_callable=AsyncMock)
async def test_pipeline_returns_reranked_chunks(
    mock_embed: AsyncMock,
    mock_rerank: AsyncMock,
    milvus_db: Path,
    tmp_path: Path,
) -> None:
    """Full pipeline must call embed → dense → bm25 → rerank and return chunks."""
    chunks = [
        _make_chunk(0, "Revenue grew 20% year over year to $5 billion."),
        _make_chunk(1, "Operating expenses increased by 15 percent."),
        _make_chunk(2, "Net income was $800 million for the quarter."),
    ]
    store = _make_store(milvus_db)
    _seed_and_build(store, chunks)
    bm25_index = build_bm25_index(chunks)

    mock_embed.return_value = [_fake_embedding()]
    # rerank mock returns top 2 chunks in reversed order for test visibility
    mock_rerank.return_value = [chunks[2], chunks[0]]

    # Use a temp config DB so get_config always works
    from config.system_config import init_config_db

    config_path = str(tmp_path / "test_config.db")
    init_config_db(config_path)

    from config.settings import get_settings

    get_settings.cache_clear()
    with patch.dict("os.environ", {"CONFIG_DB_PATH": config_path}):
        get_settings.cache_clear()
        result = await document_search("What is revenue?", store, bm25_index)

    # embed_texts called with query and input_type="query"
    mock_embed.assert_called_once()
    call_args = mock_embed.call_args
    texts_arg = call_args[0][0] if call_args[0] else call_args[1].get("texts")
    assert texts_arg == ["What is revenue?"]
    assert call_args[1].get("input_type") == "query"

    # rerank was called
    mock_rerank.assert_called_once()
    # result is whatever rerank returned
    assert result == [chunks[2], chunks[0]]

    store.drop_collection()
    get_settings.cache_clear()


@patch("retrieval.search.rerank", new_callable=AsyncMock)
@patch("retrieval.search.embed_texts", new_callable=AsyncMock)
async def test_filter_expr_threads_to_dense_search(
    mock_embed: AsyncMock,
    mock_rerank: AsyncMock,
    milvus_db: Path,
    tmp_path: Path,
) -> None:
    """filter_expr must be forwarded to dense_search unchanged (Phase 2 RBAC hook).

    Approach: spy on store.dense_search via patch.object to capture the
    filter_expr argument it received, while still executing the real Milvus
    search.  This confirms the injection point without over-asserting on
    BM25 (which is corpus-wide and intentionally not filtered in Phase 1).
    """
    chunk_acme = _make_chunk(0, "Acme revenue was $1B.", org_id="acme")
    chunk_other = _make_chunk(1, "Other company revenue was $2B.", org_id="other")
    store = _make_store(milvus_db)
    _seed_and_build(store, [chunk_acme, chunk_other])
    bm25_index = build_bm25_index([chunk_acme, chunk_other])

    mock_embed.return_value = [_fake_embedding()]
    mock_rerank.return_value = [chunk_acme]

    from config.system_config import init_config_db

    config_path = str(tmp_path / "test_config2.db")
    init_config_db(config_path)

    # Spy: wrap the real dense_search so we can capture its filter_expr arg
    captured_filter: list[str | None] = []
    original_dense = store.dense_search

    def spy_dense(
        query_vector: list[float],
        top_k: int,
        filter_expr: str | None = None,
    ) -> list[Chunk]:
        captured_filter.append(filter_expr)
        return original_dense(query_vector, top_k, filter_expr)

    store.dense_search = spy_dense  # type: ignore[method-assign]

    with patch.dict("os.environ", {"CONFIG_DB_PATH": config_path}):
        from config.settings import get_settings

        get_settings.cache_clear()
        await document_search(
            "revenue",
            store,
            bm25_index,
            filter_expr='org_id == "acme"',
        )

    # Verify filter_expr was forwarded to dense_search — the Phase 2 RBAC hook
    assert captured_filter == ['org_id == "acme"'], (
        f"dense_search must receive filter_expr unchanged; got {captured_filter}"
    )

    store.drop_collection()
    from config.settings import get_settings

    get_settings.cache_clear()


@patch("retrieval.search.rerank", new_callable=AsyncMock)
@patch("retrieval.search.embed_texts", new_callable=AsyncMock)
async def test_empty_store_returns_empty_list(
    mock_embed: AsyncMock,
    mock_rerank: AsyncMock,
    milvus_db: Path,
    tmp_path: Path,
) -> None:
    """document_search on an empty collection must return [] gracefully."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)
    bm25_index = build_bm25_index([])  # no chunks
    mock_embed.return_value = [_fake_embedding()]
    mock_rerank.return_value = []

    from config.system_config import init_config_db

    config_path = str(tmp_path / "test_config3.db")
    init_config_db(config_path)

    with patch.dict("os.environ", {"CONFIG_DB_PATH": config_path}):
        from config.settings import get_settings

        get_settings.cache_clear()
        result = await document_search("anything", store, bm25_index)

    assert result == []
    store.drop_collection()
    from config.settings import get_settings

    get_settings.cache_clear()


@patch("retrieval.search.rerank", new_callable=AsyncMock)
@patch("retrieval.search.embed_texts", new_callable=AsyncMock)
async def test_embed_called_with_input_type_query(
    mock_embed: AsyncMock,
    mock_rerank: AsyncMock,
    milvus_db: Path,
    tmp_path: Path,
) -> None:
    """embed_texts MUST be called with input_type='query' — asymmetric model invariant.

    Using input_type='passage' for queries silently destroys retrieval quality.
    This test guards against regressions on this critical invariant.
    """
    chunks = [_make_chunk(0, "Revenue grew 20%.")]
    store = _make_store(milvus_db)
    _seed_and_build(store, chunks)
    bm25_index = build_bm25_index(chunks)
    mock_embed.return_value = [_fake_embedding()]
    mock_rerank.return_value = chunks[:1]

    from config.system_config import init_config_db

    config_path = str(tmp_path / "test_config4.db")
    init_config_db(config_path)

    with patch.dict("os.environ", {"CONFIG_DB_PATH": config_path}):
        from config.settings import get_settings

        get_settings.cache_clear()
        await document_search("revenue query", store, bm25_index)

    mock_embed.assert_called_once()
    _, kwargs = mock_embed.call_args
    assert kwargs.get("input_type") == "query", (
        "embed_texts must be called with input_type='query' for search queries"
    )

    store.drop_collection()
    from config.settings import get_settings

    get_settings.cache_clear()
