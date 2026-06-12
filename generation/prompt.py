"""
generation.prompt — RAG prompt builder for grounded, cited answers.

Assembles the system prompt and user prompt that are sent to the LLM NIM.
Every context chunk is labeled with a [N] citation marker so the model can
reference specific sources inline, and the user prompt includes both the
labeled context block and the query.

WHY citation markers are [N] (not [doc_name, p.X]):
    Numeric markers are concise, easy for the LLM to reproduce faithfully,
    and trivially parsed by a regex in citations.py.  The full doc_name +
    page_number mapping lives in the chunks list — citations.py recovers it
    by index.  Using the filename directly would risk the model paraphrasing
    or truncating long filenames, making post-processing fragile.

WHY the grounding instruction is in the system prompt (not user prompt):
    System-role instructions carry higher weight in instruction-tuned models
    than user-role instructions.  Placing the grounding rule here reduces the
    chance the model treats the context as optional supplementary material.

Public API
----------
    build_rag_prompt(query, chunks) -> tuple[str, str]
        Returns (system_prompt, user_prompt).
"""

from __future__ import annotations

from ingest.models import Chunk

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a financial document analysis assistant.

RULES (follow exactly):
1. Answer ONLY using information from the numbered context passages below.
2. Cite the source of every factual claim inline using [N] notation, where N is \
the passage number.
3. You MAY combine information from multiple passages; cite all that contribute \
to a claim (e.g. [1][3]).
4. If the context does not contain enough information to answer the question, \
say exactly: "I cannot answer this question from the provided documents."
5. Do NOT use any knowledge outside the provided context passages.
6. Do NOT fabricate numbers, names, or dates.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_rag_prompt(query: str, chunks: list[Chunk]) -> tuple[str, str]:
    """Assemble the system and user prompts for a RAG query.

    Each chunk is assigned a 1-based citation number [N].  The user prompt
    contains the numbered context block followed by the question so the model
    has full context before formulating its answer.

    WHY source label includes doc_name + page_number:
        Showing the human-readable source in the context block lets the model
        reproduce the reference accurately if it chooses to include it in
        prose.  The numeric [N] is the primary citation handle; the label is
        informational.

    Args:
        query:  The user's natural-language question.
        chunks: Retrieved and reranked chunks (most relevant first).

    Returns:
        A (system_prompt, user_prompt) tuple ready to pass to llm_client.generate.
    """
    context_lines: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        label = f"[{i}] Source: {chunk.doc_name}, page {chunk.page_number}"
        context_lines.append(f"{label}\n{chunk.text}")

    context_block = "\n\n".join(context_lines)

    user_prompt = (
        f"=== CONTEXT PASSAGES ===\n\n{context_block}\n\n=== END CONTEXT ===\n\nQuestion: {query}"
    )

    return _SYSTEM_PROMPT, user_prompt
