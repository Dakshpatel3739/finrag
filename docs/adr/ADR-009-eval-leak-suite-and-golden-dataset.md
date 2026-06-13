# ADR-009 — Eval Phase 4a: Automated RBAC Leak Suite and Golden QA Dataset

**Date:** 2026-06-13
**Status:** Accepted
**Slice:** Phase 4a (feat/phase4a-leak-suite-golden-dataset)

---

## Context

Phases 0–3 delivered the full RAG pipeline with JWT auth, multi-tenancy, and
chunk-level RBAC enforced at Milvus query time.  Phase 4 introduces evaluation
infrastructure.  This ADR covers Phase 4a specifically.

The evaluation problem splits into two concerns with different CI/cost profiles:

1. **Security testing** — does the RBAC filter correctly block forbidden chunks?
   This is purely structural: we test the filter expression, not the quality of
   answers.  It requires no LLM judge, no network, and no API key.

2. **Quality evaluation (RAGAS)** — are retrieved contexts relevant?  Are answers
   faithful to them?  These metrics require an LLM judge (faithfulness,
   answer relevance) or expensive retrieval runs against a real NIM endpoint.

We deliver concern #1 in Phase 4a and deliberately defer concern #2 to Phase 4b.

---

## Decision 1 — Leak Suite is CI-safe and deterministic (no NIM calls)

**Approach:** The RBAC leak suite in `eval/leak_suite/` uses:
- **Real Milvus Lite** (in-process, no server): the actual `ARRAY_CONTAINS`
  filter runs at the C++ storage layer.  We are testing the production filter
  path, not a mock.
- **Deterministic fake embeddings**: every chunk and every query uses the same
  unit vector `[1.0, 0.0, …, 0.0]` (dim=8).  Cosine similarity is 1.0 for
  every chunk/query pair, so the Milvus ARRAY_CONTAINS filter is the ONLY thing
  that differentiates results.  This eliminates non-determinism from vector
  ordering and makes the test corpus reproducible across machines and CI runs.
- **Mocked NIM calls** (`embed_texts`, `rerank`, `generate`): these are
  patched with `unittest.mock.AsyncMock` via context managers.  No network
  calls, no API key, no `@pytest.mark.slow`.

**Why this is correct** (not a shortcut):
The security invariant is: *forbidden chunks must never enter the LLM context*.
The mechanism is the Milvus boolean filter expression.  Mocking the NIM calls
does NOT mock the filter — the filter runs inside `store.dense_search()` which
calls Milvus Lite's real C++ query engine.  Testing with fake embeddings and
real Milvus is a stronger security test than testing with real embeddings and a
mocked Milvus, because the latter would test the model quality, not the filter.

**Adversarial cases covered (all CI-blocking):**
1. Positive: OWNER and FINANCE retrieve restricted chunks.
2. Positive: All roles retrieve public/internal chunks.
3. Negative: HR and EMPLOYEE retrieve zero restricted chunks.
4. BM25 side-channel: lexical-overlap queries (words from restricted chunk text)
   for unauthorized roles still return zero restricted chunks.  This re-covers
   the Phase 2 BM25 side-channel finding.
5. Cross-tenant: acme users retrieve zero globex chunks (and vice versa).
6. Defense-in-depth: an "inconsistent" chunk (sensitivity_level=public but
   allowed_roles=["owner","finance"]) is blocked for hr/employee — the stricter
   allowed_roles field wins.
7. Empty-result safety: unauthorized query returning [] goes to the grounded
   fallback path; `generate` is never called; restricted text never appears in
   the answer.
8. Filter-bypass: 7 prompt-injection query phrasings for acme/HR return zero
   restricted and zero cross-tenant chunks.
9. LLM context-window proof: `build_rag_prompt` is wrapped to capture which
   chunks were assembled into the LLM context; restricted chunk_ids are absent.
10. Exhaustive role × restricted matrix: all 4 roles × restricted chunks
    checked in one parametrised test.

---

## Decision 2 — RAGAS deferred to Phase 4b

