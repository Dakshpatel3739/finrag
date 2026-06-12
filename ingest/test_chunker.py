"""
Tests for ingest.chunker — config-driven recursive chunker.

All tests are fast: they use the tiny_parsed_doc fixture (a hand-crafted
ParsedDoc, no Docling required) and a temp config DB.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ingest.chunker as chunker_module
from config.system_config import init_config_db, set_config
from ingest.chunker import chunk_document
from ingest.models import ContentType, SensitivityLevel
from ingest.parser import ParsedDoc, ParsedElement

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_config_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect all config DB reads/writes to a fresh temp DB for each test."""
    db = str(tmp_path / "config.db")
    init_config_db(db)
    monkeypatch.setattr(chunker_module, "_CONFIG_DB_PATH", db)


def make_text_doc(text: str, page: int = 0) -> ParsedDoc:
    """Convenience: a ParsedDoc with a single text element."""
    return ParsedDoc(
        doc_name="test.pdf",
        doc_id="testdoc",
        page_count=1,
        elements=[
            ParsedElement(
                text=text,
                page_number=page,
                section="Test Section",
                content_type=ContentType.TEXT,
                source_modality="docling-text",
            )
        ],
    )


def make_table_doc(table_md: str) -> ParsedDoc:
    """Convenience: a ParsedDoc with a single table element."""
    return ParsedDoc(
        doc_name="test.pdf",
        doc_id="testdoc",
        page_count=1,
        elements=[
            ParsedElement(
                text=table_md,
                page_number=0,
                section="Financials",
                content_type=ContentType.TABLE,
                source_modality="docling-table",
            )
        ],
    )


# ---------------------------------------------------------------------------
# All schema fields are populated
# ---------------------------------------------------------------------------


def test_all_schema_fields_populated(tiny_parsed_doc: ParsedDoc) -> None:
    """Every chunk must have every schema field set (no missing fields)."""
    chunks = chunk_document(
        tiny_parsed_doc,
        org_id="acme",
        allowed_roles=["owner", "finance"],
        sensitivity_level=SensitivityLevel.RESTRICTED,
    )
    assert chunks, "Expected at least one chunk"
    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.doc_id
        assert chunk.doc_name
        assert chunk.page_number >= 0
        assert chunk.section is not None
        assert chunk.org_id == "acme"
        assert chunk.allowed_roles == ["owner", "finance"]
        assert chunk.sensitivity_level == SensitivityLevel.RESTRICTED
        assert chunk.text
        assert chunk.content_type in ContentType
        assert chunk.source_modality
        # embedding and bm25_tokens are None until later slices
        assert chunk.embedding is None
        assert chunk.bm25_tokens is None


# ---------------------------------------------------------------------------
# chunk_size from config is respected
# ---------------------------------------------------------------------------


def test_chunk_size_respected(tmp_path: Path) -> None:
    """Chunks must not exceed chunk_size characters (except tables)."""
    db = str(tmp_path / "cfg.db")
    init_config_db(db)
    import ingest.chunker as mod

    mod._CONFIG_DB_PATH = db  # already monkeypatched but set explicitly too
    set_config(db, "chunk_size", 100)
    set_config(db, "chunk_overlap", 0)

    long_text = "word " * 200  # 1000 chars
    doc = make_text_doc(long_text)
    chunks = chunk_document(doc)

    for chunk in chunks:
        if chunk.content_type == ContentType.TEXT:
            assert len(chunk.text) <= 110, (  # small tolerance for separator
                f"Chunk exceeds chunk_size: {len(chunk.text)} chars"
            )


# ---------------------------------------------------------------------------
# Tables are NOT split
# ---------------------------------------------------------------------------


