"""
ingest.parser — Docling-based PDF parser.

Wraps Docling's DocumentConverter to produce a ParsedDoc: a structured
representation of all text elements and tables per page, ready for the
chunker.

Why Docling?
  Docling preserves table structure as Markdown, which embeds well and
  renders legibly in citations.  Alternative libraries (pypdf, pdfminer)
  flatten tables to whitespace-separated strings, losing the structure that
  carries meaning in financial filings (income statements, segment tables).
  Recorded in ADR-001.

Slow-test note:
  The live parse_pdf() function imports Docling, which downloads ML models on
  first run and can take 30-60 s.  Tests that call it directly are tagged
  @pytest.mark.slow and excluded from the default pytest run.  Fast tests use
  the ParsedDoc/ParsedElement dataclasses directly (no Docling import needed).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from ingest.errors import ParseError
from ingest.models import ContentType

if TYPE_CHECKING:
    pass  # avoid heavy Docling import at module level for non-slow tests

logger: structlog.BoundLogger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Data classes produced by the parser
# ---------------------------------------------------------------------------


@dataclass
class ParsedElement:
    """A single parsed element (paragraph or table) from a document page.

    Attributes:
        text:         Raw text or Markdown-formatted table.
        page_number:  0-indexed source page.
        section:      Nearest heading above this element, or empty string.
        content_type: Whether this is flowing text or a Markdown table.
        source_modality: Extraction method tag for provenance.
    """

    text: str
    page_number: int
    section: str
    content_type: ContentType
    source_modality: str


@dataclass
class ParsedDoc:
    """The full parsed representation of a single PDF document.

    Attributes:
        doc_name:  Original filename (basename).
        doc_id:    Stable hash of doc_name (see models.make_doc_id).
        elements:  Ordered list of all parsed elements across all pages.
        page_count: Total number of pages in the source PDF.
    """

    doc_name: str
    doc_id: str
    elements: list[ParsedElement] = field(default_factory=list)
    page_count: int = 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_pdf(path: str | Path) -> ParsedDoc:
    """Parse a PDF file with Docling and return a structured ParsedDoc.

    Extracts text paragraphs and tables (as Markdown) per page.  Tables are
    tagged with ``content_type=ContentType.TABLE`` so the chunker can treat
    them as atomic units (WHY: splitting a Markdown table mid-row breaks
    the structure and produces unembeddable fragments).

    Args:
        path: Filesystem path to the PDF file.

    Returns:
        A ParsedDoc containing all extracted elements in page order.

    Raises:
        ParseError: If Docling cannot open or process the file.  The error
                    is also logged with structured context before being raised
                    (never silently swallowed).
    """
    path = Path(path)

    # Check file existence first — before any heavy import — so the error
    # message is always clear even when Docling is not installed.
    if not path.exists():
        log = logger.bind(path=str(path))
        log.error("ingest.parse_pdf.file_not_found")
        raise ParseError(str(path), "File not found")

    # Import Docling here (not at module level) so tests that don't need a
    # live parse can import ingest.parser without triggering model downloads.
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
    except ImportError as exc:
        raise ParseError(str(path), f"Docling is not installed: {exc}") from exc

    log = logger.bind(doc_name=path.name, path=str(path))
    log.info("ingest.parse_pdf.start")

    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False  # skip OCR for speed; enable for scanned docs

        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
        result = converter.convert(str(path))
        doc = result.document
    except Exception as exc:
        log.error("ingest.parse_pdf.failed", error=str(exc))
        raise ParseError(str(path), str(exc)) from exc

    from ingest.models import make_doc_id

    parsed = ParsedDoc(
        doc_name=path.name,
        doc_id=make_doc_id(path.name),
        page_count=0,
    )

    current_section = ""
    max_page = 0

    # Docling's document model exposes items() which yields (label, element) pairs.
    # We iterate in document order so page numbers and sections stay coherent.
    for item, _level in doc.iterate_items():
        item_type = type(item).__name__

        # Track section headings for all subsequent elements
        if item_type in ("SectionHeaderItem", "TitleItem"):
            current_section = item.text if hasattr(item, "text") else ""
            continue

        # Page provenance — Docling items carry a prov list
        page_no: int = 0
        if hasattr(item, "prov") and item.prov:
            page_no = max(0, item.prov[0].page_no - 1)  # convert 1-indexed → 0-indexed
        max_page = max(max_page, page_no)

        if item_type == "TableItem":
            # Export table as Markdown — preserves row/column structure
            try:
                md_table = item.export_to_markdown()
            except Exception:
                md_table = item.text if hasattr(item, "text") else "[table]"

            if md_table.strip():
                parsed.elements.append(
                    ParsedElement(
                        text=md_table,
                        page_number=page_no,
                        section=current_section,
                        content_type=ContentType.TABLE,
                        source_modality="docling-table",
                    )
                )

        elif item_type == "TextItem" and hasattr(item, "text"):
            text = item.text.strip()
            if text:
                parsed.elements.append(
                    ParsedElement(
                        text=text,
                        page_number=page_no,
                        section=current_section,
                        content_type=ContentType.TEXT,
                        source_modality="docling-text",
                    )
                )

    parsed.page_count = max_page + 1 if parsed.elements else 0

    log.info(
        "ingest.parse_pdf.done",
        page_count=parsed.page_count,
        element_count=len(parsed.elements),
        table_count=sum(1 for e in parsed.elements if e.content_type == ContentType.TABLE),
    )
    return parsed


# ---------------------------------------------------------------------------
# Logging configuration helper (called once at app startup)
# ---------------------------------------------------------------------------


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog for the ingest pipeline.

    Args:
        level: Python logging level name (e.g. "DEBUG", "INFO").
    """
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
