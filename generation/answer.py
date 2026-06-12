"""
generation.answer — answer_query: the Phase 1 RAG end-to-end entrypoint.

This module is the chain-server's ``generate`` method for Phase 1.  It wires
together the four Phase 1 subsystems into a single coroutine:

    document_search  →  build_rag_prompt  →  llm_client.generate  →  parse_citations

The result is an AnswerWithCitations — a structured object carrying the LLM's
response text and a list of verified citation sources (doc_name + page_number +
chunk_id drawn from the retrieved chunks).

Phase 2 RBAC extension point
-----------------------------
``filter_expr`` is passed unchanged to ``document_search``, which threads it
into the Milvus ANN search.  Phase 2 constructs:

    'org_id == "{org_id}" AND ARRAY_CONTAINS(allowed_roles, "{role}")'

and passes it here.  Forbidden chunks are excluded at the Milvus search level
and therefore never enter the RAG prompt or appear in citations.

Public API
----------
    answer_query(query, store, bm25_index, filter_expr) -> AnswerWithCitations
"""

from __future__ import annotations

import time

import structlog

from generation.citations import AnswerWithCitations, parse_citations
from generation.llm_client import generate
from generation.prompt import build_rag_prompt
from ingest.models import Chunk
from retrieval.bm25 import BM25Index
from retrieval.search import document_search
from retrieval.vector_store import MilvusStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def answer_query(
    query: str,
    store: MilvusStore,
    bm25_index: BM25Index,
    filter_expr: str | None = None,
) -> AnswerWithCitations:
    """End-to-end RAG: retrieve relevant chunks and generate a cited answer.

    Orchestrates: document_search → build_rag_prompt → generate → parse_citations.

    WHY filter_expr is threaded through (not applied here):
        The RBAC filter must execute inside the Milvus ANN search so that
        forbidden chunks are excluded before they become retrieval candidates.
        Applying it here — after retrieval — would allow forbidden chunks to
        silently enter the LLM context.  Threading the raw expression to
        document_search preserves the Phase 1 architecture invariant that RBAC
        filters run at the vector-store boundary.

    Args:
        query:       Natural-language question.
        store:       Initialised MilvusStore with an existing collection.
        bm25_index:  Pre-built BM25Index over the visible chunk corpus.
        filter_expr: Optional Milvus boolean expression (Phase 2 RBAC hook).
                     None = unrestricted search (Phase 1 default).

    Returns:
        AnswerWithCitations with the LLM's answer and verified source citations.

    Raises:
        EmbeddingError:    If the query embedding NIM call fails.
        RerankError:       If the reranking NIM call fails.
        VectorStoreError:  If the Milvus search fails.
        GenerationError:   If the LLM NIM call fails.
    """
    log = logger.bind(query_preview=query[:80], has_filter=filter_expr is not None)
    log.info("answer_query.start")
    t0 = time.monotonic()

    # ── Step 1: retrieve relevant chunks ──────────────────────────────────
    # filter_expr is the Phase 2 RBAC injection point — threads to Milvus ANN.
    chunks: list[Chunk] = await document_search(
        query=query,
        store=store,
        bm25_index=bm25_index,
        filter_expr=filter_expr,
    )
    log.info("answer_query.retrieved", chunk_count=len(chunks))

    if not chunks:
        log.warning("answer_query.no_chunks", msg="No chunks retrieved; returning empty answer.")
        return AnswerWithCitations(
            answer="I cannot answer this question from the provided documents.",
            sources=[],
        )

    # ── Step 2: build the RAG prompt ──────────────────────────────────────
    system_prompt, user_prompt = build_rag_prompt(query=query, chunks=chunks)

    # ── Step 3: generate the answer ───────────────────────────────────────
    raw_answer = await generate(system_prompt=system_prompt, user_prompt=user_prompt)

    # ── Step 4: enforce citations ─────────────────────────────────────────
    # WHY post-generation enforcement: we cannot control what the model outputs,
    # but we can verify that every cited [N] maps to an actual retrieved chunk
    # and warn if the model answered without any grounding citations.
    result = parse_citations(answer=raw_answer, chunks=chunks)

    elapsed = time.monotonic() - t0
    log.info(
        "answer_query.done",
        answer_length=len(result.answer),
        sources_cited=len(result.sources),
        elapsed_s=round(elapsed, 3),
    )
    return result
