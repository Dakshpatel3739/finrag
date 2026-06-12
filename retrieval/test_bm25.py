"""
Tests for retrieval.bm25 — BM25Index lexical search.

All tests are pure-unit (no network, no Milvus).  Chunks are fabricated
in-memory; no PDF fixture required.
"""

from __future__ import annotations

from ingest.models import Chunk, ContentType, make_chunk_id
from retrieval.bm25 import BM25Index, build_bm25_index

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(idx: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id("doc_bm25_test", 0, idx),
        doc_id="doc_bm25_test",
        doc_name="bm25_test.pdf",
        page_number=idx,
        section="Test",
        text=text,
        content_type=ContentType.TEXT,
    )


_CHUNKS = [
    _make_chunk(0, "Revenue for Q1 was 4.2 billion dollars."),
    _make_chunk(1, "Operating expenses increased by 12 percent year over year."),
    _make_chunk(2, "The board approved a dividend of 0.50 dollars per share."),
    _make_chunk(3, "Net income declined due to higher interest expenses."),
    _make_chunk(4, "Cash flow from operations remained strong at 1.1 billion."),
]


# ---------------------------------------------------------------------------
# Index construction
# ---------------------------------------------------------------------------


def test_build_bm25_index_factory_alias() -> None:
    """build_bm25_index must return a BM25Index with correct size."""
    idx = build_bm25_index(_CHUNKS)
    assert isinstance(idx, BM25Index)
    assert idx.size == len(_CHUNKS)


def test_empty_corpus_builds_valid_index() -> None:
    """An empty chunk list must produce a valid index with size 0."""
    idx = BM25Index([])
    assert idx.size == 0
    results = idx.search("revenue", top_k=5)
    assert results == []


# ---------------------------------------------------------------------------
# Search correctness
# ---------------------------------------------------------------------------


def test_exact_term_match_ranks_first() -> None:
    """A query term present only in one chunk must rank that chunk first."""
    idx = BM25Index(_CHUNKS)
    results = idx.search("dividend", top_k=3)
    assert len(results) > 0
    top_chunk_id, top_score = results[0]
    # Chunk 2 is the only one with "dividend"
    assert top_chunk_id == _CHUNKS[2].chunk_id
    assert top_score > 0.0


def test_revenue_query_ranks_revenue_chunk_first() -> None:
    """'revenue' query must prefer the chunk with 'Revenue' (case-insensitive)."""
    idx = BM25Index(_CHUNKS)
    results = idx.search("revenue", top_k=5)
    top_id = results[0][0]
    assert top_id == _CHUNKS[0].chunk_id


def test_results_sorted_by_score_descending() -> None:
    """Scores must be non-increasing (highest relevance first)."""
    idx = BM25Index(_CHUNKS)
    results = idx.search("expenses income", top_k=5)
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)


def test_top_k_limits_results() -> None:
    """top_k must limit the returned list even when the corpus is larger."""
    idx = BM25Index(_CHUNKS)
    results = idx.search("the", top_k=2)
    assert len(results) <= 2


def test_no_match_returns_zero_or_empty_scores() -> None:
    """A query with no overlap returns either empty list or zero-score items."""
    idx = BM25Index(_CHUNKS)
    results = idx.search("zzzyyyxxx_nonexistent_term", top_k=3)
    # Either empty or all scores are 0
    for _, score in results:
        assert score == 0.0


def test_top_k_larger_than_corpus_returns_all() -> None:
    """top_k larger than corpus size must return at most len(corpus) results."""
    idx = BM25Index(_CHUNKS)
    results = idx.search("billion", top_k=100)
    assert len(results) <= len(_CHUNKS)


# ---------------------------------------------------------------------------
# get_chunk lookup
# ---------------------------------------------------------------------------


def test_get_chunk_returns_correct_chunk() -> None:
    """get_chunk must return the Chunk with the given chunk_id."""
    idx = BM25Index(_CHUNKS)
    chunk = _CHUNKS[2]
    retrieved = idx.get_chunk(chunk.chunk_id)
    assert retrieved is not None
    assert retrieved.chunk_id == chunk.chunk_id
    assert retrieved.text == chunk.text


def test_get_chunk_returns_none_for_unknown_id() -> None:
    """get_chunk must return None for a chunk_id not in the index."""
    idx = BM25Index(_CHUNKS)
    assert idx.get_chunk("nonexistent_id_xyz") is None


# ---------------------------------------------------------------------------
# Multi-term query
# ---------------------------------------------------------------------------


def test_multi_term_query_prefers_chunk_with_both_terms() -> None:
    """A chunk containing both query terms should rank above single-term matches."""
    idx = BM25Index(_CHUNKS)
    # "billion" appears in chunk 0 ("4.2 billion") and chunk 4 ("1.1 billion")
    # "revenue" appears only in chunk 0
    results = idx.search("revenue billion", top_k=5)
    assert results[0][0] == _CHUNKS[0].chunk_id, (
        "Chunk 0 has both 'revenue' and 'billion'; must rank first"
    )
