# FinRAG — Agent Operating Rules

## Source of truth
- FINRAG_MASTER_PLAN.md and FINRAG_NVIDIA_ARCHITECTURE.md define the project. Read them if context is missing.
- plan.md tracks the current phase.

## Boundaries
- Claude Code owns RAG logic: ingest/, retrieval/, rbac/, generation/, eval/, api/.
- Codex owns infra/boilerplate: deploy/, Dockerfiles, .github/workflows/, K8s/Helm YAML. Do not write infra YAML unless told.

## Engineering log — MANDATORY every slice
- CLAUDE_CHANGES.md is the change & incident log. At the END of EVERY slice, before committing, append:
  1. a CHANGELOG entry (what shipped, why, files, commits), and
  2. an INCIDENT entry for any critical error (symptom, root cause, fix, fallback) — or "No incidents."
- This update goes in the slice's own commits. Never skip it. Never rewrite merged entries.

## Workflow
- Trunk-based: short-lived branch per slice (feat/…, fix/…, chore/…), never commit to main directly.
- Conventional Commits on every commit.
- Before committing any slice: ruff check, ruff format --check, mypy --strict ., pytest — all must be green.
- Never commit .env or the FINRAG_*.md planning docs.

## Conventions
- Python 3.11+, full type hints, mypy --strict clean, pydantic v2 at boundaries.
- Files <300 lines, single responsibility. Docstrings on public functions. WHY-comments on non-obvious decisions.
- Tests ship in the same PR as the feature. RBAC gets adversarial tests.
- ADR in docs/adr/ for every non-trivial architecture decision.

## CI Hygiene Rules (MANDATORY — learned from 4 real CI incidents)

These exist because CI passed locally but failed on GitHub four times. Follow them on every CI-touching change:

1. "Green locally" ≠ "green in CI." Only `gh pr checks <PR>` showing green on the actual PR counts. Branch protection on main enforces this — main requires the `ruff + mypy + pytest` check to pass before merge.
2. Pin dev tool versions in pyproject.toml with `==` (ruff, mypy, pytest, pytest-asyncio, respx, pytest-cov). Version drift between local and CI caused incident #1 (a newer ruff in CI flagged RUF059 that local ruff didn't).
3. Declare EVERY dependency in pyproject.toml — including extras like `pymilvus[milvus_lite]`. A package installed globally on the dev machine but undeclared passes locally and fails on the clean CI runner. This caused incidents #2 (`pytest-cov`) and #3 (`pymilvus[milvus_lite]`).
4. Fresh-venv simulation before ANY CI-touching push:
   `python3.12 -m venv /tmp/ci_venv && source /tmp/ci_venv/bin/activate && pip install -e ".[dev]" -q && ruff check . && ruff format --check . && mypy --strict . && pytest -m "not slow" --cov=. --cov-report=term-missing; deactivate`
   Run it WITHOUT a `.env` present (CI has none — `.env` is gitignored). A clean venv with only declared deps faithfully replicates the CI runner and catches undeclared deps that global installs mask.
5. Never add a CI job that references a file which doesn't exist yet (e.g. a Docker build job before Dockerfiles exist). It gets skipped on PRs but RUNS and FAILS on push-to-main. Caused incident #4. Add such jobs only when the referenced files exist (Docker → Phase 5).
6. One stream at a time: a red main is "stop the line." Fix and merge the red-main fix before starting new feature work. Running two branches' work in parallel caused a branch tangle.
7. CI runs pytest with `-m "not slow"` — live NIM tests (which need an API key the runner doesn't have) MUST be marked `@pytest.mark.slow` so they're excluded from CI.

## CI Incident Log (root-cause summary)

| # | Symptom | Root cause | Fix |
|---|---------|-----------|-----|
| 1 | CI red, 4× RUF059 unused `corpus` | ruff version drift (CI newer) | underscore-prefix + pin tool versions |
| 2 | CI exit 4, unrecognized `--cov` args | `pytest-cov` undeclared | declare + pin pytest-cov |
| 3 | clean-venv ModuleNotFoundError milvus_lite | `pymilvus` missing `[milvus_lite]` extra | declare pymilvus[milvus_lite] |
| 4 | main CI red, Docker job missing Dockerfile.api | premature Docker job (Phase-5 file) | remove Docker job until Phase 5 |
| 5 | mypy unused-ignore in ingest/parser.py | docling-core stubs updated; `# type: ignore[attr-defined]` no longer suppresses anything | remove stale comment |

The full per-incident detail (symptom, root cause, fix, prevention) lives in CLAUDE_CHANGES.md. When you hit a NEW CI failure, add it to both the CLAUDE_CHANGES.md incident log AND this table.
