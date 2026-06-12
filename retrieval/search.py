"""
retrieval.search — document_search: the hybrid retrieval + reranking orchestrator.

This is the chain-server's documentSearch method for Phase 1.  It wires together
the four retrieval sub-systems into a single function that a caller (API layer,
eval harness, CLI) invokes with a plain query string.

Pipeline:
    1. embed query   — nv-embedqa-e5-v5 with input_type="query"
    2. dense_search  — Milvus ANN search (COSINE), top_k candidates
    3. bm25_search   — BM25Okapi lexical search, top_k candidates
    4. rrf_fuse      — Reciprocal Rank Fusion, k from system_config
    5. rerank        — cross-encoder NIM re-scores shortlist, returns rerank_n

Phase 2 extension point:
    The filter_expr parameter threads through step 2 (dense_search) unchanged.
    Phase 2 builds the expression:
        'org_id == "{org_id}" AND ARRAY_CONTAINS(allowed_roles, "{role}")'
    and passes it here.  The BM25 index SHOULD also be scoped to the caller's
    visible chunks in Phase 2 (rebuild per-org/per-role or accept pre-filtered
    chunks at index-build time).

WHY input_type="query" for query embedding:
    nv-embedqa-e5-v5 is an asymmetric QA model.  Document chunks are embedded
    with input_type="passage" at ingest time.  If the same encoder head were used
    for queries, cosine distances would be meaningless — the model's passage and
    query projection heads live in different subspaces.  This asymmetry is the
    most common silent recall killer in NeMo Retriever deployments.

Public API
----------
    document_search(query, store, bm25_index, filter_expr) -> list[Chunk]
"""

from __future__ import annotations

import time

import structlog

from config.settings import get_settings
from config.system_config import get_config, init_config_db
from ingest.models import Chunk
from ingest.nim_client import InputType, embed_texts
from retrieval.bm25 import BM25Index
from retrieval.fusion import rrf_fuse
from retrieval.reranker import rerank
from retrieval.vector_store import MilvusStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Literal so mypy knows this is a valid InputType without a cast
_QUERY_INPUT_TYPE: InputType = "query"


async def document_search(
    query: str,
    store: MilvusStore,
    bm25_index: BM25Index,
    filter_expr: str | None = None,
) -> list[Chunk]:
    """Hybrid retrieval + reranking for a single query string.

    Orchestrates: embed (query) → dense_search → bm25_search → rrf_fuse → rerank.
    Returns rerank_n chunks sorted by cross-encoder relevance (most relevant first).

    RBAC extension point:
        Pass a Milvus filter expression as filter_expr to restrict results to
        chunks the calling user is authorised to see.  Phase 1 passes None
        (no restriction).  Phase 2 passes:
            'org_id == "{org_id}" AND ARRAY_CONTAINS(allowed_roles, "{role}")'
        The filter runs inside the Milvus ANN search — forbidden chunks never
        become candidates, never enter the reranker, never reach the LLM.

    Args:
        query:       Natural-language query string.
        store:       Initialised MilvusStore with an existing collection.
        bm25_index:  Pre-built BM25Index over the visible chunk corpus.
                     Rebuild after each ingest batch; Phase 2 scopes it to
                     the authorised corpus before passing it in.
        filter_expr: Optional Milvus boolean expression (Phase 2 RBAC hook).
                     None = unrestricted search (Phase 1 default).

    Returns:
        Up to rerank_n Chunk objects, sorted by cross-encoder rerank score
        descending (most relevant first).  Returns [] if the collection is
        empty or the query matches nothing.

    Raises:
        EmbeddingError: If the embedding NIM call fails.
        RerankError:    If the reranking NIM call fails.
        VectorStoreError: If the Milvus search fails.
    """
    settings = get_settings()

    # Read runtime-tunable params from system_config; init DB idempotently
    init_config_db(settings.config_db_path)
    top_k = get_config(settings.config_db_path, "top_k")
    rerank_n = get_config(settings.config_db_path, "rerank_n")
    rrf_k = get_config(settings.config_db_path, "rrf_k")

    log = logger.bind(
        query_preview=query[:80],
        top_k=top_k,
        rerank_n=rerank_n,
        rrf_k=rrf_k,
        has_filter=filter_expr is not None,
    )
    log.info("search.start")
    t0 = time.monotonic()

    # ── Step 1: embed query ────────────────────────────────────────────────
    # WHY input_type="query": nv-embedqa-e5-v5 is asymmetric — query and passage
    # embeddings are produced by different projection heads.  Using "passage" for
    # queries silently destroys cosine similarity and degrades recall.
    t_embed = time.monotonic()
    query_vectors = await embed_texts([query], input_type=_QUERY_INPUT_TYPE)
    query_vector = query_vectors[0]
    log.info("search.embedded", elapsed_ms=round((time.monotonic() - t_embed) * 1000))

    # ── Step 2: dense search ───────────────────────────────────────────────
    # filter_expr is the Phase 2 RBAC injection point — threads through unchanged.
    t_dense = time.monotonic()
    dense_chunks = store.dense_search(query_vector, top_k=top_k, filter_expr=filter_expr)
    dense_ids = [c.chunk_id for c in dense_chunks]
    log.info(
        "search.dense_done",
        hits=len(dense_chunks),
        elapsed_ms=round((time.monotonic() - t_dense) * 1000),
    )

    # ── Step 3: BM25 lexical search ────────────────────────────────────────
    t_bm25 = time.monotonic()
    bm25_hits = bm25_index.search(query, top_k=top_k)
    bm25_ids = [cid for cid, _ in bm25_hits]
    log.info(
        "search.bm25_done",
        hits=len(bm25_hits),
        elapsed_ms=round((time.monotonic() - t_bm25) * 1000),
    )

    # ── Step 4: RRF fusion ─────────────────────────────────────────────────
    fused_ids = rrf_fuse(dense_ids, bm25_ids, k=rrf_k)

    # Build lookup pool: dense chunks + any BM25-only chunks from the index
    pool: dict[str, Chunk] = {c.chunk_id: c for c in dense_chunks}
    for cid, _ in bm25_hits:
        if cid not in pool:
            bm25_chunk = bm25_index.get_chunk(cid)
            if bm25_chunk is not None:
                pool[cid] = bm25_chunk

    fused_candidates = [pool[cid] for cid in fused_ids if cid in pool]
    log.info("search.fused", candidate_count=len(fused_candidates))

    if not fused_candidates:
        log.warning("search.no_candidates")
        return []

    # ── Step 5: rerank ─────────────────────────────────────────────────────
    t_rerank = time.monotonic()
    final_chunks = await rerank(query, fused_candidates, top_n=rerank_n)
    log.info(
        "search.reranked",
        returned=len(final_chunks),
        elapsed_ms=round((time.monotonic() - t_rerank) * 1000),
        total_elapsed_ms=round((time.monotonic() - t0) * 1000),
    )

    return final_chunks
