"""
ingest.chunker — config-driven recursive chunker.

Converts a ParsedDoc into a list of schema-complete Chunks.

Chunking strategy (see ADR-002):
  - Text elements are split with a recursive character splitter that respects
    paragraph and sentence boundaries before resorting to hard character cuts.
  - Table elements are kept as SINGLE chunks, regardless of size.
    WHY: splitting a Markdown table mid-row produces malformed fragments that
    embed poorly and cannot be rendered as a table in citations.  A table that
    is genuinely too large to embed in one call will be handled by
    truncation-with-warning in the embedding slice, not by mid-row splitting.
  - chunk_size and chunk_overlap are read from system_config (NOT hardcoded)
    so they can be tuned at runtime without a redeploy (ADR-001 §6).
"""

from __future__ import annotations

from pathlib import Path

import structlog

from config.system_config import get_config, init_config_db
from ingest.errors import ChunkError
from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
from ingest.parser import ParsedDoc, ParsedElement

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Path to the shared config DB.  Matches the default in settings.py.
# Tests can monkey-patch _CONFIG_DB_PATH before calling chunk_document.
_CONFIG_DB_PATH: str | Path = "finrag_config.db"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def chunk_document(
    parsed_doc: ParsedDoc,
    org_id: str = "dev",
    allowed_roles: list[str] | None = None,
    sensitivity_level: SensitivityLevel = SensitivityLevel.INTERNAL,
) -> list[Chunk]:
    """Convert a ParsedDoc into a list of schema-complete Chunks.

    Reads chunk_size and chunk_overlap from the runtime config DB so the
    parameters can be changed without a redeploy.

    Tables are kept as single atomic chunks (see module docstring for WHY).
    Text elements are recursively split to at most chunk_size characters,
    with chunk_overlap characters of context carry-over between adjacent
    chunks.

    Args:
        parsed_doc:        Output of parse_pdf() or a hand-crafted fixture.
        org_id:            Tenant identifier.  Phase 2 sets this from JWT.
        allowed_roles:     RBAC roles.  Defaults to ["owner"] — Phase 2 sets real roles.
        sensitivity_level: Access tier.  Phase 2 sets from doc metadata.

    Returns:
        A list of Chunks with every schema field populated.

    Raises:
        ChunkError: If chunking produces zero chunks from a non-empty document.
    """
    if allowed_roles is None:
        allowed_roles = ["owner"]

    # Pull tuning parameters from runtime config (never hardcoded — ADR-001 §6)
    _ensure_config_db()
    chunk_size = get_config(_CONFIG_DB_PATH, "chunk_size")
    chunk_overlap = get_config(_CONFIG_DB_PATH, "chunk_overlap")

    log = logger.bind(
        doc_name=parsed_doc.doc_name,
        doc_id=parsed_doc.doc_id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    log.info("ingest.chunker.start", element_count=len(parsed_doc.elements))

    chunks: list[Chunk] = []
    chunk_index = 0  # global index across all pages for stable chunk_id

    for element in parsed_doc.elements:
        new_chunks = _chunk_element(
            element=element,
            doc_id=parsed_doc.doc_id,
            doc_name=parsed_doc.doc_name,
            org_id=org_id,
            allowed_roles=allowed_roles,
            sensitivity_level=sensitivity_level,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunk_index_start=chunk_index,
        )
        chunks.extend(new_chunks)
        chunk_index += len(new_chunks)

    if not chunks and parsed_doc.elements:
        raise ChunkError(
            f"Chunking produced 0 chunks from {len(parsed_doc.elements)} elements "
            f"in {parsed_doc.doc_name!r}"
        )

    content_counts = {ct.value: 0 for ct in ContentType}
    for c in chunks:
        content_counts[c.content_type] += 1

    log.info(
        "ingest.chunker.done",
        chunk_count=len(chunks),
        content_type_breakdown=content_counts,
    )
    return chunks


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _chunk_element(
    element: ParsedElement,
    doc_id: str,
    doc_name: str,
    org_id: str,
    allowed_roles: list[str],
    sensitivity_level: SensitivityLevel,
    chunk_size: int,
    chunk_overlap: int,
    chunk_index_start: int,
) -> list[Chunk]:
    """Produce one or more Chunks from a single ParsedElement.

    Tables → one chunk (never split).
    Text   → recursively split into chunks of at most chunk_size chars.
    """
    if element.content_type == ContentType.TABLE:
        # WHY: tables are atomic — see module docstring.
        return [
            _make_chunk(
                text=element.text,
                doc_id=doc_id,
                doc_name=doc_name,
                page_number=element.page_number,
                section=element.section,
                org_id=org_id,
                allowed_roles=allowed_roles,
                sensitivity_level=sensitivity_level,
                content_type=ContentType.TABLE,
                source_modality=element.source_modality,
                chunk_index=chunk_index_start,
            )
        ]

    # Text: recursive character split
    splits = _recursive_split(element.text, chunk_size, chunk_overlap)
    return [
        _make_chunk(
            text=split,
            doc_id=doc_id,
            doc_name=doc_name,
            page_number=element.page_number,
            section=element.section,
            org_id=org_id,
            allowed_roles=allowed_roles,
            sensitivity_level=sensitivity_level,
            content_type=ContentType.TEXT,
            source_modality=element.source_modality,
            chunk_index=chunk_index_start + i,
        )
        for i, split in enumerate(splits)
    ]


def _make_chunk(
    *,
    text: str,
    doc_id: str,
    doc_name: str,
    page_number: int,
    section: str,
    org_id: str,
    allowed_roles: list[str],
    sensitivity_level: SensitivityLevel,
    content_type: ContentType,
    source_modality: str,
    chunk_index: int,
) -> Chunk:
    """Instantiate a fully-populated Chunk."""
    return Chunk(
        chunk_id=make_chunk_id(doc_id, page_number, chunk_index),
        doc_id=doc_id,
        doc_name=doc_name,
        page_number=page_number,
        section=section,
        org_id=org_id,
        allowed_roles=list(allowed_roles),
        sensitivity_level=sensitivity_level,
        text=text,
        # embedding and bm25_tokens filled by later slices
        embedding=None,
        bm25_tokens=None,
        content_type=content_type,
        source_modality=source_modality,
        caption=None,
    )


def _recursive_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split *text* into chunks of at most *chunk_size* characters.

    Tries to break at paragraph boundaries (double newline), then single
    newlines, then spaces, before resorting to hard character cuts.  This
    mirrors the behaviour of LangChain's RecursiveCharacterTextSplitter but
    without the LangChain dependency.

    Args:
        text:         The text to split.
        chunk_size:   Maximum characters per chunk.
        chunk_overlap: Number of characters to carry over from the previous
                       chunk (for context continuity).

    Returns:
        A list of non-empty string chunks.
    """
    if len(text) <= chunk_size:
        stripped = text.strip()
        return [stripped] if stripped else []

    separators = ["\n\n", "\n", ". ", " ", ""]
    return _split_with_separators(text, chunk_size, chunk_overlap, separators)


def _split_with_separators(
    text: str, chunk_size: int, chunk_overlap: int, separators: list[str]
) -> list[str]:
    """Recursively split text using the first separator that makes progress."""
    if not separators:
        # Hard character cut as last resort
        return _hard_split(text, chunk_size, chunk_overlap)

    sep = separators[0]
    remaining = separators[1:]

    if sep == "":
        return _hard_split(text, chunk_size, chunk_overlap)

    parts = text.split(sep)
    if len(parts) == 1:
        # This separator doesn't appear in the text; try the next one
        return _split_with_separators(text, chunk_size, chunk_overlap, remaining)

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for part in parts:
        part_len = len(part) + len(sep)
        if current_len + part_len > chunk_size and current:
            chunk_text = sep.join(current).strip()
            if chunk_text:
                # Sub-split any piece that is still too big
                if len(chunk_text) > chunk_size:
                    chunks.extend(
                        _split_with_separators(chunk_text, chunk_size, chunk_overlap, remaining)
                    )
                else:
                    chunks.append(chunk_text)
            # Overlap: keep last portion up to chunk_overlap chars
            overlap_text = sep.join(current)[-chunk_overlap:] if chunk_overlap > 0 else ""
            current = [overlap_text] if overlap_text else []
            current_len = len(overlap_text)
        current.append(part)
        current_len += part_len

    # Flush remainder
    if current:
        chunk_text = sep.join(current).strip()
        if chunk_text:
            if len(chunk_text) > chunk_size:
                chunks.extend(
                    _split_with_separators(chunk_text, chunk_size, chunk_overlap, remaining)
                )
            else:
                chunks.append(chunk_text)

    return [c for c in chunks if c.strip()]


def _hard_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Hard character-level split as a last resort."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - chunk_overlap if chunk_overlap > 0 else end
        if start >= len(text):
            break
    return chunks


def _ensure_config_db() -> None:
    """Initialise the config DB if it hasn't been seeded yet."""
    init_config_db(_CONFIG_DB_PATH)
