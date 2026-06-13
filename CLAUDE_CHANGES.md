# FinRAG — Engineering Change & Incident Log

> Maintained by the build agent. Every non-trivial change and every critical error gets an entry. Newest first.

## How this file is maintained
- Every code change of substance gets a CHANGELOG entry (what, why, files, commit).
- Every critical error / failed run / blocker gets an INCIDENT entry (symptom, root cause, fix, fallback).
- Entries are append-only and never rewritten after a slice is merged.
- This file is committed alongside the work it describes, in the same PR.

---

## CHANGELOG

### [2026-06-13] Phase 4a — automated RBAC leak suite + golden QA dataset and loader (Phase 4a COMPLETE)
- **What:** Full eval/ subsystem for Phase 4a.
  - `eval/__init__.py`, `eval/errors.py` (`EvalDatasetError`, `EvalLeakError`), `eval/models.py` (`GoldenQA` pydantic v2), `eval/loader.py` (`load_golden_qa` with line-number errors and structlog).
  - `eval/golden/__init__.py`, `eval/golden/golden_qa.jsonl` (10 QA pairs from NVIDIA FY2024 10-K: 6 public, 2 internal, 2 restricted; only `nvda-rev-fy2024` is verified; all others tagged `needs-verification`), `eval/golden/test_dataset.py` (9 CI-safe schema/loader tests).
  - `eval/leak_suite/__init__.py`, `eval/leak_suite/seeder.py` (`LeakTestCorpus` with 9 chunks across 2 orgs + inconsistent chunk), `eval/leak_suite/conftest.py` (pytest fixtures), `eval/leak_suite/test_rbac_leaks.py` (20 adversarial security tests covering all 6 required adversarial cases).
  - `docs/adr/ADR-009-eval-leak-suite-and-golden-dataset.md`.
- **Why:** Phase 4a eval slice — security-first. The leak suite proves the RBAC filter is CI-blocking and deterministic. RAGAS (Phase 4b) requires an LLM judge and is explicitly deferred.
- **Security invariants asserted (20 new tests, all CI-blocking):**
  - Case 1 Positive: OWNER/FINANCE retrieve restricted; ALL roles retrieve public/internal.
  - Case 2 Negative: HR and EMPLOYEE retrieve zero restricted chunks across 3 query phrasings each.
  - Case 2 BM25 side-channel: 5 lexical-overlap queries (words verbatim from restricted text) return zero restricted chunks for HR/EMPLOYEE.
  - Case 3 Cross-tenant: all 4 acme roles × globex = zero leaks; globex/OWNER × acme = zero leaks.
  - Case 4 Defense-in-depth: inconsistent chunk (sensitivity=public, allowed_roles=owner+finance) blocked for hr/employee; accessible for owner/finance.
  - Case 5 Empty-result safety: nonexistent org → empty results → fallback answer → `generate` never called → no restricted text in answer.
  - Case 6 Filter-bypass: 7 prompt-injection query phrasings for acme/HR return zero restricted and zero globex chunks.
  - Context-window proof: `build_rag_prompt` capture confirms restricted chunk_ids never assembled into LLM context for HR.
  - Exhaustive role × restricted matrix: all 4 roles checked in one test.
- **No new dependencies added.** RAGAS is NOT added in this slice (deferred to 4b per ADR-009).
- **Files:** eval/__init__.py, eval/errors.py, eval/models.py, eval/loader.py, eval/golden/__init__.py, eval/golden/golden_qa.jsonl, eval/golden/test_dataset.py, eval/leak_suite/__init__.py, eval/leak_suite/seeder.py, eval/leak_suite/conftest.py, eval/leak_suite/test_rbac_leaks.py, docs/adr/ADR-009*.
- **Test result:** 266 passed, 7 deselected (slow), 7 warnings. +30 new tests (20 leak suite + 9 dataset + 1 loader). Coverage: 91%. ruff: clean. mypy --strict: clean (67 source files).
- **No incidents.**

---

## INCIDENTS

### [2026-06-13] CI red on main push — Docker job references non-existent Phase 5 Dockerfile

- **Symptom:** After PR #3 (fix-ci) merged to main, the next push triggered the `docker-build` job in `.github/workflows/ci.yml`. It failed immediately with `ERROR: failed to read dockerfile: open Dockerfile.api: no such file or directory`. The `ruff + mypy + pytest` job passed fine; only the Docker job failed.
- **Root cause:** `ci.yml` had a `docker-build` job with `if: github.ref == 'refs/heads/main'` referencing `deploy/Dockerfile.api`. That file is a Phase 5 deliverable — `deploy/` is currently empty. The job was silently skipped on every PR (condition false) so the missing file went unnoticed. On the first push-to-main after branch protection was lifted momentarily (PR merge), the condition became true and the job ran, immediately failing.
- **Fix:** Removed the `docker-build` job from `ci.yml` entirely. Left a comment noting it will be re-added once real Dockerfiles exist in `deploy/` (Phase 5). Workflow now has exactly one job: `lint-type-test`.
- **Prevention:** Do not add CI jobs that reference files not yet committed. If a CI step is planned for a future phase, leave it commented-out or add it in the same PR that introduces the referenced file. A job with `if: github.ref == 'refs/heads/main'` is especially risky — it's invisible on every PR review and only fires on merge.
- **Verification:**
  - `ci.yml` job count: 1 (`lint-type-test` only)
  - `ruff check .` → All checks passed
  - `ruff format --check .` → 51 files already formatted
  - `mypy --strict .` / `pytest` — skipped locally due to disk full (no space for pymilvus/pandas); the `lint-type-test` job was already confirmed green on PR #3; this PR changes only `ci.yml` job structure (removes a job), not any source code, so no regression risk.

