"""
ingest.pipeline — public entrypoints for the ingest slice.

Two entry points:

  ingest_pdf(path, ...)
      Parse → chunk only.  Returns a list of schema-complete Chunks with
      embedding=None.  No network, no Milvus.  Used by the embedding step
      and by tests that need parsed chunks without NIM overhead.

  ingest_and_store(path, ...)   [async]
      Full Phase-1 end-to-end: parse → chunk → embed → ensure_collection
      → upsert.  This is the single function an API caller needs to ingest
      a document in Phase 1.  Returns the number of rows written to Milvus.

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

logger: structlog.BoundLogger = structlog.get_logger(__name__)


def ingest_pdf(
    path: str | Path,
    org_id: str = "dev",
    allowed_roles: tuple[str, ...] | list[str] = ("owner",),
    sensitivity_level: str | SensitivityLevel = SensitivityLevel.INTERNAL,
) -> list[Chunk]:
    """Parse a PDF and return schema-complete chunks ready for embedding.

    This is the Phase 1 public entry point.  It does NOT embed or write to
    Milvus — those are the next slices.

    Args:
        path:              Filesystem path to the PDF.
        org_id:            Tenant identifier (Phase 2 sets from JWT).
        allowed_roles:     RBAC roles allowed to retrieve chunks from this doc.
        sensitivity_level: Access sensitivity tier (Phase 2 sets from metadata).

    Returns:
        A list of Chunk objects with all schema fields populated.
        ``embedding`` and ``bm25_tokens`` are ``None`` (filled by later slices).

    Raises:
        IngestError: On any parse or chunking failure (never bare Exception).
    """
    path = Path(path)
    level = SensitivityLevel(sensitivity_level)
    roles = list(allowed_roles)

    log = logger.bind(doc_name=path.name, org_id=org_id, path=str(path))
    log.info("ingest.pipeline.start")

    try:
        parsed_doc = parse_pdf(path)
    except IngestError:
        # Already logged inside parse_pdf; re-raise so callers can handle it
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
        chunks = chunk_document(
            parsed_doc,
            org_id=org_id,
            allowed_roles=roles,
            sensitivity_level=level,
        )
    except IngestError:
        raise
    except Exception as exc:
        log.error("ingest.pipeline.unexpected_chunk_error", error=str(exc))
        raise IngestError(f"Unexpected error chunking {path}: {exc}") from exc

    # Log breakdown by content type
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
    allowed_roles: tuple[str, ...] | list[str] = ("owner",),
    sensitivity_level: str | SensitivityLevel = SensitivityLevel.INTERNAL,
) -> int:
    """Parse, embed, and store a PDF — the full Phase-1 ingest entrypoint.

    Orchestrates the complete pipeline:
        ingest_pdf   → parse + chunk (no network)
        embed_chunks → NeMo NIM embedding (requires NIM_API_KEY)
        ensure_collection → create Milvus collection if absent (idempotent)
        insert_chunks → upsert embedded chunks into Milvus

    Args:
        path:              Path to the PDF file.
        org_id:            Tenant identifier (Phase 2 sets from JWT; default "dev").
        allowed_roles:     RBAC roles allowed to retrieve chunks from this doc.
        sensitivity_level: Sensitivity tier (Phase 2 sets from doc metadata).

    Returns:
        Number of rows written to Milvus (as reported by upsert_count).

    Raises:
        IngestError:      If parsing or chunking fails.
        EmbeddingError:   If the NIM embedding call fails.
        VectorStoreError: If the Milvus write fails.
    """
    # Import here to avoid circular dependency and keep imports lazy
    # (retrieval is a separate domain; ingest should not hard-depend on it).
    from ingest.embedder import embed_chunks
    from retrieval.vector_store import MilvusStore

    path = Path(path)
    log = logger.bind(doc_name=path.name, org_id=org_id)
    log.info("pipeline.ingest_and_store.start")

    chunks = ingest_pdf(
        path,
        org_id=org_id,
        allowed_roles=allowed_roles,
        sensitivity_level=sensitivity_level,
    )

    if not chunks:
        log.warning("pipeline.ingest_and_store.no_chunks")
        return 0

    embedded = await embed_chunks(chunks)

    # Detect dimension from the first vector — never hardcode
    first_emb = embedded[0].embedding
    if first_emb is None:  # pragma: no cover — embed_chunks guarantees non-None
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
