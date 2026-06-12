"""
Tests for ingest.parser — Docling PDF parser.

Fast tests: work directly with ParsedDoc/ParsedElement dataclasses (no Docling).
Slow tests: call parse_pdf() against a real PDF — require Docling to be
installed and are marked @pytest.mark.slow so CI can skip them with
  pytest -m "not slow"

To run slow tests locally:
  pytest ingest/test_parser.py -m slow
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingest.errors import ParseError
from ingest.models import ContentType
from ingest.parser import ParsedDoc, ParsedElement, parse_pdf

# ---------------------------------------------------------------------------
# Fast unit tests — no Docling required
# ---------------------------------------------------------------------------


def test_parsed_doc_dataclass_construction() -> None:
    """ParsedDoc and ParsedElement can be constructed directly."""
    elem = ParsedElement(
        text="Net revenue: $4.2B",
        page_number=0,
        section="Financial Highlights",
        content_type=ContentType.TEXT,
        source_modality="docling-text",
    )
    doc = ParsedDoc(
        doc_name="q3_2024.pdf",
        doc_id="abc123",
        elements=[elem],
        page_count=1,
    )
    assert doc.doc_name == "q3_2024.pdf"
    assert len(doc.elements) == 1
    assert doc.elements[0].content_type == ContentType.TEXT


def test_parsed_element_table_type() -> None:
    """A table element has the correct content_type and source_modality."""
    elem = ParsedElement(
        text="| Revenue | Q3 |\n|---|---|\n| 4.2B | 2024 |",
        page_number=2,
        section="Segment Results",
        content_type=ContentType.TABLE,
        source_modality="docling-table",
    )
    assert elem.content_type == ContentType.TABLE
    assert elem.source_modality == "docling-table"
    assert elem.page_number == 2


def test_parse_pdf_raises_parse_error_for_missing_file() -> None:
    """parse_pdf must raise ParseError (not FileNotFoundError) for absent files."""
    with pytest.raises(ParseError, match="File not found"):
        parse_pdf("/tmp/this_file_definitely_does_not_exist_finrag.pdf")


def test_parse_pdf_raises_parse_error_when_docling_missing(tmp_path: Path) -> None:
    """If Docling is not installed, parse_pdf raises ParseError with a clear message."""
    dummy_pdf = tmp_path / "dummy.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 fake content")

    with patch.dict("sys.modules", {"docling": None, "docling.document_converter": None}):
        with pytest.raises((ParseError, ImportError)):
            parse_pdf(dummy_pdf)


def test_parse_pdf_structured_error_on_converter_failure(tmp_path: Path) -> None:
    """parse_pdf must raise ParseError (not bare RuntimeError) when Docling fails.

    We inject a fake Docling whose DocumentConverter.convert() raises RuntimeError.
    parse_pdf must catch it and re-raise as ParseError.
    """
    dummy_pdf = tmp_path / "bad.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 intentionally bad content")

    # Build a minimal fake Docling module tree
    mock_converter_instance = MagicMock()
    mock_converter_instance.convert.side_effect = RuntimeError("corrupt PDF")
    mock_converter_cls = MagicMock(return_value=mock_converter_instance)

    mock_input_fmt = MagicMock()
    mock_input_fmt.PDF = "PDF"

    fake_modules = {
        "docling": MagicMock(),
        "docling.document_converter": MagicMock(
            DocumentConverter=mock_converter_cls,
            PdfFormatOption=MagicMock(),
        ),
        "docling.datamodel": MagicMock(),
        "docling.datamodel.base_models": MagicMock(InputFormat=mock_input_fmt),
        "docling.datamodel.pipeline_options": MagicMock(PdfPipelineOptions=MagicMock()),
    }

    with patch.dict("sys.modules", fake_modules):
        with pytest.raises(ParseError, match="corrupt PDF"):
            parse_pdf(dummy_pdf)


# ---------------------------------------------------------------------------
# Slow tests — require Docling installed, skipped in CI by default
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_parse_pdf_live_text_extraction(tiny_pdf: Path) -> None:
    """Live Docling parse: must extract text from the test PDF."""
    doc = parse_pdf(tiny_pdf)
    assert doc.page_count >= 1
    text_elements = [e for e in doc.elements if e.content_type == ContentType.TEXT]
    assert text_elements, "Expected at least one text element"
    combined = " ".join(e.text for e in text_elements).lower()
    assert "revenue" in combined or "q3" in combined or "financial" in combined


@pytest.mark.slow
def test_parse_pdf_live_table_detection(tiny_pdf: Path) -> None:
    """Live Docling parse: must detect the table in the test PDF."""
    doc = parse_pdf(tiny_pdf)
    table_elements = [e for e in doc.elements if e.content_type == ContentType.TABLE]
    assert table_elements, "Expected at least one table element"
    # The table should contain the column headers
    table_text = " ".join(e.text for e in table_elements)
    assert "Segment" in table_text or "|" in table_text


@pytest.mark.slow
def test_parse_pdf_live_page_numbers_populated(tiny_pdf: Path) -> None:
    """Live Docling parse: all elements must have a valid page_number >= 0."""
    doc = parse_pdf(tiny_pdf)
    for elem in doc.elements:
        assert elem.page_number >= 0


@pytest.mark.slow
def test_parse_pdf_live_doc_name_preserved(tiny_pdf: Path) -> None:
    """Live Docling parse: doc_name must match the file's basename."""
    doc = parse_pdf(tiny_pdf)
    assert doc.doc_name == tiny_pdf.name