### [2026-06-13] CI red on chore/fix-ci — pytest-cov undeclared + pymilvus[milvus_lite] missing

- **Symptom:** CI failed on the pytest step with `pytest: error: unrecognized arguments: --cov=. --cov-report=term-missing` (exit code 4). The `--cov` flags require the `pytest-cov` plugin, which was not declared in `pyproject.toml dev` dependencies. CI only installs declared deps; the flag was silently available locally because `pytest-cov` was installed globally on the dev machine. Additionally, a fresh-venv simulation revealed `ModuleNotFoundError: No module named 'milvus_lite'` because `pyproject.toml` declared `pymilvus>=2.4.0` but not the `[milvus_lite]` extra that bundles Milvus Lite.
- **Root cause:** Two undeclared dependencies — same local/CI drift class as the ruff version pin issue, but *missing deps* rather than *version mismatch*: (1) `pytest-cov` used in CI yaml but absent from `[project.optional-dependencies].dev`; (2) `pymilvus` declared without `[milvus_lite]` extra so the Lite in-process store was missing in clean environments. Both were masked locally by globally-installed packages.
- **Additional finding:** `pymilvus 3.0` calls `load_dotenv()` at module import time (in `pymilvus/settings.py`), which reads `.env` from CWD and can pick up `MILVUS_URI=milvus_finrag.db`. On CI, `.env` is gitignored and absent, so this is not an issue. Local devs should be aware.
- **Fix:** Added `pytest-cov==7.1.0` (exact pin, matching local version) and changed `pymilvus>=2.4.0` → `pymilvus[milvus_lite]>=2.4.0` in `pyproject.toml`.
- **Prevention:** Fresh-venv simulation before every CI change: `python -m venv /tmp/ci_venv && /tmp/ci_venv/bin/pip install -e ".[dev]" && run all four CI commands in that venv`. This catches undeclared deps that global installs mask.
- **Verification (clean venv, Python 3.12, no .env):**
  - `ruff check .` → All checks passed
  - `ruff format --check .` → 51 files already formatted
  - `mypy --strict .` → Success: no issues found in 51 source files
  - `pytest -m "not slow" --cov=. --cov-report=term-missing` → 199 passed, 7 deselected, TOTAL 90% coverage

### [2026-06-13] CI red on main — ruff version drift (RUF059 + collateral issues)

- **Symptom:** CI failed on `ruff check .` with 4 `RUF059` (`unused-unpacked-variable`) errors in `rbac/test_adversarial_leaks.py` at lines 200, 230, 256, 491: `corpus` unpacked from `rbac_store_and_index` but never used in those 4 tests. Local `ruff check` passed silently because local ruff was an older version that didn't enforce RUF059.
- **Root cause:** Version drift — dev tools were pinned only with `>=` lower bounds (`ruff>=0.4.0`, `mypy>=1.10.0`, `pytest>=8.2.0`). CI installed `ruff==0.15.17` which added RUF059. Local installs were older. RUF059 was introduced in ruff 0.15.x; the gap went undetected until CI upgraded. Additionally, CI yaml had `DEPLOY_MODE: dev` (invalid; must be `hosted` or `self_hosted`) and `JWT_SECRET: ci-test-secret` (14 chars; minimum is 32 bytes), which would have caused `pytest` to fail on collection even if ruff passed.
- **Fix:**
  1. Renamed `corpus` → `_corpus` at the 4 offending unpack sites (lines 200, 230, 256, 491). The 8 other unpack sites that DO use `corpus` were left unchanged.
  2. Pinned all dev tool versions to exact CI versions: `ruff==0.15.17`, `mypy==2.1.0`, `pytest==9.0.3`, `pytest-asyncio==1.4.0`, `respx==0.23.1`. Eliminates drift by making local and CI installs identical.
  3. Fixed CI env vars: `DEPLOY_MODE: dev` → `hosted`; `JWT_SECRET` padded to 52 chars (≥ 32 required).
  4. Added explicit `-m "not slow"` to CI pytest step (addopts in pyproject.toml already covered it, but explicit is safer against future config drift).
  5. Added `# type: ignore[attr-defined]` to `ingest/parser.py:169` — Docling's `NodeItem` stubs don't expose the `TableItem.export_to_markdown()` subclass method; the surrounding `try/except` guards it at runtime. This was a pre-existing latent mypy 2.1.0 hit.
- **Prevention:** Exact-version pins (`==`) in `[project.optional-dependencies].dev`. Everyone who runs `pip install -e ".[dev]"` gets the EXACT same binaries CI uses. Version drift is structurally impossible once reinstalled.
- **Final CI command results (local, pinned versions, 51 source files on chore/fix-ci):**
  - `ruff check .` → All checks passed
  - `ruff format --check .` → 51 files already formatted
  - `mypy --strict .` → Success: no issues found in 51 source files
  - `pytest -m "not slow"` → 199 passed, 7 deselected, 4 warnings
### [2026-06-13] CI red on main — ruff version drift (RUF059 + collateral rule hits)

