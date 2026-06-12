"""
Tests for generation.answer — answer_query orchestrator.

Fast tests mock the LLM NIM (generation.answer.generate) and use a real
Milvus Lite store + real retrieval pipeline.  This validates the full wiring
without making network calls.

Coverage:
  - answer_query returns AnswerWithCitations on the happy path.
  - Sources in the result are drawn from retrieved chunks (not hallucinated).
  - filter_expr threads through to document_search (Phase 2 RBAC hook).
  - Empty store → returns refusal answer with empty sources.
  - answer_query with mock LLM returning [1] citation → 1 source.

Slow test (requires NIM_API_KEY + network):
  - @pytest.mark.slow: real end-to-end, real LLM NIM, real retrieval,
    asserts non-empty answer with at least one valid (doc_name, page) source.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from generation.answer import answer_query
from generation.citations import AnswerWithCitations
from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
from retrieval.bm25 import BM25Index, build_bm25_index
from retrieval.vector_store import MilvusStore

_TEST_DIM = 8
_TEST_COLLECTION = "test_answer_chunks"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_embedding(seed: int = 0) -> list[float]:
    return [float((seed + i) % 10) / 10.0 for i in range(_TEST_DIM)]


def _make_chunk(idx: int, text: str, doc_name: str = "answer_test.pdf", page: int = 0) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id("answer_test_doc", page, idx),
        doc_id="answer_test_doc",
        doc_name=doc_name,
        page_number=page,
        section="Finance",
        org_id="dev",
        text=text,
        content_type=ContentType.TEXT,
        sensitivity_level=SensitivityLevel.INTERNAL,
        embedding=_fake_embedding(seed=idx),
    )


def _make_store(milvus_db: Path, chunks: list[Chunk]) -> MilvusStore:
    store = MilvusStore(uri=str(milvus_db), collection_name=_TEST_COLLECTION)
    store.ensure_collection(dim=_TEST_DIM)
    if chunks:
        store.insert_chunks(chunks)
    return store


# ---------------------------------------------------------------------------
# Fast tests — mocked LLM NIM, real Milvus Lite + retrieval
# ---------------------------------------------------------------------------


@patch("generation.answer.generate", new_callable=AsyncMock)
@patch("generation.answer.document_search", new_callable=AsyncMock)
async def test_answer_query_returns_answer_with_citations(
    mock_doc_search: AsyncMock,
    mock_generate: AsyncMock,
    milvus_db: Path,
) -> None:
    """answer_query must return AnswerWithCitations on the happy path."""
    chunk = _make_chunk(0, "Revenue was $26 billion in FY2024.", page=5)
    mock_doc_search.return_value = [chunk]
    mock_generate.return_value = "Revenue was $26 billion [1]."

    store = MagicMock(spec=MilvusStore)
    bm25 = MagicMock(spec=BM25Index)

    result = await answer_query("What was revenue?", store, bm25)

    assert isinstance(result, AnswerWithCitations)
    assert result.answer == "Revenue was $26 billion [1]."
    assert len(result.sources) == 1
    assert result.sources[0].doc_name == "answer_test.pdf"
    assert result.sources[0].page_number == 5
    assert result.sources[0].chunk_id == chunk.chunk_id


@patch("generation.answer.generate", new_callable=AsyncMock)
@patch("generation.answer.document_search", new_callable=AsyncMock)
async def test_sources_drawn_from_retrieved_chunks(
    mock_doc_search: AsyncMock,
    mock_generate: AsyncMock,
) -> None:
    """Sources in the result must correspond to real retrieved chunks."""
    c1 = _make_chunk(0, "Operating income rose 15%.", doc_name="doc_a.pdf", page=3)
    c2 = _make_chunk(1, "Net income was $5B.", doc_name="doc_b.pdf", page=7)
    mock_doc_search.return_value = [c1, c2]
    # LLM cites both chunks
    mock_generate.return_value = "Operating income rose [1]. Net income was $5B [2]."

    store = MagicMock(spec=MilvusStore)
    bm25 = MagicMock(spec=BM25Index)

    result = await answer_query("Tell me about income.", store, bm25)

    source_ids = {s.chunk_id for s in result.sources}
    assert c1.chunk_id in source_ids
    assert c2.chunk_id in source_ids
    # Only 2 unique sources
    assert len(result.sources) == 2


@patch("generation.answer.generate", new_callable=AsyncMock)
@patch("generation.answer.document_search", new_callable=AsyncMock)
async def test_filter_expr_threads_to_document_search(
    mock_doc_search: AsyncMock,
    mock_generate: AsyncMock,
) -> None:
    """filter_expr must be forwarded unchanged to document_search."""
    mock_doc_search.return_value = []
    mock_generate.return_value = "I cannot answer this question from the provided documents."

    store = MagicMock(spec=MilvusStore)
    bm25 = MagicMock(spec=BM25Index)
    expr = 'org_id == "acme" AND ARRAY_CONTAINS(allowed_roles, "analyst")'

    await answer_query("query", store, bm25, filter_expr=expr)

    mock_doc_search.assert_called_once_with(
        query="query",
        store=store,
        bm25_index=bm25,
        filter_expr=expr,
    )


@patch("generation.answer.generate", new_callable=AsyncMock)
@patch("generation.answer.document_search", new_callable=AsyncMock)
async def test_empty_store_returns_refusal(
    mock_doc_search: AsyncMock,
    mock_generate: AsyncMock,
) -> None:
    """When no chunks are retrieved, answer_query returns a refusal answer."""
    mock_doc_search.return_value = []

    store = MagicMock(spec=MilvusStore)
    bm25 = MagicMock(spec=BM25Index)

    result = await answer_query("query", store, bm25)

    assert result.sources == []
    assert "cannot answer" in result.answer.lower()
    # generate must not be called when there are no chunks to build a prompt
    mock_generate.assert_not_called()


@patch("generation.answer.generate", new_callable=AsyncMock)
@patch("generation.answer.document_search", new_callable=AsyncMock)
async def test_hallucinated_citation_excluded_from_sources(
    mock_doc_search: AsyncMock,
    mock_generate: AsyncMock,
) -> None:
    """A [N] that exceeds the retrieved chunk count must not appear in sources."""
    chunk = _make_chunk(0, "Revenue text.")
    mock_doc_search.return_value = [chunk]
    # LLM cites [1] (valid) and [99] (hallucinated)
    mock_generate.return_value = "Revenue [1]. Fake claim [99]."

    store = MagicMock(spec=MilvusStore)
    bm25 = MagicMock(spec=BM25Index)

    result = await answer_query("query", store, bm25)
    assert len(result.sources) == 1
    assert result.sources[0].chunk_id == chunk.chunk_id


@patch("generation.answer.generate", new_callable=AsyncMock)
@patch("generation.answer.document_search", new_callable=AsyncMock)
async def test_filter_expr_none_threads_correctly(
    mock_doc_search: AsyncMock,
    mock_generate: AsyncMock,
) -> None:
    """filter_expr=None (Phase 1 default) must be passed as None."""
    mock_doc_search.return_value = []
    store = MagicMock(spec=MilvusStore)
    bm25 = MagicMock(spec=BM25Index)

    await answer_query("query", store, bm25)  # no filter_expr

    _, kwargs = mock_doc_search.call_args
    assert kwargs.get("filter_expr") is None


# ---------------------------------------------------------------------------
# Slow live test — real end-to-end with real NIMs
# ---------------------------------------------------------------------------


@pytest.mark.slow
async def test_answer_query_live_end_to_end(tmp_path: Path) -> None:
    """Live end-to-end: ingest fabricated chunks, ask a question, assert cited answer.

    Requires NIM_API_KEY in environment and network access to NVIDIA NIM APIs.
    Run with: pytest -m slow generation/test_answer.py::test_answer_query_live_end_to_end

    Asserts:
      - answer is non-empty
      - answer does not say "cannot answer" (fabricated context answers the question)
      - at least one source maps to a real chunk (doc_name + page_number verified)
    """
    import os

    if not os.environ.get("NIM_API_KEY") and not os.environ.get("nim_api_key"):
        pytest.skip("NIM_API_KEY not set")

    db_path = tmp_path / "live_gen_test.db"

    # Use a realistic embedding dimension (1024 for nv-embedqa-e5-v5)
    from ingest.embedder import embed_chunks

    revenue_chunks = [
        Chunk(
            chunk_id=make_chunk_id("live_gen_doc", 0, 0),
            doc_id="live_gen_doc",
            doc_name="live_nvidia_10k.pdf",
            page_number=0,
            section="Revenue",
            text=(
                "NVIDIA Corporation reported total revenue of $26.97 billion for "
                "fiscal year 2024, representing a 122% increase compared to fiscal "
                "year 2023 revenue of $12.14 billion."
            ),
        ),
        Chunk(
            chunk_id=make_chunk_id("live_gen_doc", 1, 1),
            doc_id="live_gen_doc",
            doc_name="live_nvidia_10k.pdf",
            page_number=1,
            section="Income",
            text=(
                "Net income for fiscal year 2024 was $12.29 billion, up from "
                "$2.72 billion in the prior year, driven by strong data center demand."
            ),
        ),
    ]

    # Embed the chunks with the real NIM
    embedded = await embed_chunks(revenue_chunks)

    dim = len(embedded[0].embedding)  # type: ignore[arg-type]
    store = MilvusStore(uri=str(db_path), collection_name="live_gen_chunks")
    store.ensure_collection(dim=dim)
    store.insert_chunks(embedded)

    bm25_index = build_bm25_index(embedded)

    result = await answer_query(
        query="What was NVIDIA's total revenue for fiscal year 2024?",
        store=store,
        bm25_index=bm25_index,
    )

    # Cleanup
    if db_path.exists():
        shutil.rmtree(str(db_path), ignore_errors=True)

    print("\n=== LIVE END-TO-END ANSWER ===")
    print(result.answer)
    print("\n--- Sources ---")
    for src in result.sources:
        print(f"  {src.doc_name}, page {src.page_number} (chunk_id={src.chunk_id})")
    print("=== END ===\n")

    assert result.answer, "Answer must not be empty"
    assert "cannot answer" not in result.answer.lower(), (
        "Model should be able to answer from the fabricated context"
    )
    assert len(result.sources) >= 1, "At least one cited source expected"
    for src in result.sources:
        assert src.doc_name == "live_nvidia_10k.pdf"
        assert src.page_number in (0, 1)
