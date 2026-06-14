# FinRAG — Build State

> Living document. Updated at the end of every phase. Source of truth for what's shipped, what's next, and what broke.

---

## 1. Project Snapshot

**Repo:** `finrag/` — multi-tenant financial document RAG platform on NVIDIA NIM.  
**Resume sentence:** Built and deployed a production-grade multi-tenant financial RAG platform on AWS using NVIDIA NIM microservices (LLM + embedding + reranking on GPU), with hybrid retrieval (BM25 + dense + RRF + cross-encoder reranking), chunk-level RBAC enforced at retrieval time, Milvus vector store, Kubernetes orchestration with HPA autoscaling, Prometheus/Grafana observability, and RAGAS evaluation.

**Non-negotiable invariant:** RBAC filters execute inside the Milvus vector query (`ARRAY_CONTAINS(allowed_roles, role)` WHERE clause). Forbidden chunks must never enter the LLM context window. Filtering after retrieval is insecure.

---

## 2. Current State

| Phase | Status | PR(s) | Notes |
|-------|--------|-------|-------|
| Phase 0 — scaffold + CI + config | ✅ MERGED | #1–2 | Repo skeleton, GitHub Actions CI, typed settings, runtime `system_config`. |
| Phase 1 — core text RAG loop | ✅ MERGED | #1–2 | Ingest→chunk→embed→Milvus→hybrid retrieve→rerank→cited answer. Single tenant, no auth. 148 tests. |
| Phase 2 — chunk-level RBAC | ✅ MERGED | #3 | `ARRAY_CONTAINS` Milvus filter + BM25 post-filter + adversarial leak suite. 199 tests. |
| Phase 3 — JWT auth + multi-tenancy | ✅ MERGED | #5 | Argon2 password hashing, HS256 JWT, `get_current_identity` dependency, org isolation. 236 tests. |
| Phase 4 — evaluation | ✅ MERGED | #7 leak suite + golden dataset; #8 RAGAS harness, NIM-as-judge, `[eval-live]` optional extra | ~288 tests passing; +22 CI-safe eval tests this phase; live RAGAS tests are `@pytest.mark.slow` (excluded from CI, run via `python -m eval.ragas` against the live NIM). |
| UI — web integration | ✅ PR OPEN | — | Frontend (Claude Design export) lives in `web/`; `api.js` wired to real FastAPI endpoints with normalize layer. Documents list + admin members list remain mock-only (no list endpoints in backend yet). |
| Phase 5 — GPU/EKS deployment (burst) | ⬜ NOT STARTED | — | 3 NIMs on EKS via NIM Operator, Milvus on cluster, Prometheus/Grafana/DCGM, HPA, Locust load test. Spin up → capture proof → tear down. |
| Phase 6 — multimodal v2 (stretch) | ⬜ NOT STARTED | — | Chart images → VLM caption → embed caption as text (`content_type='chart'`). |

**main tip after Phase 4: b5a7acc**  
(main tip after Phase 3: d9b57f1)

---

## 3. Immediate Next Actions

1. **UI (Claude Design) — in progress.** Login page + cited-answer hero first. Then: document upload + loaded-docs view, dashboard, owner-only admin panel. Connects to existing FastAPI endpoints (`/auth/login`, `/query`, `/documents/upload`, `/admin/users`).
2. **Phase 5 — GPU/EKS deploy.** After UI is complete. Requires real AWS GPU budget (~$10–30 burst). Spin up, capture nvidia-smi + Grafana dashboards + HPA scaling screenshots, tear down same day.
3. **Backlog — CI action version bump:** `actions/checkout v4 → v5` and `actions/setup-python v5 → v6` (still on old versions per `.github/workflows/ci.yml`). Low urgency — current versions work fine, no security advisory. Do in a `chore/ci-bump` PR before Phase 5 CI changes.

---

## 4. Architecture Status

All Phase 1–4 invariants are enforced and proven by tests:

