# FinRAG — Engineering Change & Incident Log

> Maintained by the build agent. Every non-trivial change and every critical error gets an entry. Newest first.

## How this file is maintained
- Every code change of substance gets a CHANGELOG entry (what, why, files, commit).
- Every critical error / failed run / blocker gets an INCIDENT entry (symptom, root cause, fix, fallback).
- Entries are append-only and never rewritten after a slice is merged.
- This file is committed alongside the work it describes, in the same PR.

---

## CHANGELOG

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

### [2026-06-12] Phase 1 slice 3 — mypy generator return type on pytest fixture
- **Symptom:** `mypy --strict` error: "The return type of a generator function should be 'Generator' or one of its supertypes [misc]" in `retrieval/conftest.py`.
- **Where:** retrieval/conftest.py, `milvus_db` fixture.
- **Root cause:** Fixture uses `yield` making it a generator function; annotated as `-> Path` instead of `-> Generator[Path, None, None]`.
- **Fix:** added `from collections.abc import Generator` and changed return type to `Generator[Path, None, None]`.
- **Fallback / prevention:** any yield-based pytest fixture must use `Generator[YieldType, None, None]` (or `Iterator[YieldType]`) as the return annotation under `--strict`.
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
