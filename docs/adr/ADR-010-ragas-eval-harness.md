# ADR-010: RAGAS Evaluation Harness with NVIDIA NIM as Judge (Phase 4b)

**Status:** Accepted  
**Date:** 2026-06-13  
**Deciders:** FinRAG engineering

---

## Context

Phase 4a delivered the golden QA dataset (`golden_qa.jsonl`) and the RBAC leak
suite.  Phase 4b adds an automated retrieval/generation quality harness using
RAGAS (Retrieval-Augmented Generation Assessment Suite) to measure:

- **Faithfulness** — does the generated answer stay faithful to the retrieved context?
- **Answer Relevancy** — is the answer relevant to the question?
- **Context Precision** — are the retrieved chunks precise (not noisy)?
- **Context Recall** — does retrieval cover all the ground-truth supporting contexts?

Three architecture decisions arise:

1. Which RAGAS version to adopt and which metric API to use.
2. How to keep CI green when ragas is a heavy optional dependency.
3. How to wire NVIDIA NIM as the LLM/embedding judge instead of OpenAI.

---

## Decision 1: ragas==0.4.3 with `metrics.collections` API

We pin **ragas 0.4.3**.  The 0.4.x series introduced `ragas.metrics.collections`
as the preferred import path (the old `ragas.metrics` shim is deprecated and
will be removed in v1.0).

```python
from ragas.metrics.collections import (
    faithfulness, answer_relevancy, context_precision, context_recall
)
```

`SingleTurnSample` (0.4.x schema) maps directly to our GoldenQA fields:

| `SingleTurnSample` field | GoldenQA / harness source            |
|--------------------------|---------------------------------------|
| `user_input`             | `GoldenQA.question`                   |
| `retrieved_contexts`     | chunks returned by `document_search`  |
| `reference_contexts`     | `GoldenQA.ground_truth_contexts`      |
| `response`               | `AnswerWithCitations.answer`          |
| `reference`              | `GoldenQA.ground_truth_answer`        |

**Rejected alternative:** ragas 0.1.x — uses a different (now-deprecated) API
(`Faithfulness()` instantiation pattern, `Dataset` from HuggingFace).  The
0.4.x API is cleaner and the project is actively maintained.

---

## Decision 2: `[eval-live]` optional extra; ragas imports are lazy

**Option A — ragas in `[dev]`:** CI always installs ragas.  Simple, but ragas
pulls in langchain, datasets, tiktoken, instructor, and instructor pulls in
tenacity, pydantic, httpx variants.  The ragas dependency graph adds ~120 MB
to the CI install and has historically had transitive conflicts (protobuf
version pins).  CI runs every commit; the cost is multiplicative.

**Option B (chosen) — ragas in `[eval-live]`:** ragas and its transitive peers
are declared under `[project.optional-dependencies] eval-live`.  CI installs
only `.[dev]`.  Live evaluation runs install `.[eval-live]` separately.

```toml
[project.optional-dependencies]
eval-live = [
    "ragas==0.4.3",
    "langchain==0.3.30",
    ...
]
```

**Lazy imports:** Every `from ragas import ...` statement appears inside a
function body in `eval/ragas/runner.py` and `eval/ragas/nim_judge.py`.  This
makes those modules importable in CI without `ImportError`.  Tests that
actually need ragas use `pytest.importorskip("ragas")` and are marked
`@pytest.mark.slow`.

**EvalHarnessError:** When a lazy-import fails, we re-raise as
`EvalHarnessError` (not bare `ImportError`) so callers can catch it distinctly
from other import failures.

---

## Decision 3: NVIDIA NIM as RAGAS LLM/embedding judge

RAGAS 0.4.x accepts `LangchainLLMWrapper` and `LangchainEmbeddingsWrapper`
around any LangChain-compatible backend.  We wrap NIM's OpenAI-compatible
endpoints:

```python
# LLM judge
ChatOpenAI(base_url=nim_llm_base_url, model=nim_llm_model, temperature=0.0)

# Embedding judge
OpenAIEmbeddings(base_url=nim_embed_base_url, model=nim_embed_model)
```

**Asymmetric-embedding note (nv-embedqa-e5-v5):**  
NVIDIA's `nv-embedqa-e5-v5` requires `input_type="query"` for query vectors
and `input_type="passage"` for document vectors.  LangChain's generic
`OpenAIEmbeddings` does not pass these parameters.  For correctness in
faithfulness and context metrics, the default embedding model should be a
symmetric model (e.g. `nvidia/nv-embed-v1`) or a custom `LangchainEmbeddingsWrapper`
subclass must be provided.  This is documented in `nim_judge.py` for future
implementors.

**Rejected alternative:** OpenAI gpt-4o as judge.  NVIDIA NIM keeps all
evaluation traffic within the customer's infrastructure, which is a hard
requirement for financial document evaluation (data residency / confidentiality).

---

## Decision 4: Per-question error isolation; RPM throttling

The harness wraps each question in `_safe_run_question`, which catches all
exceptions and records them as `QuestionScore.error=<message>`.  A single
NIM timeout, retrieval failure, or RAGAS scorer crash does not abort the run.

An `rpm_limit` (default 10) inter-question sleep avoids saturating the NIM
inference endpoint when evaluating large datasets.

---

## Consequences

- CI remains fast: ragas install not required for the default `.[dev]` install.
- Slow/live tests (`@pytest.mark.slow`) are excluded from CI via
  `addopts = "-m 'not slow'"` in `pyproject.toml`.
- Teams running live evals need `pip install 'finrag[eval-live]'` and a NIM
  API key (`NIM_API_KEY` env var).
- RAGAS version is pinned with `==`; upgrades require explicit ADR update.
- The default LLM judge temperature is 0.0 for deterministic scoring.
