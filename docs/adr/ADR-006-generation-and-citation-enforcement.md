# ADR-006 — Generation and Citation Enforcement

**Status:** Accepted  
**Date:** 2026-06-12  
**Deciders:** FinRAG build agent  
**Context:** Phase 1 slice 5 — LLM NIM integration + grounded, cited answers

---

## Context

Phase 1 slice 4 produced `document_search` — a ranked list of retrieved chunks.
Slice 5 completes the Phase 1 loop: the ranked chunks must become a grounded,
cited answer via the LLM NIM.  The answer must be:

1. **Grounded** — every factual claim must come from the retrieved context, not
   the model's parametric memory.
2. **Cited** — every claim must reference a specific source (doc_name +
   page_number) so a user can verify it.
3. **Enforceable** — hallucinated citations (references to chunks the model was
   never given) must be rejected, not silently included.

---

## Decision

### LLM endpoint

NVIDIA NIM exposes an OpenAI-compatible `chat/completions` endpoint at
`{NIM_LLM_BASE_URL}/chat/completions`.  We use this directly with `httpx`
(same pattern as `ingest/nim_client.py` and `retrieval/reranker.py`) rather
than pulling in the OpenAI SDK, keeping dependencies minimal and consistent.

The model is `meta/llama-3.1-8b-instruct` (configurable via `NIM_LLM_MODEL`).

### Temperature = 0.1

Financial document Q&A requires factual fidelity.  Low temperature keeps
generation near the mode of the distribution, reducing paraphrase drift and
invented numbers.  The grounding instruction in the system prompt provides the
primary constraint; temperature provides a second line of defense.

We chose 0.1 (not 0.0) to avoid pure greedy decoding, which can produce
repetitive or degenerate output on longer answers.

### Citation format: `[N]` numeric markers

Each retrieved chunk is labeled `[N]` (1-indexed) in the user prompt.  The
system prompt instructs the model to cite every claim using `[N]` notation.
Post-generation, a regex parses all `[N]` references from the answer text.

**Alternatives considered:**

| Format | Reason rejected |
|--------|-----------------|
| `[doc_name, p.X]` | LLMs paraphrase or truncate long filenames → fragile regex |
| Footnote references `¹` | Unicode char — LLMs reproduce inconsistently |
| Structured JSON output | Requires JSON mode / grammar sampling — not all NIM versions support it cleanly |

Numeric `[N]` markers are short, reliably reproduced by instruction-tuned
models, and trivially parsed.

### Grounding instruction in the system prompt

The grounding rule ("answer ONLY from the context") is placed in the system
message, not the user message.  Instruction-tuned models assign higher weight
to system-role instructions, reducing the chance the model treats the context
as optional supplementary material.

### Post-generation citation enforcement

We cannot enforce citation behavior before generation.  Post-generation, we:

1. Parse `[N]` references with `re.compile(r'\[(\d+)\]')`.
2. Map each valid N (1-based) to `chunks[N-1]`.
3. **Reject** hallucinated indices (N out of range): including a citation
   pointing to a non-existent source is more misleading than omitting it.
4. **Warn** (structlog) if the model produced a positive answer with zero
   citations — this signals the model answered from parametric memory.
5. **Do not warn** if the answer is a refusal
   ("I cannot answer this question from the provided documents.") with no
   citations — that is correct behavior.

This is pragmatic enforcement, not perfect constraint.  A grounded model on
low temperature with explicit system-level instructions passes the citation
check on well-formed context in practice.  Adversarial tests and eval (Phase 4
RAGAS faithfulness) will surface systematic failures.

### RBAC filter threading

`answer_query` accepts `filter_expr: str | None = None` and passes it
unchanged to `document_search`, which passes it to the Milvus ANN search.
This preserves the Phase 1 invariant: forbidden chunks are excluded at the
vector-store boundary, not filtered post-retrieval.  Phase 2 injects:

```
'org_id == "{org_id}" AND ARRAY_CONTAINS(allowed_roles, "{role}")'
```

at the `answer_query` call site.  `generation/` code never constructs or
inspects the filter expression.

---

## Consequences

- **Positive:** Slice 5 completes the Phase 1 loop.  `answer_query` is the
  single entry point a caller needs: pass a query + store + BM25 index → get
  `AnswerWithCitations`.
- **Positive:** Citation enforcement catches the most dangerous failure mode
  (hallucinated sources) and surfaces uncited positive answers as observable
  warnings.
- **Negative / future work:** Citation parsing relies on the model following
  `[N]` instructions faithfully.  A model that rephrases to `(1)` or `¹` will
  produce zero citations.  Phase 4 evaluation (RAGAS faithfulness) will measure
  this in aggregate.
- **Future work:** If grounding rates are unsatisfactory, add constrained
  generation (logit bias on `[N]` tokens) or structured output via NIM grammar
  sampling.
