# ADR-002 — Chunking Strategy

**Status:** Accepted  
**Date:** 2026-06-12  
**Scope:** ingest/chunker.py

---

## Context

Financial PDFs contain two structurally distinct content types that require
different chunking treatment:

1. **Free text** — paragraphs, narrative sections, footnotes.  These benefit
   from overlap-aware splitting so a question that spans a chunk boundary still
   retrieves the relevant context.

2. **Tables** — income statements, segment breakdowns, KPI summaries.  These
   are structured data where every cell's meaning depends on its row and column
   header.  Splitting mid-row or mid-column produces malformed Markdown
   fragments that embed poorly (the embedding model sees a partial table with
   no headers) and cannot be rendered in citations.

---

## Decision

### Text: recursive character splitter (no LangChain)

Split text at progressively finer boundaries — `\n\n` (paragraphs) → `\n`
(lines) → `. ` (sentences) → ` ` (words) → hard character cut — until all
chunks are ≤ `chunk_size` characters.  Carry `chunk_overlap` characters from
the previous chunk into the next to preserve cross-boundary context.

Both `chunk_size` and `chunk_overlap` are read from the `system_config` runtime
DB (not hardcoded), so they can be tuned without a redeploy.

**Why not LangChain's `RecursiveCharacterTextSplitter`?**  
Adding LangChain as a dependency (~50 transitive packages) for a single utility
function is disproportionate.  The algorithm is well-understood and small
enough to own directly.  If we later need LangChain for something else, we can
switch.

### Tables: single atomic chunk (never split)

A table element produced by Docling is kept as **one chunk**, regardless of its
size.

**Why:** Splitting a Markdown table mid-row destroys the header-to-cell
relationship.  The embedding model and the reranker both see a fragment with no
column headers, making it unembeddable and unrenderable in citations.  A table
that is too large to embed in one API call will be handled by
truncation-with-warning in the embedding slice — a better failure mode than a
silently incorrect split.

### Docling for parsing (not pypdf / pdfminer)

Docling preserves table structure as Markdown (`| col1 | col2 |` rows) rather
than whitespace-separated strings.  For financial documents where tables carry
critical numerical data, this is the only option that makes the table content
embeddable and citable.  Recorded originally in ADR-001; restated here for
completeness.

---

## Consequences

- Tables may exceed the embedding NIM's token limit.  The embedding slice must
  detect and warn (or truncate to the model's max tokens) rather than crashing.
- `chunk_size` default of 512 characters is a starting point.  RAGAS evaluation
  in Phase 4 will reveal whether a larger size (e.g. 1024) improves context
  precision.  The runtime-config mechanism exists precisely for this tuning loop.
- The custom recursive splitter is ~80 lines of code.  If it develops edge-case
  bugs, consider switching to `langchain_text_splitters` (drop-in replacement
  with the same algorithm).
