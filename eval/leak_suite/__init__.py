"""eval.leak_suite — automated RBAC leak-test suite.

CI-safe: deterministic fake embeddings, mocked NIM calls, real Milvus Lite
filter execution.  No network, no API key, NOT marked slow.

This suite SUPERSETS rbac/test_adversarial_leaks.py:
  - Parametrised coverage of all (role x sensitivity) combinations
  - BM25 side-channel re-coverage (lexical-overlap queries)
  - Cross-tenant coverage across ≥2 orgs
  - Defense-in-depth: allowed_roles vs sensitivity_level disagreement
  - Empty-result safety: unauthorized empty context → no fallback leak
  - Filter-bypass attempts: injection via query text cannot widen results

Architecture documented in docs/adr/ADR-009.
"""
