"""
Tests for generation.citations — parse_citations + AnswerWithCitations.

Verifies that:
  - Valid [N] references map to the correct (doc_name, page_number, chunk_id).
  - Hallucinated indices (N > len(chunks) or N < 1) are silently rejected.
  - An answer with no [N] references triggers a grounding warning.
  - Duplicate [N] references produce a single citation source.
  - AnswerWithCitations validates correctly via pydantic v2.
  - A refusal answer ("I cannot answer …") with no citations does NOT warn.
"""

from __future__ import annotations

from structlog.testing import capture_logs

from generation.citations import AnswerWithCitations, CitationSource, parse_citations
from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(idx: int, doc_name: str = "test.pdf", page: int = 0) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id("doc_cite_test", page, idx),
        doc_id="doc_cite_test",
        doc_name=doc_name,
        page_number=page,
        section="Finance",
        text=f"Chunk text {idx}.",
        content_type=ContentType.TEXT,
        sensitivity_level=SensitivityLevel.INTERNAL,
    )


# ---------------------------------------------------------------------------
# AnswerWithCitations pydantic model
# ---------------------------------------------------------------------------


def test_answer_with_citations_constructs() -> None:
    """AnswerWithCitations must construct from valid data."""
    src = CitationSource(doc_name="a.pdf", page_number=3, chunk_id="abc123")
    result = AnswerWithCitations(answer="Revenue was $1B [1].", sources=[src])
    assert result.answer == "Revenue was $1B [1]."
    assert len(result.sources) == 1
    assert result.sources[0].doc_name == "a.pdf"
    assert result.sources[0].page_number == 3


def test_answer_with_citations_empty_sources() -> None:
    """AnswerWithCitations must accept an empty sources list."""
    result = AnswerWithCitations(answer="no answer", sources=[])
    assert result.sources == []


def test_citation_source_constructs() -> None:
    """CitationSource must expose doc_name, page_number, chunk_id."""
    src = CitationSource(doc_name="nvidia.pdf", page_number=42, chunk_id="xyz")
    assert src.doc_name == "nvidia.pdf"
    assert src.page_number == 42
    assert src.chunk_id == "xyz"


# ---------------------------------------------------------------------------
# parse_citations — happy path
# ---------------------------------------------------------------------------


def test_valid_citation_maps_to_chunk() -> None:
    """[1] in the answer must map to chunks[0]."""
    chunk = _make_chunk(0, doc_name="nvidia_10k.pdf", page=5)
    result = parse_citations("Revenue grew [1].", [chunk])
    assert len(result.sources) == 1
    assert result.sources[0].doc_name == "nvidia_10k.pdf"
    assert result.sources[0].page_number == 5
    assert result.sources[0].chunk_id == chunk.chunk_id


def test_multiple_valid_citations() -> None:
    """[1] and [2] in the answer map to chunks[0] and chunks[1]."""
    c1 = _make_chunk(0, doc_name="doc_a.pdf", page=1)
    c2 = _make_chunk(1, doc_name="doc_b.pdf", page=2)
    result = parse_citations("Claim one [1]. Claim two [2].", [c1, c2])
    assert len(result.sources) == 2
    ids = {s.chunk_id for s in result.sources}
    assert c1.chunk_id in ids
    assert c2.chunk_id in ids


def test_answer_text_preserved() -> None:
    """parse_citations must not modify the answer text."""
    chunk = _make_chunk(0)
    answer = "Revenue was $5B [1]. Operating income rose 20% [1]."
    result = parse_citations(answer, [chunk])
    assert result.answer == answer


# ---------------------------------------------------------------------------
# parse_citations — hallucinated / out-of-range indices
# ---------------------------------------------------------------------------


def test_hallucinated_index_is_rejected() -> None:
    """[3] when only 2 chunks exist must not appear in sources."""
    chunks = [_make_chunk(0), _make_chunk(1)]
    result = parse_citations("Claim [3].", chunks)
    assert len(result.sources) == 0


def test_zero_index_is_rejected() -> None:
    """[0] is not a valid 1-based citation; must be rejected."""
    chunk = _make_chunk(0)
    result = parse_citations("Claim [0].", [chunk])
    # [0] maps to chunk_index = -1 which is out of range
    assert len(result.sources) == 0


def test_hallucinated_and_valid_mix() -> None:
    """Valid citations survive even if hallucinated ones are present."""
    chunk = _make_chunk(0, doc_name="real.pdf", page=7)
    result = parse_citations("Good [1]. Bad [99].", [chunk])
    assert len(result.sources) == 1
    assert result.sources[0].doc_name == "real.pdf"


# ---------------------------------------------------------------------------
# parse_citations — deduplication
# ---------------------------------------------------------------------------


def test_duplicate_citation_deduped() -> None:
    """Repeated [1] references must produce only one CitationSource."""
    chunk = _make_chunk(0)
    result = parse_citations("Claim [1]. Another claim [1]. More [1].", [chunk])
    assert len(result.sources) == 1


# ---------------------------------------------------------------------------
# parse_citations — grounding warnings
# ---------------------------------------------------------------------------


def test_no_citation_answer_triggers_warning() -> None:
    """An answer with no [N] references and no refusal phrase must log a warning."""
    chunk = _make_chunk(0)
    with capture_logs() as captured:
        result = parse_citations("Revenue was large.", [chunk])
    assert result.sources == []
    event_names = [e["event"] for e in captured]
    assert any("grounding" in name or "no_grounding" in name for name in event_names)


def test_refusal_answer_no_warning() -> None:
    """'I cannot answer …' with no citations must NOT trigger a grounding warning."""
    chunk = _make_chunk(0)
    with capture_logs() as captured:
        result = parse_citations(
            "I cannot answer this question from the provided documents.", [chunk]
        )
    assert result.sources == []
    event_names = [e["event"] for e in captured]
    assert not any("no_grounding" in name for name in event_names)


def test_hallucinated_citation_triggers_warning() -> None:
    """An out-of-range [N] must log a hallucination warning."""
    chunks = [_make_chunk(0)]
    with capture_logs() as captured:
        parse_citations("Claim [99].", chunks)
    event_names = [e["event"] for e in captured]
    assert any("hallucinated" in name for name in event_names)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_chunks_with_citation_produces_no_sources() -> None:
    """[1] when chunks list is empty → rejected, no sources."""
    result = parse_citations("Claim [1].", [])
    assert result.sources == []


def test_answer_with_no_brackets_no_warning_refusal() -> None:
    """Refusal answer (no [N]) must return empty sources without grounding warning."""
    result = parse_citations("I cannot answer this question from the provided documents.", [])
    assert result.sources == []