**RAGAS** (Retrieval Augmented Generation Assessment) computes:
- **Faithfulness** — is the answer supported by the retrieved contexts?
- **Answer Relevance** — does the answer address the question?
- **Context Precision/Recall** — did retrieval surface the right chunks?

RAGAS requires an LLM judge for faithfulness and answer relevance.  An LLM
judge means live NIM calls, which means:
- `@pytest.mark.slow` (CI excludes it)
- Requires `NIM_API_KEY` in the environment
- Non-deterministic (LLM outputs vary across runs and model versions)
- Expensive (API credits per eval run)

For these reasons, RAGAS is structurally incompatible with CI-blocking tests.
Phase 4b will run RAGAS as a separate job gated by `[not slow]` exclusion,
with a dedicated CI step that requires the API key secret.

**We do NOT add the RAGAS dependency in Phase 4a.**  Adding it would pull in
a large dependency tree (pandas, datasets, langchain, etc.) and slow `pip
install` in CI without any benefit until Phase 4b is implemented.

---

## Decision 3 — Golden QA Dataset Schema and "Don't Fabricate" Rule

### Schema (`eval/models.py — GoldenQA`)

```
id                  str         unique identifier
question            str         natural-language question (min 10 chars)
ground_truth_answer str         expected correct answer text
ground_truth_contexts list[str] verbatim/near-verbatim source snippets
doc_name            str         source document filename
page_number         int         0-indexed source page
required_role       str         minimum role that should retrieve the answer
sensitivity_level   Literal     "public" | "internal" | "restricted"
tags                list[str]   freeform labels
```

**Why pydantic v2 (not raw dicts):** Validation happens at load time via
`eval.loader.load_golden_qa()`.  A bad row raises `EvalDatasetError` with the
1-indexed line number.  Downstream RAGAS code can rely on field presence and
types without defensive None-checks.

### The "Don't Fabricate" Rule

Ground-truth accuracy is the entire point of a golden dataset.  A wrong
ground truth produces misleading evaluation metrics that INCREASE confidence
in a broken system.

**Rule: never invent precise financial figures without verification.**

The only verified fact in the FY2024 NVIDIA 10-K golden dataset is:
> Total revenue for fiscal year 2024 was **$26.97 billion**.
> Source: Phase 1 live NIM test (`live_nvidia_10k.pdf`, chunk_id=e2c75bfcaf97769d).

All other quantitative claims in `golden_qa.jsonl` are tagged
`"needs-verification"` and use cautious phrasing ("approximately", "including
equity awards" rather than specific dollar amounts in the answer text).

Restricted-sensitivity rows (CEO/NEO compensation) describe the structure of
the compensation table rather than specific figures, because compensation data
varies and was not extracted in a prior live test.

**For Phase 4b:** before running RAGAS, all `needs-verification` rows should be
spot-checked against the actual 10-K PDF.  Rows that cannot be verified should
be removed or corrected before they produce false RAGAS signals.

---

## Consequences

- The leak suite runs in `pytest -m "not slow"` with no network and no `.env`.
  All leak tests are CI-blocking.
- RAGAS is NOT a dependency yet.  `pip install -e ".[dev]"` does not change.
- The golden dataset is usable immediately for structural assertions (Phase 4a)
  and will feed RAGAS in Phase 4b once `needs-verification` rows are audited.
- The leak suite SUPERSETS rbac/test_adversarial_leaks.py — both suites run.

---

## Alternatives Considered

**Combine leak suite and RAGAS in one phase:**
Rejected.  RAGAS requires an LLM judge (live NIM) which is incompatible with
CI-safe test requirements.  The security test is the highest-priority deliverable
and must not be blocked on the evaluation harness.

**Use the same Milvus collection as rbac/conftest.py:**
Rejected.  The eval corpus needs more chunks (multiple per sensitivity level,
inconsistent chunk, two org chunks for globex) for parametrised coverage.
Reusing the Phase 2 fixture would require modifying it, risking regressions.
A separate corpus in eval/leak_suite/seeder.py has single responsibility.

**Run leak tests marked @pytest.mark.slow:**
Rejected.  The value of the leak suite is precisely that it is CI-blocking.
A security test that is excluded from CI is a security test that will not be
run consistently, which defeats the purpose of having it.
