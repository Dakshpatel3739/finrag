# ADR-012 — Chain-server holds long-lived MilvusStore + BM25Index in app.state, rebuilt from persisted corpus at startup

**Status:** Accepted  
**Date:** 2026-06-15  
**Authors:** FinRAG build agent

---

## Context

The FinRAG hybrid retrieval pipeline (`document_search`) requires two components:

1. **MilvusStore** — wraps MilvusClient for dense (ANN) search with RBAC filters.
2. **BM25Index** — an in-memory rank-bm25 index that provides lexical retrieval.

`BM25Index` is built from a `list[Chunk]` passed at construction time and is immutable thereafter.  Milvus holds the authoritative copy of all ingested chunks.  The two stores are currently independent: ingest writes to Milvus but the BM25 index only exists for the lifetime of an in-process ingest call.

**Problem:** on a cold boot (fresh process, no prior in-process ingest), the server has no `BM25Index` and no `MilvusStore` in memory.  Hybrid retrieval's lexical half is unavailable even though the Milvus collection is fully populated.

**Constraints considered:**

- Milvus Lite (used in phases 1–4) does not provide a native BM25/sparse-vector search API through `MilvusClient`.  The in-memory `rank-bm25` implementation is the only available lexical search path for dev.
- `MilvusStore` has no "stream all chunks" API.  A new method (`list_all_chunks`) is needed to scan the persisted collection and reconstruct Chunk objects for BM25 bootstrap.
- BM25 index rebuilds are O(N) in corpus size — acceptable at startup (once), not acceptable per-request.
- The BM25 corpus must stay in memory for the lifetime of the process.  Rebuilding per-request would be prohibitively slow and would defeat the purpose of lexical retrieval.

---

## Decision

**The chain-server holds a long-lived `MilvusStore` and `BM25Index` in `FastAPI.state`, bootstrapped from the persisted Milvus corpus during the ASGI lifespan.**

Concretely:

### 1. `MilvusStore.list_all_chunks(org_id=None)`

A new method on `MilvusStore` scans the collection with `MilvusClient.query()`, paginates at 16 384 rows per page (Milvus Lite limit), and reconstructs `Chunk` objects from scalar fields only (`embedding=None`; BM25 does not need vectors).  When `org_id` is given it filters to one tenant; when `None` it returns the full corpus.

The filter expression `'chunk_id != ""'` is used for the "all rows" case, exploiting the schema invariant that `chunk_id` is always a non-empty string.

### 2. Lifespan bootstrap

In the `lifespan` async context manager:

```python
store = MilvusStore()
corpus = store.list_all_chunks()   # O(N) Milvus scan
bm25   = build_bm25_index(corpus)  # O(N) BM25 build
_app.state.store        = store
_app.state.bm25         = bm25
_app.state.corpus_size  = len(corpus)
```

**Empty-corpus tolerance:** `build_bm25_index([])` produces a valid `BM25Index` that always returns `[]` from `.search()`.  The server boots and `/query` returns the `"I cannot answer"` refusal rather than a 500.  A structured warning `lifespan.empty_corpus` is logged so operators know ingest hasn't run.

**Failure tolerance:** the entire bootstrap is wrapped in `try/except`.  If `MilvusClient` fails to connect (network error, corrupt db file, etc.), `lifespan.store_init_failed` is logged with the error and `yield` still runs — the app boots.  `/query` then returns a clean 503 via `get_store` / `get_bm25`.

### 3. FastAPI dependency functions

```python
def get_store(request: Request) -> MilvusStore: ...
def get_bm25(request: Request)  -> BM25Index:  ...
```

Both functions are **module-level** (not inside `create_app`) so tests can override them via `app.dependency_overrides[get_store] = lambda: my_test_store`.  Each raises `HTTPException(503)` with a descriptive message if the corresponding state attribute is absent.

### 4. Test-mode behaviour (`skip_secret_check=True`)

When `skip_secret_check=True`, the lifespan skips the Milvus bootstrap entirely.  Tests inject `store` and `bm25` via `dependency_overrides`, keeping unit tests fast and isolated (no `milvus_finrag.db` side-effect in the project directory).

---

## Consequences

### Positive

- **Cold-boot correctness:** hybrid retrieval works immediately after a process restart, provided the Milvus collection was populated by a prior ingest.
- **Graceful degradation:** an empty corpus or a failed Milvus connection produces a clean refusal / 503, not a 500 or a process crash.
- **Testability:** module-level dependency functions make injection trivial.
- **Security:** `get_store` / `get_bm25` raise 503 on uninitialised state rather than `AttributeError`, giving callers a predictable, safe failure mode.

### Negative / trade-offs

- **Stale BM25 after ingest:** documents ingested after the server started are in Milvus (dense search picks them up immediately) but not in the in-memory BM25 index.  A full rebuild requires a process restart.  Mitigation: Phase 5 can add a `/admin/rebuild-bm25` endpoint or a background task that rebuilds on a schedule.  For the current phase (phases 1–4) this is accepted: ingest is a batch operation and BM25 staleness is documented.
- **Memory footprint:** the BM25 index holds all chunk texts in RAM.  At 512-token chunks, a 10 000-chunk corpus is approximately 40 MB — acceptable on any modern server.
- **Startup latency:** a large corpus (100 000+ chunks) adds several seconds to startup.  Acceptable for a long-lived server process; not a concern for the current dev/demo scale.

---

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Rebuild BM25 per-request | O(N) per request is prohibitively slow and defeats the purpose of pre-built lexical index. |
| Persist BM25 index to disk (pickle) | Adds a serialisation/deserialisation step, pickle is not type-safe, and the on-disk file can go stale if chunks are added without a rebuild.  Simpler to rebuild from the canonical Milvus source. |
| Milvus native sparse/BM25 | Not available in Milvus Lite (phases 1–4).  Planned for Phase 5 migration. |
| Store corpus in a separate relational DB | Doubles the write path at ingest time and adds a sync problem.  Milvus is already the canonical chunk store. |
| Request-scoped store + BM25 | FastAPI creates a new instance per request, rebuilding BM25 on every call.  Equivalent to rebuild-per-request above. |
