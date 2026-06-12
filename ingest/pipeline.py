"""
ingest.pipeline — public entrypoint for the ingest slice.

Orchestrates parse → chunk and returns a list of schema-complete Chunks.
This is the only function callers outside the ingest package need to call
for Phase 1.  Later phases (embedding, Milvus insertion) will extend this
pipeline by consuming the returned chunks.

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