| Invariant | Enforced by | Proven by |
|-----------|-------------|-----------|
| RBAC filter runs in Milvus (never in prompt) | `rbac/filter.py` → `retrieval/search.py` | 20 adversarial leak tests in `eval/leak_suite/` |
| `allowed_roles` is a Milvus `DataType.ARRAY` | `retrieval/vector_store.py` schema | `test_vector_store.py` |
| BM25 side-channel closed by post-filter | `_passes_rbac` in `retrieval/search.py` | BM25 side-channel tests in `eval/leak_suite/` |
| Cross-tenant isolation via `org_id` | Milvus filter AND `Identity.org_id` from JWT | Cross-tenant cases 3+4 in leak suite |
| Identity comes ONLY from JWT (no request body) | `api/identity.py` `get_current_identity` | `test_identity.py` adversarial suite (6 tests) |
| Prompt injection cannot bypass filter | filter lives at C++ Milvus layer | filter-bypass case 6 in leak suite (7 phrasings) |

---

## 5. Test Suite Summary

| Phase completed | Passing (CI, `not slow`) | Deselected (`slow`) | Key additions |
|-----------------|--------------------------|---------------------|---------------|
| Phase 1 | 148 | 6 | Full RAG pipeline unit + integration |
| Phase 2 | 199 | 7 | RBAC filter, classifier, adversarial leak suite |
| Phase 3 | 236 | 7 | JWT security, identity dependency, 7 API adversarial tests |
| Phase 4a | 266 | 7 | 20 RBAC leak tests, 9 golden dataset tests, 1 loader test |
| Phase 4b (current) | ~288 | 7 | +22 CI-safe RAGAS harness tests (all mocked, no ragas import at collection) |

Live RAGAS tests (`@pytest.mark.slow`) require `pip install -e ".[eval-live]"` and a valid `NVIDIA_API_KEY`. Run via `python -m eval.ragas`. Not a merge gate — CI + mocked tests are the gate.

---

## 6. Module Map

```
finrag/
├── ingest/          # PDF→chunks (Docling) + NeMo embedding NIM client
├── retrieval/       # Milvus vector store, BM25, RRF fusion, reranking NIM
├── rbac/            # RBAC filter builder, role policy, classifier
├── generation/      # LLM NIM client, citation enforcement, answer orchestrator
├── eval/            # RAGAS harness (eval/ragas/), golden dataset, RBAC leak suite
├── api/             # FastAPI app: auth, query, upload, admin endpoints
├── config/          # Typed settings, runtime system_config (DB-backed, no redeploy to tune)
├── docs/adr/        # ADR-001 through ADR-010
└── .github/         # CI: ruff + mypy --strict + pytest (not slow)
```

---

## 7. ADRs

| ADR | Decision |
|-----|----------|
| ADR-001 | Stack and architecture (NVIDIA NIM, Milvus, FastAPI, RAGAS) |
| ADR-002 | Chunking strategy (Docling + recursive/semantic) |
| ADR-003 | NeMo embedding NIM + 36-RPM throttle + retry |
| ADR-004 | Milvus schema (13 fields, `allowed_roles` as ARRAY from day one) |
| ADR-005 | Hybrid retrieval: BM25 + dense + RRF + reranking NIM |
| ADR-006 | Generation + citation enforcement (`[N]` markers, post-parse enforcement) |
| ADR-007 | RBAC at retrieval time (Milvus `ARRAY_CONTAINS`, BM25 post-filter) |
| ADR-008 | JWT auth + org isolation (`get_current_identity` as sole identity gateway) |
| ADR-009 | Eval leak suite + golden QA dataset (security first; RAGAS deferred to 4b) |
| ADR-010 | RAGAS harness: lazy imports, ragas 0.4.3 deprecated singleton path, `[eval-live]` extra |

---

## 8. Environment & Tooling

