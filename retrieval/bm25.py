"""
retrieval.bm25 — in-memory BM25 lexical search index over the chunk corpus.

WHY in-memory BM25 (rank-bm25) instead of native Milvus sparse:
    Milvus 2.4 supports sparse/BM25 vectors natively, but Milvus Lite (used in
    Phases 1-4 dev) does not expose them through the MilvusClient API.  rank-bm25
    gives a fully correct BM25Okapi implementation that runs in-process with zero
    server overhead and zero schema changes.  Phase 5 / production can swap this
    for Milvus native BM25 sparse vectors by replacing BM25Index with sparse-vector
    ingest + query and keeping the same (chunk_id, score) fusion interface.

WHY whitespace tokenisation (not sub-word):
    Simple `.lower().split()` tokenisation is sufficient for financial document
    retrieval where queries and passages share the same domain vocabulary.  A
    production upgrade (spaCy, tiktoken, or a custom financial tokeniser) is a
    drop-in replacement in BM25Index.__init__() without touching fusion or search.

Public API
----------
    BM25Index(chunks)
        .search(query, top_k)   — lexical search; returns (chunk_id, score) pairs
        .get_chunk(chunk_id)    — look up a stored Chunk by id (used by fusion)
        .size                   — number of indexed chunks
    build_bm25_index(chunks)    — convenience alias for BM25Index(chunks)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from rank_bm25 import BM25Okapi

from ingest.models import Chunk

if TYPE_CHECKING:
    pass

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class BM25Index:
    """BM25Okapi index over a fixed chunk corpus.

    Build once at application startup (or after each ingest batch), then call
    search() for every incoming query.  The index is immutable — adding new
    documents requires rebuilding via build_bm25_index().

    Args:
        chunks: The full corpus of chunks to index.  Empty list produces a
                valid (empty) index that always returns zero results.
    """

    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks: list[Chunk] = chunks
        self._chunk_map: dict[str, Chunk] = {c.chunk_id: c for c in chunks}
        # Tokenise: lowercase whitespace split — see WHY comment at module level
        tokenized: list[list[str]] = [c.text.lower().split() for c in chunks]
        # WHY None guard: BM25Okapi([[]] or []) raises ZeroDivisionError on an empty
        # or single-empty-doc corpus. We skip instantiation and return [] from search().
        self._bm25: BM25Okapi | None = BM25Okapi(tokenized) if chunks else None
        logger.debug("bm25.index_built", chunk_count=len(chunks))

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int) -> list[tuple[str, float]]:
        """Return the top-k chunk_ids ordered by BM25 relevance score.

        Args:
            query:  Raw query string (tokenised the same way as index text).
            top_k:  Maximum number of results.  Returns fewer if the corpus
                    has fewer than top_k chunks with a positive score.

        Returns:
            List of (chunk_id, score) pairs, sorted by score descending.
            Score of 0.0 means no lexical overlap with the query.
        """
        if not self._chunks or self._bm25 is None:
            return []

        tokens = query.lower().split()
        scores = self._bm25.get_scores(tokens)

        # Zip with index, sort by score desc, take top_k
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        results = [(self._chunks[i].chunk_id, float(s)) for i, s in ranked]

        logger.debug("bm25.search_done", query_tokens=len(tokens), hits=len(results))
        return results

    # ------------------------------------------------------------------
    # Lookup helpers (used by document_search to build fusion pool)
    # ------------------------------------------------------------------

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Return the Chunk for a given chunk_id, or None if not found."""
        return self._chunk_map.get(chunk_id)

    @property
    def size(self) -> int:
        """Number of chunks in the index."""
        return len(self._chunks)


def build_bm25_index(chunks: list[Chunk]) -> BM25Index:
    """Convenience factory — equivalent to BM25Index(chunks).

    Args:
        chunks: Corpus to index.

    Returns:
        A ready-to-search BM25Index.
    """
    return BM25Index(chunks)
