"""
ingest — PDF parsing and chunking pipeline.

Public API for Phase 1:
    ingest_pdf(path, ...)  → list[Chunk]

The returned Chunks have all schema fields populated; ``embedding`` and
``bm25_tokens`` are ``None`` until the later pipeline slices run.
"""

from ingest.errors import ChunkError, IngestError, ParseError
from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id, make_doc_id
from ingest.pipeline import ingest_pdf

__all__ = [
    "Chunk",
    "ChunkError",
    "ContentType",
    "IngestError",
    "ParseError",
    "SensitivityLevel",
    "ingest_pdf",
    "make_chunk_id",
    "make_doc_id",
]