- **Symptom:** CI (GitHub Actions) failed on the `ruff check .` step with 4 `RUF059` errors in `rbac/test_adversarial_leaks.py` at lines 200, 230, 256, 491: `unused-unpacked-variable` on `corpus` in `store, bm25, corpus = rbac_store_and_index`. All four tests don't use `corpus`. Locally, `ruff check` passed because local ruff was an older version that didn't enforce RUF059.
- **Root cause:** Version drift — local ruff was pre-0.15.x while CI installed `ruff==0.15.17` (unpinned `>=0.4.0` in `pyproject.toml`). RUF059 (`unused-unpacked-variable`) was added in ruff 0.15.x. Additionally, `mypy>=1.10.0` and `pytest>=8.2.0` were also unpinned, leaving CI free to pick up breaking-change versions at any time.
- **Additional collateral found during fix:** Upgrading to pinned ruff 0.15.17 revealed 21 additional lint errors across `api/` files (F401 unused imports, ANN401 `Any` annotations, B008 `Depends` in defaults, B904 `raise … from`, UP017/UP045/RUF023 style upgrades, I001 import order, E501 line length). Mypy 2.1.0 revealed 1 pre-existing type error (`NodeItem.export_to_markdown` attr-defined). CI YAML had two broken env vars (`DEPLOY_MODE: dev` → invalid, `JWT_SECRET: ci-test-secret` → only 14 chars, minimum 32). `from __future__ import annotations` in `api/app.py` broke FastAPI body-parameter resolution for locally-scoped Pydantic models (annotations became lazy strings; FastAPI treated the `body: LoginRequest` param as a query param, causing 422 on all endpoints).
- **Fix:**
  1. Renamed unused `corpus` → `_corpus` at the 4 offending lines (lines 200, 230, 256, 491). The other 8 uses of `corpus` in the file DO use the variable and were not changed.
  2. Ran `ruff check --fix .` to auto-fix 13 of 21 collateral errors; fixed remaining 8 manually (import cleanup, B904 `from exc`/`from None`, B008 `# noqa`, ANN401 proper starlette types).
  3. Added `# type: ignore[attr-defined]` on `item.export_to_markdown()` — Docling's `NodeItem` stubs don't expose the `TableItem` subclass method; the `try/except` already guards it at runtime.
  4. Removed `from __future__ import annotations` from `api/app.py` — FastAPI uses `get_type_hints()` to resolve parameter types; PEP 563 deferred evaluation makes locally-scoped Pydantic model class names unresolvable, silently degrading them to query parameters (422 on all endpoints).
  5. Fixed CI env vars: `DEPLOY_MODE: dev` → `hosted`; `JWT_SECRET` padded to 52 chars (≥ 32 required by startup assertion).
  6. Added `pydantic[email]` to main dependencies (required for `EmailStr` on `LoginRequest`/`CreateUserRequest`).
  7. Pinned all dev tool versions to exact CI versions: `ruff==0.15.17`, `mypy==2.1.0`, `pytest==9.0.3`, `pytest-asyncio==1.4.0`, `respx==0.23.1`.
  8. Added explicit `-m "not slow"` to the CI pytest step (addopts in pyproject already covered it, but explicit is safer against future config drift).
- **Prevention:** Exact-version pins (`==`) in `[project.optional-dependencies].dev` — no more `>=` drift. Local `pip install -e ".[dev]"` now installs the EXACT same binaries CI uses. Discrepancy between local and CI is structurally impossible once everyone reinstalls.
- **Final CI command results (local, pinned versions):**
  - `ruff check .` → All checks passed
  - `ruff format --check .` → 58 files already formatted
  - `mypy --strict .` → Success: no issues found in 58 source files
  - `pytest -m "not slow"` → 236 passed, 7 deselected, 7 warnings

---

## CHANGELOG

### [2026-06-13] chore/fix-ci-docker — remove premature Docker build job from CI

- **What:** Removed the `docker-build` job from `.github/workflows/ci.yml`. Left a comment explaining it will be re-added in Phase 5 when `deploy/Dockerfile.api` exists. CI now has exactly one job: `lint-type-test` (ruff + mypy + pytest).
- **Why:** The Docker job referenced `deploy/Dockerfile.api` which is a Phase 5 deliverable. It was skipped on PRs (`if: github.ref == 'refs/heads/main'`) but ran on merge to main and failed immediately.
- **Files:** `.github/workflows/ci.yml`, `CLAUDE_CHANGES.md`.
- **Test result:** `ruff check .` → clean; `ruff format --check .` → 51 files already formatted. `lint-type-test` job was already green on PR #3; no source code changed in this slice.

