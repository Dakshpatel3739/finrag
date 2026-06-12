"""
generation.citations — citation enforcement and AnswerWithCitations model.

After the LLM generates an answer, this module:
  1. Parses [N] citation references from the answer text.
  2. Maps each valid N back to the corresponding retrieved chunk.
  3. Rejects hallucinated indices (N out of range for the chunks list).
  4. Emits a structured-log warning if the answer has NO citations — the
     model may have answered from its parametric memory instead of the
     retrieved context.

WHY enforce citations post-generation (not pre-generation):
    Pre-generation filtering is impossible for text output.  Post-generation
    enforcement catches the two failure modes we care about:
      a) Hallucinated citations — indices that point to chunks the model was
         never given (N > len(chunks) or N < 1).  These are silently dropped
         rather than included, because the model fabricated a source reference.
      b) No citations at all — the model answered without grounding.  We
         surface this as a warning so the caller can decide whether to surface
         a confidence flag to the end user.
    The instruction in the system prompt handles the happy path; enforcement
    here handles the failure paths.

WHY reject hallucinated indices (not just warn):
    Including a citation that doesn't map to a real retrieved chunk would
    mislead users into thinking there's a verifiable source for a claim that
    isn't actually in the retrieved context.  Silent inclusion is worse than
    silent omission.

Public API
----------
    CitationSource  — pydantic model for a single citation.
    AnswerWithCitations — pydantic model for the full generation result.
    parse_citations(answer, chunks) -> AnswerWithCitations
"""

from __future__ import annotations

import re

import structlog
from pydantic import BaseModel

from ingest.models import Chunk

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# WHY [N] not inline footnote: numeric markers are short, reliably reproduced
# by instruction-tuned models, and trivially parsed.  See prompt.py docstring.
_CITATION_RE = re.compile(r"\[(\d+)\]")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CitationSource(BaseModel):
    """A single verified citation source drawn from the retrieved chunks."""

    doc_name: str
    page_number: int
    chunk_id: str


class AnswerWithCitations(BaseModel):
    """The complete output of a RAG generation call.

    ``sources`` contains only citations that were:
      - referenced in the answer text as [N], AND
      - map to a real retrieved chunk (N is in-range).

    Hallucinated indices (N > number of retrieved chunks) are excluded.
    If ``sources`` is empty and the answer is not an "I cannot answer" reply,
    parse_citations will have emitted a grounding warning via structlog.
    """

    answer: str
    sources: list[CitationSource]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Phrase the model is instructed to use when context is insufficient.
_NO_ANSWER_PHRASE = "I cannot answer this question from the provided documents"


def parse_citations(answer: str, chunks: list[Chunk]) -> AnswerWithCitations:
    """Parse [N] citations from the answer and map them to retrieved chunks.

    WHY hallucinated indices are dropped (not flagged inline):
        Returning a citation pointing to a non-existent source would be more
        misleading to an end-user than omitting it.  The rejection is logged
        so operators can monitor hallucination rates without exposing the
        implementation detail to callers.

    WHY the no-citation path is a warning, not an error:
        The model may legitimately respond "I cannot answer …" with no
        citations.  That is correct behaviour.  We only warn on uncited
        *positive* answers, which indicate the model answered from parametric
        memory rather than the provided context.

    Args:
        answer: Raw text produced by the LLM.
        chunks: The retrieved chunks that were included in the RAG prompt,
                in the same order as they appeared (1-indexed in the prompt).

    Returns:
        AnswerWithCitations with deduplicated, in-range sources only.
    """
    raw_indices = [int(m) for m in _CITATION_RE.findall(answer)]

    seen: set[str] = set()
    sources: list[CitationSource] = []
    hallucinated_count = 0

    for idx in raw_indices:
        # [N] is 1-based in the prompt; convert to 0-based chunk index.
        chunk_index = idx - 1
        if chunk_index < 0 or chunk_index >= len(chunks):
            # WHY reject: the model cited a source number that doesn't exist
            # in the retrieved set — this is a hallucinated citation.
            hallucinated_count += 1
            logger.warning(
                "citations.hallucinated_index",
                cited_n=idx,
                chunks_available=len(chunks),
            )
            continue

        chunk = chunks[chunk_index]
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        sources.append(
            CitationSource(
                doc_name=chunk.doc_name,
                page_number=chunk.page_number,
                chunk_id=chunk.chunk_id,
            )
        )

    if hallucinated_count > 0:
        logger.warning(
            "citations.hallucination_summary",
            hallucinated_count=hallucinated_count,
            valid_citations=len(sources),
        )

    # Warn if the model produced a positive answer with no grounding citations.
    # (Silence is correct if the model said "I cannot answer …".)
    is_refusal = _NO_ANSWER_PHRASE.lower() in answer.lower()
    if not sources and not is_refusal:
        logger.warning(
            "citations.no_grounding",
            answer_preview=answer[:120],
            msg="Model produced an answer without citing any retrieved chunks.",
        )

    return AnswerWithCitations(answer=answer, sources=sources)
