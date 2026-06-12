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
