"""
ingest test fixtures.

Provides a tiny synthetic PDF (1 page, heading + paragraph + table) built
with fpdf2 so tests can run without any external files.  This fixture is used
by test_parser.py (slow/live Docling test) and test_chunker.py (fast unit
tests against a hand-crafted ParsedDoc).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ingest.parser import ParsedDoc


@pytest.fixture(scope="session")
def tiny_pdf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a 1-page PDF with a heading, a paragraph, and a 3-column table.

    Uses fpdf2 (lightweight, no ML deps) so this fixture always runs fast.
    The PDF is created once per test session and reused.

    Returns:
        Path to the generated PDF file.
    """
    from fpdf import FPDF

    tmp = tmp_path_factory.mktemp("fixtures")
    pdf_path = tmp / "test_financial.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, "Q3 2024 Financial Summary")
    pdf.ln()

    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(
        0,
        7,
        (
            "Revenue for Q3 2024 increased by 12% year-over-year to $4.2 billion, "
            "driven primarily by strong performance in the cloud services segment. "
            "Operating income reached $1.1 billion, representing a margin of 26.2%. "
            "Free cash flow was $890 million, up 18% from Q3 2023."
        ),
    )

    pdf.ln(4)
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(0, 8, "Segment Revenue ($ millions)")
    pdf.ln()

    pdf.set_font("Helvetica", size=10)
    col_w = [60.0, 40.0, 40.0]
    headers = ["Segment", "Q3 2024", "Q3 2023"]
    rows = [
        ["Cloud Services", "1,820", "1,540"],
        ["Enterprise Software", "1,380", "1,250"],
        ["Professional Services", "1,000", "960"],
    ]

    # Header row
    for header, w in zip(headers, col_w, strict=True):
        pdf.cell(w, 8, header, border=1)
    pdf.ln()

    # Data rows
    for row in rows:
        for cell, w in zip(row, col_w, strict=True):
            pdf.cell(w, 7, cell, border=1)
        pdf.ln()

    pdf.output(str(pdf_path))
    return pdf_path


@pytest.fixture(scope="session")
def tiny_parsed_doc() -> ParsedDoc:
    """A hand-crafted ParsedDoc that mirrors what parse_pdf() would return.

    Used in fast unit tests that don't need Docling to actually run.
    """
    from ingest.models import ContentType
    from ingest.parser import ParsedDoc, ParsedElement

    return ParsedDoc(
        doc_name="test_financial.pdf",
        doc_id="abc123",
        page_count=1,
        elements=[
            ParsedElement(
                text=(
                    "Revenue for Q3 2024 increased by 12% year-over-year to $4.2 billion, "
                    "driven primarily by strong performance in the cloud services segment. "
                    "Operating income reached $1.1 billion, representing a margin of 26.2%."
                ),
                page_number=0,
                section="Q3 2024 Financial Summary",
                content_type=ContentType.TEXT,
                source_modality="docling-text",
            ),
            ParsedElement(
                text=(
                    "| Segment | Q3 2024 | Q3 2023 |\n|---|---|---|\n"
                    "| Cloud Services | 1,820 | 1,540 |"
                ),
                page_number=0,
                section="Segment Revenue",
                content_type=ContentType.TABLE,
                source_modality="docling-table",
            ),
        ],
    )
