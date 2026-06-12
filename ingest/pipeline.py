"""
ingest.pipeline — public entrypoints for the ingest slice.

Two entry points:

  ingest_pdf(path, ...)
      Parse → chunk → classify.  Returns a list of schema-complete Chunks
      with real org_id, sensitivity_level, and allowed_roles (Phase 2).
      embedding=None (filled by the embedding step).

  ingest_and_store(path, ...)   [async]
      Full end-to-end: parse → chunk → classify → embed → ensure_collection
      → upsert.  This is the single function an API caller needs to ingest
      a document.  Returns the number of rows written to Milvus.

Phase 2 change from Phase 1:
  allowed_roles is no longer a caller parameter.  It is derived automatically
  from the sensitivity_level via the policy table in rbac.roles.  This
  prevents privilege-escalation errors from callers specifying incorrect roles.
  sensitivity_level=None invokes the heuristic classifier (best-effort).

Structured logging at every boundary makes it easy to trace throughput,
spot errors, and wire metrics into Prometheus (Phase 5).
"""

from __future__ import annotations

from pathlib import Path

import structlog

from ingest.chunker import chunk_document
from ingest.errors import IngestError
from ingest.models import Chunk, ContentType, SensitivityLevel
from ingest.parser import parse_pdf
from rbac.classifier import assign_access

logger: structlog.BoundLogger = structlog.get_logger(__name__)


def ingest_pdf(
    path: str | Path,
    org_id: str = "dev",
    sensitivity_level: SensitivityLevel | None = None,
) -> list[Chunk]:
    """Parse a PDF and return schema-complete chunks with real RBAC metadata.

    Chunks are stamped with org_id, sensitivity_level, and allowed_roles
    by rbac.classifier.assign_access.  If sensitivity_level is None, the
    heuristic classifier inspects each chunk's text/section for restricted
    signals; otherwise the provided level is applied to all chunks.

    This does NOT embed or write to Milvus — those are downstream steps.

    Args:
        path:              Filesystem path to the PDF.
        org_id:            Tenant organisation identifier.
        sensitivity_level: Access sensitivity tier.  None = use heuristic
                           per-chunk classification (best-effort).

    Returns:
        A list of Chunk objects with all schema fields populated.
        ``embedding`` and ``bm25_tokens`` are ``None`` (filled later).

    Raises:
        IngestError: On any parse or chunking failure (never bare Exception).
    """
    path = Path(path)
    log = logger.bind(doc_name=path.name, org_id=org_id, path=str(path))
    log.info("ingest.pipeline.start")

    try:
        parsed_doc = parse_pdf(path)
    except IngestError:
        raise
    except Exception as exc:
        log.error("ingest.pipeline.unexpected_parse_error", error=str(exc))
        raise IngestError(f"Unexpected error parsing {path}: {exc}") from exc

    log.info(
        "ingest.pipeline.parsed",
        page_count=parsed_doc.page_count,
        element_count=len(parsed_doc.elements),
    )

    try:
        # chunk_document sets placeholder allowed_roles; assign_access overwrites
        # them with the policy-derived list for the actual sensitivity level.
        raw_chunks = chunk_document(parsed_doc, org_id=org_id)
    except IngestError:
        raise
    except Exception as exc:
        log.error("ingest.pipeline.unexpected_chunk_error", error=str(exc))
        raise IngestError(f"Unexpected error chunking {path}: {exc}") from exc

    # Apply RBAC classification: stamp real sensitivity_level + allowed_roles.
    # WHY per-chunk (not per-document): the heuristic classifier can assign
    # different sensitivities to different sections of the same document
    # (e.g. a salary table on page 8 gets RESTRICTED; other pages stay INTERNAL).
    # Explicit sensitivity_level overrides the heuristic for all chunks.
    chunks: list[Chunk] = [
        assign_access(chunk, org_id=org_id, sensitivity_level=sensitivity_level)
        for chunk in raw_chunks
    ]

    breakdown = {ct.value: 0 for ct in ContentType}
    for chunk in chunks:
        breakdown[chunk.content_type] += 1

    log.info(
        "ingest.pipeline.done",
        chunk_count=len(chunks),
        content_type_breakdown=breakdown,
    )
    return chunks


async def ingest_and_store(
    path: str | Path,
    org_id: str = "dev",
    sensitivity_level: SensitivityLevel | None = None,
) -> int:
    """Parse, embed, and store a PDF — the full ingest entrypoint.

    Orchestrates the complete pipeline:
        ingest_pdf   → parse + chunk + classify (no network)
        embed_chunks → NeMo NIM embedding (requires NIM_API_KEY)
        ensure_collection → create Milvus collection if absent (idempotent)
        insert_chunks → upsert embedded chunks into Milvus

    Args:
        path:              Path to the PDF file.
        org_id:            Tenant organisation identifier.
        sensitivity_level: Sensitivity tier.  None = heuristic per-chunk
                           classification.

    Returns:
        Number of rows written to Milvus (as reported by upsert_count).

    Raises:
        IngestError:      If parsing or chunking fails.
        EmbeddingError:   If the NIM embedding call fails.
        VectorStoreError: If the Milvus write fails.
    """
    from ingest.embedder import embed_chunks
    from retrieval.vector_store import MilvusStore

    path = Path(path)
    log = logger.bind(doc_name=path.name, org_id=org_id)
    log.info("pipeline.ingest_and_store.start")

    chunks = ingest_pdf(path, org_id=org_id, sensitivity_level=sensitivity_level)

    if not chunks:
        log.warning("pipeline.ingest_and_store.no_chunks")
        return 0

    embedded = await embed_chunks(chunks)

    first_emb = embedded[0].embedding
    if first_emb is None:  # pragma: no cover
        raise IngestError("embed_chunks returned a chunk with None embedding")
    dim = len(first_emb)

    store = MilvusStore()
    store.ensure_collection(dim)
    count = store.insert_chunks(embedded)

    log.info(
        "pipeline.ingest_and_store.done",
        chunk_count=len(embedded),
        rows_stored=count,
        embedding_dim=dim,
    )
    return count
