"""
generation.answer — answer_query: the end-to-end RAG entrypoint.

This module is the chain-server's ``generate`` method.  It wires together:

    document_search  →  build_rag_prompt  →  llm_client.generate  →  parse_citations

The result is an AnswerWithCitations — carrying the LLM's response text and
verified citation sources (doc_name + page_number + chunk_id).

RBAC enforcement:
    answer_query accepts (org_id, role) and passes them to document_search,
    which builds the Milvus filter and BM25 post-filter from them.  Forbidden
    chunks are excluded at the Milvus storage layer before any Python code sees
    them — they can never enter the RAG prompt or appear in citations.

    The filter_expr escape hatch is retained for admin/eval paths.  If org_id
    + role are provided, they take precedence over filter_expr.

Public API
----------
    answer_query(query, store, bm25_index, org_id, role, filter_expr)
        -> AnswerWithCitations
"""

from __future__ import annotations

import time

import structlog

from generation.citations import AnswerWithCitations, parse_citations
from generation.llm_client import generate
from generation.prompt import build_rag_prompt
from ingest.models import Chunk
from rbac.roles import Role
from retrieval.bm25 import BM25Index
from retrieval.search import document_search
from retrieval.vector_store import MilvusStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def answer_query(
    query: str,
    store: MilvusStore,
    bm25_index: BM25Index,
    org_id: str | None = None,
    role: Role | None = None,
    filter_expr: str | None = None,
) -> AnswerWithCitations:
    """End-to-end RAG with RBAC: retrieve → prompt → generate → cite.

    Orchestrates: document_search (RBAC-filtered) → build_rag_prompt →
    generate → parse_citations.

    RBAC enforcement path:
        Provide org_id + role for the normal query path.  They are forwarded
        to document_search, which builds the Milvus RBAC filter and applies
        a BM25 post-filter.  Forbidden chunks never enter the RAG prompt.

        filter_expr is an escape hatch for admin/eval paths that need a custom
        Milvus filter without a typed Role.  If org_id + role are both provided,
        they take precedence and filter_expr is ignored.

    Args:
        query:       Natural-language question.
        store:       Initialised MilvusStore with an existing collection.
        bm25_index:  Pre-built BM25Index over the visible chunk corpus.
        org_id:      Tenant identifier (RBAC path).
        role:        Querying user's role (RBAC path).
        filter_expr: Direct Milvus filter expression (admin/eval override).

    Returns:
        AnswerWithCitations with the LLM's answer and verified source citations.

    Raises:
        EmbeddingError:    If the query embedding NIM call fails.
        RerankError:       If the reranking NIM call fails.
        VectorStoreError:  If the Milvus search fails.
        GenerationError:   If the LLM NIM call fails.
    """
    log = logger.bind(
        query_preview=query[:80],
        org_id=org_id,
        role=str(role) if role is not None else None,
        has_filter=filter_expr is not None or (org_id is not None and role is not None),
    )
    log.info("answer_query.start")
    t0 = time.monotonic()

    # RBAC filter is built inside document_search from (org_id, role).
    # WHY pass through (not build here): document_search also applies the same
    # filter to BM25 results.  Building it in one place (document_search) ensures
    # both retrieval paths see the identical policy.
    chunks: list[Chunk] = await document_search(
        query=query,
        store=store,
        bm25_index=bm25_index,
        org_id=org_id,
        role=role,
        filter_expr=filter_expr,
    )
    log.info("answer_query.retrieved", chunk_count=len(chunks))

    if not chunks:
        log.warning("answer_query.no_chunks")
        return AnswerWithCitations(
            answer="I cannot answer this question from the provided documents.",
            sources=[],
        )

    system_prompt, user_prompt = build_rag_prompt(query=query, chunks=chunks)
    raw_answer = await generate(system_prompt=system_prompt, user_prompt=user_prompt)
    result = parse_citations(answer=raw_answer, chunks=chunks)

    elapsed = time.monotonic() - t0
    log.info(
        "answer_query.done",
        answer_length=len(result.answer),
        sources_cited=len(result.sources),
        elapsed_s=round(elapsed, 3),
    )
    return result
