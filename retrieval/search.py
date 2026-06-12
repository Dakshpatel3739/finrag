"""
retrieval.search — document_search: the hybrid retrieval + reranking orchestrator.

This is the chain-server's documentSearch method.  It wires together the four
retrieval sub-systems into a single function that a caller invokes with a plain
query string and an RBAC identity (org_id + role).

Pipeline:
    1. build RBAC filter  — from (org_id, role) via rbac.filter
    2. embed query         — nv-embedqa-e5-v5 with input_type="query"
    3. dense_search        — Milvus ANN search (COSINE) with RBAC filter
    4. bm25_search         — BM25Okapi lexical search, then RBAC-filtered in-memory
    5. rrf_fuse            — Reciprocal Rank Fusion
    6. rerank              — cross-encoder NIM re-scores shortlist

WHY RBAC filtering at TWO levels (Milvus + BM25):
    Dense search is filtered by the Milvus boolean expression (enforced at the
    C++ storage layer — forbidden chunks never materialise in Python).
    BM25 search runs over an in-memory corpus-wide index, so forbidden chunks
    can appear in BM25 hits before filtering.  We filter BM25 results against
    the same RBAC policy before they enter the RRF fusion step.  This ensures
    forbidden chunks never reach the reranker or the LLM context window,
    regardless of which retrieval path surfaced them.

WHY input_type="query" for query embedding:
    nv-embedqa-e5-v5 is an asymmetric QA model.  Document chunks are embedded
    with input_type="passage" at ingest time.  If the same encoder head were used
    for queries, cosine distances would be meaningless.

RBAC audit log:
    Every call logs org_id, role, filter applied, and result count to structlog.
    This provides a queryable audit trail without a separate audit database.

Public API
----------
    document_search(query, store, bm25_index, org_id, role, filter_expr) -> list[Chunk]
"""

from __future__ import annotations

import time

import structlog

from config.settings import get_settings
from config.system_config import get_config, init_config_db
from ingest.models import Chunk
from ingest.nim_client import InputType, embed_texts
from rbac.filter import build_rbac_filter
from rbac.roles import Role
from retrieval.bm25 import BM25Index
from retrieval.fusion import rrf_fuse
from retrieval.reranker import rerank
from retrieval.vector_store import MilvusStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_QUERY_INPUT_TYPE: InputType = "query"


def _passes_rbac(chunk: Chunk, org_id: str, role: Role) -> bool:
    """Return True if chunk is visible to the given org and role.

    Used to post-filter BM25 results, which come from a corpus-wide in-memory
    index that has no Milvus-side filter.  We check the chunk's actual metadata
    (org_id + allowed_roles) rather than recomputing from the policy, because
    the chunk's allowed_roles field IS the ground truth at query time.

    WHY check allowed_roles directly (not via can_role_see):
        can_role_see(role, sensitivity_level) encodes the policy default.
        chunk.allowed_roles encodes what was actually set at ingest time, which
        may have been overridden by an explicit classification.  The chunk's
        field is authoritative.
    """
    return chunk.org_id == org_id and str(role) in chunk.allowed_roles