- **Python:** 3.11+ (CI: 3.11; dev: 3.12 recommended; 3.14 is NOT supported — triggers source-compiles in deps)
- **Dev install:** `pip install -e ".[dev]"` — pins ruff, mypy, pytest, pytest-asyncio, respx, pytest-cov to exact versions (local == CI by construction)
- **Live eval install:** `pip install -e ".[eval-live]"` — adds ragas==0.4.3 + 12 pinned peers; not required for CI
- **CI commands (in order):** `ruff check .` → `ruff format --check .` → `mypy --strict .` → `pytest -m "not slow" --cov=. --cov-report=term-missing`
- **Fresh-venv simulation** (run before any CI-touching push): `python3.12 -m venv /tmp/ci_venv && source /tmp/ci_venv/bin/activate && pip install -e ".[dev]" -q && ruff check . && ruff format --check . && mypy --strict . && pytest -m "not slow" --cov=. --cov-report=term-missing; deactivate`
- **NIM dev:** hosted API at `build.nvidia.com` (free credits); override URL/model via env vars for Phase 5 self-hosted
- **Milvus dev:** Milvus Lite (in-process); Phase 5 switches to self-hosted via `MILVUS_MODE=remote`

---

## 9. Cost & Deployment Notes

| Mode | Cost | When |
|------|------|------|
| Dev (Phases 1–4) | ~$0 | Hosted NIM credits + Milvus Lite + CPU only |
| GPU burst (Phase 5) | ~$10–30 one-time | EKS spin-up → capture proof → same-day teardown |
| Always-on demo (Mode B) | ~$15–20/mo | CPU box, hosted NIM API; the live resume demo link |

Ceiling: $100–200/mo.

---

## 10. Backlog

- [ ] **CI action bump:** `actions/checkout v4 → v5`, `actions/setup-python v5 → v6` (low urgency; do in a `chore/ci-bump` PR)
- [ ] **Live RAGAS run:** execute `python -m eval.ragas` against hosted NIM on a stable network to capture actual faithfulness/answer_relevancy/context_precision/context_recall scores; save the JSON report in `eval/ragas/reports/`
- [ ] **Phase 5 Dockerfiles:** `deploy/Dockerfile.api` (triggers the Docker CI job that was removed in PR #4)
- [ ] **Golden dataset verification:** 9 of 10 QA pairs in `eval/golden/golden_qa.jsonl` are tagged `needs-verification`; verify against the NVIDIA FY2024 10-K source

---

## 11. CI Incident History

| # | Phase | Symptom | Root cause | Fix |
|---|-------|---------|-----------|-----|
| 1 | Phase 3 fix | CI red: 4× RUF059 unused `corpus` | ruff version drift (`>=0.4.0` → CI got 0.15.17 which added RUF059) | Rename `corpus` → `_corpus`; pin all dev tools to exact versions |
| 2 | Phase 3 fix | CI exit 4: `--cov` args unrecognized | `pytest-cov` undeclared in `[dev]` | Declare + pin `pytest-cov==7.1.0` |
| 3 | Phase 3 fix | clean-venv `ModuleNotFoundError: milvus_lite` | `pymilvus` missing `[milvus_lite]` extra | Change to `pymilvus[milvus_lite]>=2.4.0` |
| 4 | Phase 3 fix | main CI red: Docker job missing `Dockerfile.api` | Premature Docker CI job (Phase 5 file doesn't exist yet) | Remove Docker job until Phase 5 Dockerfiles exist |

Phase 4b local-env saga: a Python 3.14 `.venv` triggered source-compiles for native deps (ragas peer stack); a corrupted 389 MB pip cache spammed deserialization warnings on every install; a flaky hotspot connection then killed the heavy `[eval-live]` install (DNS failures, `IncompleteRead` mid-download). Resolution: rebuilt the venv on Python 3.12, purged the cache; merged PR #8 on CI-green since the harness is proven by 22 mocked CI-safe tests; deferred the live RAGAS metrics run to a stable network or the Phase 5 GPU box. Lesson: the live RAGAS run is a quality readout, not a merge gate — CI + mocked tests are the gate.
