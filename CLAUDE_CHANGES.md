# FinRAG — Engineering Change & Incident Log

> Maintained by the build agent. Every non-trivial change and every critical error gets an entry. Newest first.

## How this file is maintained
- Every code change of substance gets a CHANGELOG entry (what, why, files, commit).
- Every critical error / failed run / blocker gets an INCIDENT entry (symptom, root cause, fix, fallback).
- Entries are append-only and never rewritten after a slice is merged.
- This file is committed alongside the work it describes, in the same PR.

---

## CHANGELOG

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
