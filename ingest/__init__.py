"""
ingest — PDF parsing and chunking pipeline.

Public API for Phase 1:
    ingest_pdf(path, ...)  → list[Chunk]  (import from ingest.pipeline)

The returned Chunks have all schema fields populated; ``embedding`` and
``bm25_tokens`` are ``None`` until the later pipeline slices run.

WHY ingest_pdf is not re-exported from this __init__:
    ingest.pipeline imports rbac.classifier, which imports rbac.roles, which
    imports ingest.models.  Eagerly importing ingest.pipeline here creates a
    circular import when api.identity (which imports rbac.roles) is loaded
    before the ingest package has finished initialising.  The safe pattern is:
    import ingest_pdf directly from ingest.pipeline at the call site.
"""

from ingest.errors import ChunkError, IngestError, ParseError
from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id, make_doc_id

__all__ = [
    "Chunk",
    "ChunkError",
    "ContentType",
    "IngestError",
    "ParseError",
    "SensitivityLevel",
    "make_chunk_id",
    "make_doc_id",
]
