"""
Tests for ingest.models — Chunk pydantic model and factory helpers.

All tests are fast (no Docling, no PDF I/O).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ingest.models import (
    Chunk,
    ContentType,
    SensitivityLevel,
    make_chunk_id,
    make_doc_id,
)

# ---------------------------------------------------------------------------
# Chunk construction
# ---------------------------------------------------------------------------


def _minimal_chunk(**overrides: object) -> Chunk:
    """Return a valid Chunk with sensible defaults, applying any overrides."""
    defaults: dict[str, object] = {
        "chunk_id": make_chunk_id("doc1", 0, 0),
        "doc_id": "doc1",
        "doc_name": "report.pdf",
        "page_number": 0,
        "section": "Introduction",
        "text": "Revenue grew 12% year-over-year.",
    }
    defaults.update(overrides)
    return Chunk(**defaults)  # type: ignore[arg-type]


def test_chunk_constructs_with_required_fields() -> None:
    chunk = _minimal_chunk()
    assert chunk.doc_id == "doc1"
    assert chunk.doc_name == "report.pdf"
    assert chunk.page_number == 0


def test_chunk_defaults_access_fields_to_dev_values() -> None:
    """Phase 1 default access fields must be the safe dev defaults."""
    chunk = _minimal_chunk()
    assert chunk.org_id == "dev"
    assert chunk.allowed_roles == ["owner"]
    assert chunk.sensitivity_level == SensitivityLevel.INTERNAL


def test_chunk_embedding_defaults_to_none() -> None:
    chunk = _minimal_chunk()
    assert chunk.embedding is None


def test_chunk_bm25_tokens_defaults_to_none() -> None:
    chunk = _minimal_chunk()
    assert chunk.bm25_tokens is None


def test_chunk_caption_defaults_to_none() -> None:
    chunk = _minimal_chunk()
    assert chunk.caption is None


def test_chunk_content_type_defaults_to_text() -> None:
    chunk = _minimal_chunk()
    assert chunk.content_type == ContentType.TEXT


def test_chunk_accepts_table_content_type() -> None:
    chunk = _minimal_chunk(
        content_type=ContentType.TABLE,
        source_modality="docling-table",
        text="| A | B |\n|---|---|\n| 1 | 2 |",
    )
    assert chunk.content_type == ContentType.TABLE


def test_chunk_accepts_all_sensitivity_levels() -> None:
    for level in SensitivityLevel:
        chunk = _minimal_chunk(sensitivity_level=level)
        assert chunk.sensitivity_level == level


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_bad_sensitivity_level_rejected() -> None:
    with pytest.raises(ValidationError):
        _minimal_chunk(sensitivity_level="top_secret")  # not a valid enum value


def test_bad_content_type_rejected() -> None:
    with pytest.raises(ValidationError):
        _minimal_chunk(content_type="image")  # not a valid enum value


def test_empty_text_rejected() -> None:
    with pytest.raises(ValidationError):
        _minimal_chunk(text="")


def test_negative_page_number_rejected() -> None:
    with pytest.raises(ValidationError):
        _minimal_chunk(page_number=-1)


def test_empty_chunk_id_rejected() -> None:
    with pytest.raises(ValidationError):
        _minimal_chunk(chunk_id="")


# ---------------------------------------------------------------------------
# make_chunk_id — determinism and stability
# ---------------------------------------------------------------------------


def test_chunk_id_is_deterministic() -> None:
    """Same inputs must always produce the same chunk_id."""
    id1 = make_chunk_id("doc_abc", 3, 7)
    id2 = make_chunk_id("doc_abc", 3, 7)
    assert id1 == id2


def test_chunk_id_differs_for_different_inputs() -> None:
    assert make_chunk_id("doc1", 0, 0) != make_chunk_id("doc1", 0, 1)
    assert make_chunk_id("doc1", 0, 0) != make_chunk_id("doc1", 1, 0)
    assert make_chunk_id("doc1", 0, 0) != make_chunk_id("doc2", 0, 0)


def test_chunk_id_is_16_hex_chars() -> None:
    cid = make_chunk_id("report.pdf", 0, 0)
    assert len(cid) == 16
    assert all(c in "0123456789abcdef" for c in cid)


# ---------------------------------------------------------------------------
# make_doc_id
# ---------------------------------------------------------------------------


def test_doc_id_is_deterministic() -> None:
    assert make_doc_id("annual_report.pdf") == make_doc_id("annual_report.pdf")


def test_doc_id_differs_for_different_filenames() -> None:
    assert make_doc_id("q1.pdf") != make_doc_id("q2.pdf")


def test_doc_id_is_16_hex_chars() -> None:
    did = make_doc_id("report.pdf")
    assert len(did) == 16
    assert all(c in "0123456789abcdef" for c in did)
