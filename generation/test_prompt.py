"""
Tests for generation.prompt — build_rag_prompt.

Verifies that:
  - Each chunk's doc_name and page_number appear in the user prompt.
  - The query string is included in the user prompt.
  - Citation number labels [1], [2], … are present for each chunk.
  - The system prompt contains grounding + citation instructions.
  - An empty chunks list produces a prompt with no context passages.
"""

from __future__ import annotations

from generation.prompt import _SYSTEM_PROMPT, build_rag_prompt
from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(idx: int, text: str, doc_name: str = "test.pdf", page: int = 0) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id("doc_prompt_test", page, idx),
        doc_id="doc_prompt_test",
        doc_name=doc_name,
        page_number=page,
        section="Overview",
        text=text,
        content_type=ContentType.TEXT,
        sensitivity_level=SensitivityLevel.INTERNAL,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_query_present_in_user_prompt() -> None:
    """The user's question must appear in the user prompt."""
    chunks = [_make_chunk(0, "Revenue was $1B.")]
    _, user_prompt = build_rag_prompt("What was revenue?", chunks)
    assert "What was revenue?" in user_prompt


def test_each_chunk_labeled_with_citation_number() -> None:
    """Each chunk must be preceded by a [N] citation label in the user prompt."""
    chunks = [
        _make_chunk(0, "Chunk A text."),
        _make_chunk(1, "Chunk B text."),
        _make_chunk(2, "Chunk C text."),
    ]
    _, user_prompt = build_rag_prompt("query", chunks)
    assert "[1]" in user_prompt
    assert "[2]" in user_prompt
    assert "[3]" in user_prompt


def test_chunk_doc_name_in_user_prompt() -> None:
    """Each chunk's doc_name must appear in the user prompt."""
    chunks = [
        _make_chunk(0, "text A", doc_name="nvidia_10k_2024.pdf", page=3),
        _make_chunk(1, "text B", doc_name="apple_10k_2023.pdf", page=7),
    ]
    _, user_prompt = build_rag_prompt("query", chunks)
    assert "nvidia_10k_2024.pdf" in user_prompt
    assert "apple_10k_2023.pdf" in user_prompt


def test_chunk_page_number_in_user_prompt() -> None:
    """Each chunk's page_number must appear in the user prompt."""
    chunks = [
        _make_chunk(0, "text A", page=12),
        _make_chunk(1, "text B", page=99),
    ]
    _, user_prompt = build_rag_prompt("query", chunks)
    assert "12" in user_prompt
    assert "99" in user_prompt


def test_chunk_text_in_user_prompt() -> None:
    """Chunk text content must be present in the user prompt."""
    chunks = [_make_chunk(0, "Net income grew 42% year-over-year.")]
    _, user_prompt = build_rag_prompt("query", chunks)
    assert "Net income grew 42% year-over-year." in user_prompt


def test_system_prompt_contains_grounding_instruction() -> None:
    """System prompt must forbid answering outside provided context."""
    system, _ = build_rag_prompt("query", [])
    lower = system.lower()
    assert "only" in lower or "only using" in lower or "provided" in lower
    # Must tell model to say something specific if context is insufficient
    assert "cannot answer" in lower or "not contain" in lower or "insufficient" in lower


def test_system_prompt_contains_citation_instruction() -> None:
    """System prompt must instruct the model to cite every claim."""
    system, _ = build_rag_prompt("query", [])
    lower = system.lower()
    assert "cite" in lower or "citation" in lower or "[n]" in lower


def test_system_prompt_is_constant() -> None:
    """build_rag_prompt must return the module-level system prompt unchanged."""
    system, _ = build_rag_prompt("q", [])
    assert system == _SYSTEM_PROMPT


def test_empty_chunks_produces_empty_context_block() -> None:
    """With no chunks, the context block should be empty (no passage labels)."""
    _, user_prompt = build_rag_prompt("query", [])
    assert "[1]" not in user_prompt
    assert "=== CONTEXT PASSAGES ===" in user_prompt


def test_chunk_ordering_preserved() -> None:
    """Chunks must appear in the order passed (most relevant first = [1])."""
    chunks = [
        _make_chunk(0, "FIRST_CHUNK_TEXT"),
        _make_chunk(1, "SECOND_CHUNK_TEXT"),
    ]
    _, user_prompt = build_rag_prompt("query", chunks)
    pos1 = user_prompt.index("FIRST_CHUNK_TEXT")
    pos2 = user_prompt.index("SECOND_CHUNK_TEXT")
    assert pos1 < pos2, "Most relevant chunk must appear first in the context block"
    # [1] must precede [2]
    assert user_prompt.index("[1]") < user_prompt.index("[2]")


def test_multiple_chunks_all_labeled() -> None:
    """Five chunks must get labels [1] through [5]."""
    chunks = [_make_chunk(i, f"text {i}") for i in range(5)]
    _, user_prompt = build_rag_prompt("query", chunks)
    for n in range(1, 6):
        assert f"[{n}]" in user_prompt