### [2026-06-13] chore/fix-ci — ruff RUF059 fix + dev-tool version pinning
- **What:** Fixed 4 `RUF059` errors in `rbac/test_adversarial_leaks.py` (unused `corpus` → `_corpus`); pinned dev tool versions to exact versions matching CI; fixed broken CI env vars (`DEPLOY_MODE`, `JWT_SECRET`); added explicit `-m "not slow"` to CI pytest step; fixed latent mypy 2.1.0 `attr-defined` in `ingest/parser.py`.
- **Why:** CI was red on main due to ruff version drift — unpinned `>=` allowed CI to pick up ruff 0.15.17 which enforces RUF059; local was older and silent. Pinning dev tools makes local == CI structurally.
- **Files:** `rbac/test_adversarial_leaks.py`, `pyproject.toml`, `.github/workflows/ci.yml`, `ingest/parser.py`, `CLAUDE_CHANGES.md`.
- **Test result:** 199 passed, 7 deselected (slow), 4 warnings. ruff: clean. mypy --strict: clean (51 source files).
### [2026-06-13] chore/fix-ci — ruff RUF059 fix + dev-tool version pinning
- **What:** Fixed 4 `RUF059` unused-unpacked-variable errors in `rbac/test_adversarial_leaks.py`; pinned dev tool versions to eliminate CI/local drift; fixed 21 collateral ruff/mypy/pytest issues uncovered by the upgrade; corrected broken CI env vars; removed `from __future__ import annotations` from `api/app.py` that caused 422s on all FastAPI endpoints.
- **Why:** CI was red on main. Root cause: unpinned `ruff>=0.4.0` in pyproject.toml allowed CI to pick up ruff 0.15.17 which enforces RUF059; local ruff was older and silent. Pinning dev tools to exact versions makes local == CI structurally.
- **Files:** `rbac/test_adversarial_leaks.py` (4× `corpus` → `_corpus`), `pyproject.toml` (pin dev deps, add `pydantic[email]`), `.github/workflows/ci.yml` (add `-m "not slow"`, fix DEPLOY_MODE and JWT_SECRET), `api/app.py` (remove `from __future__ import annotations`, remove unused imports), `api/identity.py` (B904 from-clause, B008 noqa, proper starlette types), `api/security.py` (UP017 UTC alias), `api/users.py` (UP045 X|None), `api/test_*.py` (import sort, E501 wrap, return types), `ingest/parser.py` (type: ignore[attr-defined] for Docling subclass method), `CLAUDE_CHANGES.md`.
- **Test result:** 236 passed, 7 deselected (slow), 7 warnings. ruff: clean. mypy --strict: clean (58 source files).

