"""eval — FinRAG evaluation framework.

Phase 4a delivers:
  - eval.models:      GoldenQA pydantic v2 schema
  - eval.loader:      load_golden_qa() typed dataset loader
  - eval.errors:      EvalDatasetError, EvalLeakError domain exceptions
  - eval.golden:      golden QA dataset (JSONL) + schema/loader tests
  - eval.leak_suite:  automated RBAC leak-test suite (CI-safe, no network)

Phase 4b (future) will add RAGAS harness (faithfulness, answer relevance,
context precision/recall) consuming the golden dataset produced here.
"""