def test_table_is_not_split(tiny_parsed_doc: ParsedDoc) -> None:
    """A table element must always produce exactly one chunk."""
    table_elements = [e for e in tiny_parsed_doc.elements if e.content_type == ContentType.TABLE]
    assert table_elements, "Fixture must have at least one table element"

    table_doc = ParsedDoc(
        doc_name=tiny_parsed_doc.doc_name,
        doc_id=tiny_parsed_doc.doc_id,
        page_count=tiny_parsed_doc.page_count,
        elements=table_elements,
    )
    chunks = chunk_document(table_doc)
    assert len(chunks) == len(table_elements), "Each table element should produce exactly one chunk"
    for chunk in chunks:
        assert chunk.content_type == ContentType.TABLE


def test_large_table_is_not_split(tmp_path: Path) -> None:
    """Even a table larger than chunk_size must remain a single chunk."""
    db = str(tmp_path / "cfg.db")
    init_config_db(db)
    set_config(db, "chunk_size", 50)  # tiny chunk_size
    import ingest.chunker as mod

    mod._CONFIG_DB_PATH = db

    big_table = "| Col1 | Col2 | Col3 |\n|---|---|---|\n" + "\n".join(
        [f"| Row{i} | Val{i}a | Val{i}b |" for i in range(20)]
    )
    doc = make_table_doc(big_table)
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].content_type == ContentType.TABLE
    assert chunks[0].text == big_table


# ---------------------------------------------------------------------------
# content_type is correct
# ---------------------------------------------------------------------------


def test_text_element_produces_text_chunks(tiny_parsed_doc: ParsedDoc) -> None:
    text_elements = [e for e in tiny_parsed_doc.elements if e.content_type == ContentType.TEXT]
    text_doc = ParsedDoc(
        doc_name=tiny_parsed_doc.doc_name,
        doc_id=tiny_parsed_doc.doc_id,
        page_count=1,
        elements=text_elements,
    )
    chunks = chunk_document(text_doc)
    for chunk in chunks:
        assert chunk.content_type == ContentType.TEXT


def test_table_element_produces_table_chunks(tiny_parsed_doc: ParsedDoc) -> None:
    table_elements = [e for e in tiny_parsed_doc.elements if e.content_type == ContentType.TABLE]
    table_doc = ParsedDoc(
        doc_name=tiny_parsed_doc.doc_name,
        doc_id=tiny_parsed_doc.doc_id,
        page_count=1,
        elements=table_elements,
    )
    chunks = chunk_document(table_doc)
    for chunk in chunks:
        assert chunk.content_type == ContentType.TABLE


# ---------------------------------------------------------------------------
# Overlap: consecutive text chunks share a suffix/prefix
# ---------------------------------------------------------------------------


def test_chunk_overlap_produces_shared_context(tmp_path: Path) -> None:
    db = str(tmp_path / "cfg.db")
    init_config_db(db)
    set_config(db, "chunk_size", 80)
    set_config(db, "chunk_overlap", 20)
    import ingest.chunker as mod

    mod._CONFIG_DB_PATH = db

    # Enough text to produce multiple chunks
    text = "Alpha beta gamma. " * 15
    doc = make_text_doc(text)
    chunks = chunk_document(doc)

    if len(chunks) >= 2:
        # At least some content from chunk N must appear at the start of chunk N+1
        # (because we carry over chunk_overlap chars)
        c0_tail = chunks[0].text[-20:]
        c1_start = chunks[1].text[:30]
        assert any(word in c1_start for word in c0_tail.split()), (
            "Expected some overlap between consecutive text chunks"
        )


# ---------------------------------------------------------------------------
# chunk_id uniqueness and determinism
# ---------------------------------------------------------------------------


def test_chunk_ids_are_unique(tiny_parsed_doc: ParsedDoc) -> None:
    chunks = chunk_document(tiny_parsed_doc)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "chunk_ids must be unique within a document"


def test_chunk_ids_are_deterministic(tiny_parsed_doc: ParsedDoc) -> None:
    chunks_a = chunk_document(tiny_parsed_doc)
    chunks_b = chunk_document(tiny_parsed_doc)
    assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]