### [2026-06-13] Phase 3 — JWT auth + multi-tenancy (Phase 3 COMPLETE)
- **What:** Full JWT authentication layer that makes identity unforgeable. New: `api/security.py` (argon2 password hashing via passlib, `hash_password`/`verify_password` with constant-time compare; JWT create/decode via python-jose HS256, `create_access_token`/`decode_token`, custom `AuthError`/`TokenExpiredError`/`InvalidTokenError`); `api/identity.py` (typed `Identity` class with `user_id`/`org_id`/`role`, `get_current_identity` FastAPI dependency — the SOLE gateway for identity in the system, structured-logs every auth decision); `api/users.py` (SQLite `UserStore` with `create_user`/`get_user_by_email`/`authenticate`, `DuplicateUserError`, `get_user_store` process-singleton); `api/app.py` (FastAPI chain-server with `create_app()` factory, startup JWT_SECRET assertion in lifespan, structured-log middleware; endpoints: `POST /auth/login`, `POST /admin/users` owner-only, `POST /documents/upload`, `POST /query`, `GET /healthz`). Also: `ingest/__init__.py` fixed (removed eager `ingest.pipeline` import that caused circular import via `api.identity → rbac.roles → ingest → ingest.pipeline → rbac.classifier → rbac.roles`). 37 new tests: `test_security.py` (12 tests — hash round-trips, slow-hash proof, JWT claims, expired/tampered/wrong-secret/malformed rejection, missing-claim rejection), `test_identity.py` (6 tests — valid token → Identity, 401 on missing/expired/bad-sig/malformed/unknown-role), `test_app.py` (19 tests including 7 adversarial). ADR-008.
- **Why:** Phase 2's RBAC trusted `(org_id, role)` as function arguments. Phase 3 makes these come ONLY from a cryptographically-signed JWT that a logged-in user cannot forge. `org_id` and `role` have NO request-body representation at any endpoint — isolation is structural, not just a policy check.
- **Security invariants proven by adversarial suite:**
  - FORGED ROLE (#1): HR user's `role` in `/query` response is "hr" — request body has no role field to elevate
  - TOKEN TAMPERING (#2): Valid HR token with role claim flipped to "owner" (without re-signing) → 401 signature failure. This is the key proof: self-promotion without the JWT_SECRET is impossible.
  - CROSS-TENANT (#3): acme-token user's `/query` response `org_id` is always "acme" — no request field exists to specify "globex"; cross-tenant access is impossible by construction
  - WRONG SECRET (#4): Token signed with a different secret → 401
  - EXPIRED TOKEN (#5): Token past `exp` → 401
  - NON-OWNER CREATE USER (#6): role=employee/hr/finance calling `/admin/users` → 403; only owner can provision, and only into their own org
- **Files:** api/security.py, api/identity.py, api/users.py, api/app.py, api/test_security.py, api/test_identity.py, api/test_app.py, ingest/__init__.py (circular-import fix), pyproject.toml (passlib[argon2], python-jose[cryptography], types-passlib), .env.example (updated JWT docs), docs/adr/ADR-008*, CLAUDE_CHANGES.md.
- **Test result:** 236 passed, 7 deselected (slow), 7 warnings. ruff: clean. mypy --strict: clean (58 source files).

### [2026-06-13] Phase 2 — chunk-level RBAC enforced at retrieval time (Phase 2 COMPLETE)
- **What:** Full chunk-level RBAC with dual-axis enforcement (org_id tenant isolation + role allowlist). New: `rbac/roles.py` (Role StrEnum, `_POLICY` dict — single source of truth, `sensitivity_to_default_roles`, `can_role_see`); `rbac/classifier.py` (heuristic keyword scanner → SensitivityLevel, `assign_access` stamps org_id + allowed_roles onto every chunk at ingest time); `rbac/filter.py` (`build_rbac_filter` with injection prevention — rejects `"`, `\`, null bytes in org_id). Updated: `ingest/pipeline.py` (removed hard-coded `allowed_roles` param, now calls `assign_access` per chunk); `retrieval/search.py` (added `org_id`+`role` params, builds Milvus filter AND BM25 post-filter via `_passes_rbac`); `generation/answer.py` (passes `org_id`+`role` to `document_search`). 51 new tests: `test_roles.py` (24 tests — exhaustive policy table, all 12 role×sensitivity combinations), `test_filter.py` (15 tests — injection prevention: double-quote, backslash, null byte, empty org_id), `test_adversarial_leaks.py` (12 adversarial security tests — zero-leak proofs, prompt injection immunity, BM25 side-channel closure, cross-org isolation). ADR-007.
- **Why:** Non-negotiable security invariant: forbidden chunks must NEVER enter the LLM context window. Prompt-level access control is defeatable by prompt injection; Milvus `ARRAY_CONTAINS` runs at C++ storage layer before any Python sees the data. BM25 post-filter closes the lexical side-channel.
- **Security invariants proven by adversarial suite:**
  - HR cannot retrieve RESTRICTED salary chunk (chunk count == 0)
  - EMPLOYEE cannot retrieve RESTRICTED salary chunk (chunk count == 0)
  - HR cannot retrieve GLOBEX chunks (cross-tenant isolation, count == 0)
  - EMPLOYEE cannot retrieve GLOBEX chunks (cross-tenant isolation, count == 0)
  - OWNER only sees its own org's chunks (count == 3 for acme, never globex)
  - RESTRICTED chunk NEVER enters build_rag_prompt when called as HR (context-window proof via mock capture)
  - 5 prompt injection attempts all return count == 0 (filter is at C++ layer, query string cannot influence it)
  - BM25 "salary" keyword query returns 0 results for HR (BM25 side-channel closed by _passes_rbac post-filter)
  - Positive sanity: HR can retrieve public + internal chunks (count == 2)
  - Empty result for non-existent org
- **Files:** rbac/roles.py, rbac/classifier.py, rbac/filter.py, rbac/conftest.py, rbac/test_roles.py, rbac/test_filter.py, rbac/test_adversarial_leaks.py, rbac/__init__.py, ingest/pipeline.py, retrieval/search.py, generation/answer.py, generation/test_answer.py (updated filter_expr assertion), docs/adr/ADR-007*, CLAUDE_CHANGES.md.
- **Test result:** 199 passed, 7 deselected (slow), 3 warnings.

### [2026-06-12] Phase 1 slice 5 — generation + citation enforcement (Phase 1 COMPLETE)
- **What:** `GenerationError` exception; async `generate()` LLM NIM client (OpenAI-compatible chat/completions, temperature=0.1, retry on 429/5xx, nim_cost_log hook); `build_rag_prompt(query, chunks)` assembling numbered [N]-labeled context block + grounding+citation system prompt; `parse_citations(answer, chunks)` post-generation enforcement (reject hallucinated indices, warn on uncited positive answers, no warning on refusal); `AnswerWithCitations` + `CitationSource` pydantic v2 models; `answer_query` Phase 1 end-to-end entrypoint (document_search → build_rag_prompt → generate → parse_citations, filter_expr threaded through for Phase 2 RBAC); 32 tests (all non-slow) + 1 @pytest.mark.slow live test; ADR-006.
- **Why:** complete the Phase 1 loop — upload 10-K → ask question → cited answer. `answer_query` is the single call-site for Phase 2 and beyond.
- **RBAC hook:** `filter_expr: str | None = None` on `answer_query` threads unchanged to `document_search` → Milvus ANN search. Phase 2 injects `'org_id == "..." AND ARRAY_CONTAINS(allowed_roles, "...")'` here; forbidden chunks never enter the RAG prompt or citations.
- **Citation enforcement:** [N] numeric markers in the prompt; post-generation regex parse; hallucinated indices (N > len(chunks)) silently rejected; no-citation positive answers emit `citations.no_grounding` structlog warning; refusal phrase ("I cannot answer…") suppresses the warning. Uses `structlog.testing.capture_logs()` in tests (structlog writes to stdout, not Python logging).
- **Live test result:** `NVIDIA's total revenue for fiscal year 2024 was $26.97 billion [1].` → `live_nvidia_10k.pdf, page 0 (chunk_id=e2c75bfcaf97769d)`. Prompt tokens: 301, completion tokens: 21, total latency: 1.77s.
- **Files:** generation/errors.py, generation/llm_client.py, generation/prompt.py, generation/citations.py, generation/answer.py, generation/conftest.py, generation/test_prompt.py, generation/test_citations.py, generation/test_answer.py, docs/adr/ADR-006*, CLAUDE_CHANGES.md.
- **Test result:** 148 passed, 7 deselected (slow), 3 warnings.

### [2026-06-12] Phase 1 slice 4 — hybrid retrieval + reranking
- **What:** `dense_search` on MilvusStore (with `filter_expr` RBAC injection point), in-memory `BM25Index` (rank-bm25, whitespace tokenisation), `rrf_fuse` (Reciprocal Rank Fusion, k from system_config), async `rerank` NIM client (nv-rerankqa-mistral-4b-v3, env-driven URL/model, retry on 429/5xx), `document_search` orchestrator (embed→dense→bm25→rrf→rerank), `RerankError`, `config_db_path` setting, ADR-005. 53 new tests (all non-slow).
- **Why:** turn a query string into a ranked list of relevant chunks for the generation step; set up the Phase 2 RBAC hook at the exact Milvus search boundary.
- **RBAC hook:** `filter_expr: str | None = None` parameter threads from `document_search` → `dense_search` → Milvus ANN search. Phase 2 injects `'org_id == "{o}" AND ARRAY_CONTAINS(allowed_roles, "{r}")'` here; forbidden chunks never enter the reranker or LLM.
- **Key invariant:** `embed_texts(..., input_type="query")` — nv-embedqa-e5-v5 is asymmetric; using "passage" for queries silently destroys recall. Guarded by `test_embed_called_with_input_type_query`.
- **Files:** retrieval/errors.py, retrieval/vector_store.py, retrieval/bm25.py, retrieval/fusion.py, retrieval/reranker.py, retrieval/search.py, retrieval/test_fusion.py, retrieval/test_bm25.py, retrieval/test_reranker.py, retrieval/test_search.py, retrieval/test_vector_store.py (extended), config/settings.py, docs/adr/ADR-005*, CLAUDE_CHANGES.md.
- **Test result:** 116 passed, 6 deselected (slow), 3 warnings.

### [2026-06-12] Phase 1 slice 3 — Milvus write (vector store + ingest_and_store)
- **What:** `VectorStoreError` exception, `MilvusStore` class (full 13-field schema from day one, `allowed_roles` as `DataType.ARRAY` of VARCHAR, AUTOINDEX+COSINE metric, upsert semantics), `ingest_and_store()` async end-to-end entrypoint in pipeline.py, 14 Milvus-Lite tests (all non-slow, in-process), ADR-004.
- **Why:** persist embedded chunks in Milvus so Phase 1 slice 4 can do hybrid retrieval; schema laid down once with all future-phase fields to avoid collection re-creation.
- **Files:** retrieval/errors.py, retrieval/vector_store.py, retrieval/conftest.py, retrieval/test_vector_store.py, ingest/pipeline.py, docs/adr/ADR-004*, CLAUDE_CHANGES.md.
- **Key invariant:** `allowed_roles` is `DataType.ARRAY` (element_type VARCHAR) — required for Phase 2 `ARRAY_CONTAINS(allowed_roles, user_role)` filter inside ANN search so forbidden chunks never enter the LLM context window.
- **Test result:** 77 passed, 5 deselected (slow), 3 warnings.

### [2026-06-12] Phase 1 slice 2 — embedding (NeMo NIM client + embed_chunks)
- **What:** `EmbeddingError` exception, async NIM HTTP client (`nim_client.py`) with 36-RPM throttle + exponential-backoff retry, `embed_chunks` step with count/dimension validation, 21 fast tests (respx-mocked), one slow live NIM test, ADR-003, `respx` dev dep, `asyncio_mode = "auto"` pytest config.
- **Why:** fill `Chunk.embedding` with dense vectors from nv-embedqa-e5-v5 in preparation for the Milvus write slice.
- **Files:** ingest/errors.py, ingest/nim_client.py, ingest/embedder.py, ingest/test_nim_client.py, ingest/test_embedder.py, docs/adr/ADR-003*, pyproject.toml, CLAUDE_CHANGES.md.
- **Commits:** ba8eaf5, ea75eb3.

### [2026-06-12] Phase 1 slice 1 — ingest (parse + chunk)
- **What:** Chunk model (full schema, dev-default access fields), Docling parser, config-driven chunker, pipeline entrypoint, tests with PDF fixture, ADR-002.
- **Why:** turn a PDF into schema-complete chunks ready to embed.
- **Files:** ingest/models.py, ingest/parser.py, ingest/chunker.py, ingest/pipeline.py, ingest/errors.py, ingest/test_*.py, docs/adr/ADR-002*.
- **Commits:** 9bdd4d5, 0466192, 8b0cdb6.

### [2026-06-12] Phase 0 — scaffold + config (retroactive baseline)
- **What:** repo skeleton, CI, ADR-001, typed settings, runtime system_config with tests.
- **Why:** establish trunk + green CI before feature work.
- **Files:** pyproject.toml, .github/workflows/ci.yml, config/*, docs/adr/ADR-001*.
- **Commits:** 955e8d0, 978bcd0.

---

## INCIDENT LOG

### [2026-06-12] Phase 1 slice 2 — mypy narrowing + dual Python env
- **Symptom 1:** `mypy --strict` error: "Incompatible types in assignment (expression has type 'list[float] | None', variable has type 'list[float]')" in the pre-allocated result slot loop.
- **Where:** ingest/nim_client.py, `embed_texts()` result assembly loop.
- **Root cause:** mypy does not narrow `list[float] | None` to `list[float]` for a for-loop variable after a `if var is None: raise` guard, even though the raise is reachable on all None paths.
- **Fix:** eliminated the pre-allocated list; collect each batch result in `batched_vectors: list[list[list[float]]]` and flatten at the end. No Optional needed, no narrowing required.
- **Fallback / prevention:** if pre-allocation is reintroduced (for future parallel batches), use `cast(list[list[float]], [v for v in results if v is not None])` after a separate None-slot check.
- **Status:** Resolved.

- **Symptom 2:** `httpx` and `respx` not importable in `python3.12 -m pytest` because `/opt/homebrew/bin/python3.12` and `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12` are two different installs; packages land in the Framework site-packages but `pytest` resolves to the Homebrew one.
- **Where:** CI test run, dev workstation.
- **Root cause:** macOS has two Python 3.12 installs; `pip` (Framework) and `python3.12 -m pip` (Homebrew) manage different site-packages.
- **Fix:** ran `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m pytest` explicitly; installed missing deps (`structlog`, `mypy`) into the Framework env via `pip install`.
- **Fallback / prevention:** add a `Makefile` target or `CONTRIBUTING.md` note specifying `pip install -e ".[dev]"` must be done in the same env used to run tests. TODO for slice 3.
- **Status:** Resolved.

### [2026-06-12] Phase 1 slice 4 — BM25Okapi ZeroDivisionError on empty corpus
- **Symptom:** `BM25Okapi([[]])` raises `ZeroDivisionError: division by zero` in `_calc_idf` when given an empty or single-empty-doc corpus.
- **Where:** retrieval/bm25.py `BM25Index.__init__()` and retrieval/test_bm25.py + test_search.py.
- **Root cause:** rank-bm25's `_calc_idf` divides by `len(self.idf)` which is 0 when no real tokens are indexed.
- **Fix:** store `_bm25: BM25Okapi | None = None` when `chunks` is empty; guard `search()` with `if self._bm25 is None: return []`.
- **Fallback / prevention:** any BM25 wrapper over rank-bm25 must guard the empty-corpus case. Added `test_empty_corpus_builds_valid_index` to the suite.
- **Status:** Resolved.

### [2026-06-12] Phase 1 slice 4 — rerank NIM wrong URL and model name
- **Symptom:** Live reranker test returned 404 from all attempted endpoints.
- **Where:** retrieval/reranker.py, config/settings.py, .env.
- **Root cause:** NVIDIA's hosted reranking NIM uses `ai.api.nvidia.com/v1/retrieval/nvidia/reranking` (not `integrate.api.nvidia.com/v1/ranking`). The model name on the hosted API is `nvidia/rerank-qa-mistral-4b` (not `nvidia/nv-rerankqa-mistral-4b-v3`). The `.env` and settings defaults carried over the wrong values from the embedding NIM.
- **Fix:** Updated `nim_rerank_base_url` default to `https://ai.api.nvidia.com/v1/retrieval/nvidia`, updated `nim_rerank_model` default to `nvidia/rerank-qa-mistral-4b`, changed reranker to append `/reranking` (not `/ranking`), updated `.env`, ADR-005, and test helper.
- **Fallback / prevention:** Self-hosted Phase 5 NIMs expose the endpoint at `http://nim-rerank-service:8000/v1/retrieval/nvidia` — the path structure is identical, only the host changes. Override `NIM_RERANK_BASE_URL` via env var for self-hosted deployments.
- **Status:** Resolved. Live test: `nvidia/rerank-qa-mistral-4b` correctly ranked revenue chunks above an unrelated chunk (logits: -2.5, -6.0, -15.2).

### [2026-06-12] Phase 1 slice 4 — test_filter_expr incorrectly asserted BM25 is filtered
- **Symptom:** `test_filter_expr_threads_to_dense_search` failed because `chunk_other` appeared in rerank candidates despite `filter_expr='org_id == "acme"'`.
- **Where:** retrieval/test_search.py.
- **Root cause:** `filter_expr` correctly scopes only the dense (Milvus) search. The BM25 index is corpus-wide in Phase 1 — filtering BM25 is a Phase 2 concern. The test incorrectly asserted that `other_org` chunks would be absent from rerank.
- **Fix:** rewrote the test to spy on `store.dense_search` and assert it received the correct `filter_expr`, rather than asserting absence of chunks from rerank.
- **Fallback / prevention:** ADR-005 documents that Phase 2 must scope the BM25 index to the authorised corpus (rebuild per-org or filter at index-build time).
- **Status:** Resolved.

### [2026-06-12] Phase 1 slice 3 — mypy generator return type on pytest fixture
- **Symptom:** `mypy --strict` error: "The return type of a generator function should be 'Generator' or one of its supertypes [misc]" in `retrieval/conftest.py`.
- **Where:** retrieval/conftest.py, `milvus_db` fixture.
- **Root cause:** Fixture uses `yield` making it a generator function; annotated as `-> Path` instead of `-> Generator[Path, None, None]`.
- **Fix:** added `from collections.abc import Generator` and changed return type to `Generator[Path, None, None]`.
- **Fallback / prevention:** any yield-based pytest fixture must use `Generator[YieldType, None, None]` (or `Iterator[YieldType]`) as the return annotation under `--strict`.
- **Status:** Resolved.

### [2026-06-12] Phase 1 slice 5 — structlog warning tests used Python logging caplog
- **Symptom:** `test_no_citation_answer_triggers_warning` and `test_hallucinated_citation_triggers_warning` failed with empty `caplog.text` despite structlog clearly emitting `[warning]` lines to stdout.
- **Where:** generation/test_citations.py.
- **Root cause:** pytest's `caplog` fixture captures messages routed through Python's standard `logging` module. structlog by default uses its own renderer pipeline that writes directly to stdout (via `PrintLoggerFactory`), bypassing the Python logging system entirely.
- **Fix:** replaced `caplog.at_level(logging.WARNING)` with `structlog.testing.capture_logs()` context manager, which intercepts structlog events at the processor level and returns them as a list of dicts. Assertions now check `e["event"]` keys.
- **Fallback / prevention:** any test that asserts structlog emitted a warning or error must use `structlog.testing.capture_logs()`, not `caplog`. Python `caplog` only works when structlog is explicitly configured to route through `logging.Logger` (e.g., via `structlog.stdlib.add_log_level` + `structlog.stdlib.PositionalArgumentsFormatter` pipeline). The default structlog configuration does not do this.
- **Status:** Resolved.

### [2026-06-13] Phase 2 — ruff EN DASH in docstring blocked commit
- **Symptom:** `ruff check` reported `RUF002 Docstring contains ambiguous – (EN DASH)` in `rbac/roles.py:6`. The `sed -i` command to fix it failed on macOS with `sed: -I or -i may not be used with stdin`.
- **Where:** rbac/roles.py, line 6. Session also interrupted here.
- **Root cause:** The docstring contained a Unicode EN DASH (U+2013) in "role–sensitivity" instead of a plain ASCII hyphen. macOS BSD `sed` requires `sed -i '' ...` (empty string for in-place) not `sed -i ...` (Linux form).
- **Fix:** Used the Edit tool directly to replace the EN DASH with a HYPHEN-MINUS.
- **Fallback / prevention:** When `sed -i` fails on macOS, use the Edit tool or `perl -pi -e` which has consistent cross-platform in-place semantics.
- **Status:** Resolved.

### [2026-06-13] Phase 2 — generation/test_answer.py broken by new document_search signature
- **Symptom:** `test_filter_expr_threads_to_document_search` was asserting `mock_doc_search.assert_called_once_with(query=..., store=..., bm25_index=..., filter_expr=expr)` — missing the new `org_id=None, role=None` kwargs added in Phase 2.
- **Where:** generation/test_answer.py.
- **Root cause:** `answer_query` now always passes `org_id` and `role` to `document_search` (defaulting to None). The test's call assertion did not include those kwargs.
- **Fix:** Updated the assertion to include `org_id=None, role=None`.
- **Fallback / prevention:** When a function signature gains new parameters with defaults, review existing mock call assertions that use `assert_called_once_with` — they assert on ALL kwargs.
- **Status:** Resolved.

### [2026-06-13] Phase 3 — circular import via ingest.__init__ when api.identity is loaded first
- **Symptom:** `ImportError: cannot import name 'Role' from partially initialized module 'rbac.roles'` when `pytest api/` ran and `api/test_app.py` was the first file collected.
- **Where:** `api/identity.py` → `rbac.roles` → `from ingest.models import SensitivityLevel` → `ingest/__init__.py` → `ingest.pipeline` → `rbac.classifier` → `rbac.roles` (circular).
- **Root cause:** `ingest/__init__.py` eagerly imported `ingest_pdf` from `ingest.pipeline`. When Python was loading `rbac.roles` (triggered by `api.identity`) and hit `from ingest.models import SensitivityLevel`, it initialized the `ingest` package, which ran `ingest/__init__.py`, which loaded `ingest.pipeline`, which loaded `rbac.classifier`, which tried to import `Role` from `rbac.roles` — which was still mid-initialization. The existing Phase 2 tests passed because they loaded `rbac.roles` via a path where `ingest.models` was already in `sys.modules` before `ingest.pipeline` was needed.
- **Fix:** Removed `from ingest.pipeline import ingest_pdf` from `ingest/__init__.py`. No external code used `from ingest import ingest_pdf` — all call sites import from `ingest.pipeline` directly. Added a WHY-comment explaining the removal.
- **Fallback / prevention:** The guard is: never eagerly import modules in `__init__.py` that form a cross-module import cycle. Any future `__init__.py` re-export should be checked for cycles if it involves `ingest.pipeline` or `rbac.*`.
- **Status:** Resolved.

### [2026-06-13] Phase 3 — FastAPI 422 on pydantic models defined inside create_app closure
- **Symptom:** All POST endpoints returned 422 with `{'loc': ['query', 'body'], 'msg': 'Field required', 'input': None}`. FastAPI treated `body: LoginRequest` as a query parameter named "body" rather than the request body.
- **Where:** `api/app.py` `create_app()` — pydantic models (`LoginRequest`, `QueryRequest`, etc.) were defined inside the factory function.
- **Root cause:** FastAPI's type introspection resolves parameter types at route registration time. Classes defined inside a function closure are not reliably resolved by the dependency injection machinery — FastAPI fell back to treating them as query parameters.
- **Fix:** Moved all pydantic request/response models to module level (outside `create_app`). Added a WHY-comment explaining the requirement.
- **Fallback / prevention:** FastAPI pydantic models must always be defined at module level, not inside factory functions or closures.
- **Status:** Resolved.

### [TEMPLATE — copy for each incident]
- **Symptom:** what failed, exact error message / behavior.
- **Where:** file, command, or slice.
- **Root cause:** the actual underlying reason (not the surface symptom).
- **Fix:** what was changed to resolve it.
- **Fallback / prevention:** what we'd do if the fix fails in future, or what guard was added so it can't recur.
- **Status:** Resolved / Mitigated / Open.

### [2026-06-12] Phase 1 slice 1 — mypy + ruff + invalid test patch (retroactive)
- **Symptom:** mypy errors on config overload + missing settings default; ruff zip(strict=) warnings; an invalid __globals__ test patch in test_parser.py.
- **Root cause:** ConfigKey Literal had no attribute access; nim_api_key had no default; test used an unsupported patch mechanism.
- **Fix:** simplified get_config signature, added SecretStr("") default, replaced the patch with a sys.modules docling mock.
- **Fallback / prevention:** slow-marked the live Docling test so CI never depends on the heavy dep.
- **Status:** Resolved.