async def document_search(
    query: str,
    store: MilvusStore,
    bm25_index: BM25Index,
    org_id: str | None = None,
    role: Role | None = None,
    filter_expr: str | None = None,
) -> list[Chunk]:
    """Hybrid retrieval + reranking with RBAC enforcement.

    Orchestrates: build_filter → embed → dense_search (filtered) →
    bm25_search (post-filtered) → rrf_fuse → rerank.

    RBAC enforcement:
        Provide org_id + role to activate full RBAC enforcement.  The filter
        expression is built via rbac.filter.build_rbac_filter and applied at
        both the Milvus layer (dense search) and in-memory (BM25 post-filter).

        Alternatively, provide filter_expr directly for admin/eval paths that
        need a custom filter without a Role enum value.

        If neither is provided, no filter is applied (internal/eval path only).

    Security note on BM25 filtering:
        The BM25 index is corpus-wide; it has no Milvus-side access control.
        When org_id + role are provided, BM25 hits are post-filtered by
        _passes_rbac() before entering the fusion step.  This ensures forbidden
        chunks never reach the reranker or the LLM — the same invariant as the
        Milvus dense-search filter.

    Security audit log:
        Every call logs org_id, role, effective filter expression, and result
        count.  This provides an audit trail for access pattern analysis.

    Args:
        query:       Natural-language query string.
        store:       Initialised MilvusStore with an existing collection.
        bm25_index:  Pre-built BM25Index over the chunk corpus.
        org_id:      Tenant identifier for RBAC filtering.
        role:        Querying user's role for RBAC filtering.
        filter_expr: Direct Milvus filter expression (admin/eval override).
                     Ignored if org_id + role are both provided.

    Returns:
        Up to rerank_n Chunk objects sorted by cross-encoder score desc.
        Returns [] if the collection is empty or no chunks pass the filter.

    Raises:
        EmbeddingError:    If the embedding NIM call fails.
        RerankError:       If the reranking NIM call fails.
        VectorStoreError:  If the Milvus search fails.
    """
    settings = get_settings()

    init_config_db(settings.config_db_path)
    top_k = get_config(settings.config_db_path, "top_k")
    rerank_n = get_config(settings.config_db_path, "rerank_n")
    rrf_k = get_config(settings.config_db_path, "rrf_k")

    # Build or select the effective Milvus filter expression.
    # WHY (org_id, role) takes precedence over filter_expr:
    #   The typed RBAC path is the normal entrypoint; filter_expr is an escape
    #   hatch for eval/admin.  If a caller passes both, they almost certainly
    #   want RBAC — silently ignoring the type-safe path would be surprising.
    effective_filter: str | None
    rbac_active = org_id is not None and role is not None
    if rbac_active:
        assert org_id is not None and role is not None  # narrow for mypy
        effective_filter = build_rbac_filter(org_id, role)
    else:
        effective_filter = filter_expr

    log = logger.bind(
        query_preview=query[:80],
        org_id=org_id,
        role=str(role) if role is not None else None,
        has_filter=effective_filter is not None,
        top_k=top_k,
        rerank_n=rerank_n,
    )
    log.info("search.start")
    t0 = time.monotonic()

    # ── Step 1: embed query ────────────────────────────────────────────────
    t_embed = time.monotonic()
    query_vectors = await embed_texts([query], input_type=_QUERY_INPUT_TYPE)
    query_vector = query_vectors[0]
    log.info("search.embedded", elapsed_ms=round((time.monotonic() - t_embed) * 1000))

    # ── Step 2: dense search (Milvus RBAC filter applied here) ────────────
    t_dense = time.monotonic()
    dense_chunks = store.dense_search(query_vector, top_k=top_k, filter_expr=effective_filter)
    log.info(
        "search.dense_done",
        hits=len(dense_chunks),
        elapsed_ms=round((time.monotonic() - t_dense) * 1000),
    )

    # ── Step 3: BM25 lexical search + RBAC post-filter ────────────────────
    t_bm25 = time.monotonic()
    raw_bm25_hits = bm25_index.search(query, top_k=top_k)

    if rbac_active:
        assert org_id is not None and role is not None  # narrow for mypy
        # WHY post-filter BM25: the BM25 index has no Milvus-side filter.
        # Without this step, restricted chunks from other orgs could enter the
        # RRF fusion pool and ultimately the LLM context window.
        bm25_hits = [
            (cid, score)
            for cid, score in raw_bm25_hits
            if (chunk := bm25_index.get_chunk(cid)) is not None
            and _passes_rbac(chunk, org_id, role)
        ]
    else:
        bm25_hits = raw_bm25_hits

    bm25_ids = [cid for cid, _ in bm25_hits]
    log.info(
        "search.bm25_done",
        hits=len(bm25_hits),
        bm25_filtered_count=len(raw_bm25_hits) - len(bm25_hits),
        elapsed_ms=round((time.monotonic() - t_bm25) * 1000),
    )

    # ── Step 4: RRF fusion ─────────────────────────────────────────────────
    dense_ids = [c.chunk_id for c in dense_chunks]
    fused_ids = rrf_fuse(dense_ids, bm25_ids, k=rrf_k)

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
