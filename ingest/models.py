"""
ingest.models — schema-complete Chunk model.

Every chunk stored in Milvus carries ALL fields defined here from day one.
Phases populate them progressively (Phase 1 = text/table parsing; Phase 2 =
real RBAC values; Phase 6 = multimodal captions) but the shape never changes,
so we never need a costly re-ingest to add columns.

Design decisions recorded in docs/adr/ADR-001 and ADR-002.
"""

from __future__ import annotations

import hashlib
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class SensitivityLevel(StrEnum):
    """RBAC sensitivity axis — Phase 2 populates from real doc metadata."""

    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"


class ContentType(StrEnum):
    """Origin modality of the chunk content."""

    TEXT = "text"
    TABLE = "table"
    CHART = "chart"  # Phase 6: VLM-captioned chart images


# ---------------------------------------------------------------------------
# Chunk model
# ---------------------------------------------------------------------------


class Chunk(BaseModel):
    """A schema-complete chunk ready for embedding and Milvus insertion.

    Every field is present from day one (Phase 1).  Fields that are not yet
    populated by this phase are typed as ``Optional`` with ``None`` defaults
    and will be filled by later slices:
      - ``embedding``   — filled by the embedding slice (Phase 1 slice 2)
      - ``bm25_tokens`` — filled by the BM25 indexing slice (Phase 1 slice 3)
      - ``caption``     — filled by the VLM captioning slice (Phase 6)

    WHY access defaults here:
      Phase 2 replaces org_id / allowed_roles / sensitivity_level with values
      derived from real document metadata and the uploader's JWT claims.  For
      now we ship safe dev defaults so the rest of the pipeline can run
      end-to-end without auth.  The defaults are intentionally conservative
      (internal, owner-only) rather than open.
    """

    # ── Identity ─────────────────────────────────────────────────────────
    chunk_id: Annotated[str, Field(description="Deterministic SHA-256 of doc_id+page+index")]
    doc_id: Annotated[str, Field(description="Parent document identifier (UUID or path hash)")]
    doc_name: Annotated[str, Field(description="Original filename — used in citations")]
    page_number: Annotated[int, Field(ge=0, description="0-indexed source page number")]
    section: Annotated[str, Field(description="Nearest heading above this chunk, or empty str")]

    # ── Access (Phase 2 replaces these with real values) ─────────────────
    # WHY dev defaults: allow the full pipeline to run without auth infrastructure.
    # Phase 2 ingest will accept org_id/allowed_roles/sensitivity_level from the
    # JWT claims of the uploading user and overwrite these placeholders.
    org_id: Annotated[str, Field(description="Tenant organisation identifier")] = "dev"
    allowed_roles: Annotated[
        list[str],
        Field(description="Roles permitted to retrieve this chunk (ARRAY_CONTAINS filter)"),
    ] = Field(default_factory=lambda: ["owner"])
    sensitivity_level: SensitivityLevel = SensitivityLevel.INTERNAL

    # ── Retrieval ─────────────────────────────────────────────────────────
    text: Annotated[str, Field(min_length=1, description="The chunk text content")]
    # None until the embedding slice runs
    embedding: list[float] | None = None
    # None until the BM25 tokenisation slice runs
    bm25_tokens: list[str] | None = None

    # ── Multimodal ────────────────────────────────────────────────────────
    content_type: ContentType = ContentType.TEXT
    source_modality: Annotated[
        str,
        Field(description="How this chunk was extracted, e.g. 'docling-text', 'docling-table'"),
    ] = "docling-text"
    # None until the VLM captioning slice runs (Phase 6)
    caption: str | None = None

    @field_validator("chunk_id")
    @classmethod
    def chunk_id_must_be_nonempty(cls, v: str) -> str:
        """Ensure chunk_id is a non-empty hex string."""
        if not v:
            raise ValueError("chunk_id must not be empty")
        return v


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def make_chunk_id(doc_id: str, page_number: int, chunk_index: int) -> str:
    """Return a deterministic, stable chunk_id.

    The ID is the first 16 hex chars of SHA-256(doc_id:page:index).
    Using a hash (not a UUID4) means re-ingesting the same document with the
    same chunking parameters produces identical chunk_ids, which lets us
    upsert into Milvus idempotently rather than inserting duplicates.

    Args:
        doc_id:      Parent document identifier.
        page_number: 0-indexed page number.
        chunk_index: Position of this chunk within the page's chunks.

    Returns:
        A 16-character lowercase hex string.
    """
    payload = f"{doc_id}:{page_number}:{chunk_index}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def make_doc_id(doc_name: str) -> str:
    """Return a stable doc_id derived from the document filename.

    In Phase 3 this will be replaced by a UUID stored in the documents table.
    For now, hash the filename so identical uploads produce the same doc_id.

    Args:
        doc_name: The original filename (basename only).

    Returns:
        A 16-character lowercase hex string.
    """
    return hashlib.sha256(doc_name.encode()).hexdigest()[:16]
