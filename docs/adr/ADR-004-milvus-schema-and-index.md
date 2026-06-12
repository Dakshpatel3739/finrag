# ADR-004 — Milvus Schema, Index, and Upsert Strategy

**Status:** Accepted  
**Date:** 2026-06-12  
**Scope:** retrieval/vector_store.py, ingest/pipeline.py

---

## Context

Phase 1 requires storing embedded Chunk objects in a vector database so they
can be searched in Phase 1 slice 4 (hybrid retrieval).  The FINRAG_MASTER_PLAN
mandates:

1. All Milvus fields must exist from day one — later phases must never re-create
   or ALTER the collection.
2. `allowed_roles` must be a native ARRAY field so the Phase 2 retrieval filter
   (`ARRAY_CONTAINS`) can run inside the vector search.
3. All inference (LLM, embedding, reranking) routes through NVIDIA NIM.  The
   vector store itself is Milvus (not Pinecone, Chroma, or Qdrant).

Three constraints drive the design:

- **Dev vs. Phase 5 parity** — Phases 1-4 run on a local laptop with no GPU.
  Milvus Lite (bundled in `pymilvus[milvus_lite]`) gives a fully functional
  Milvus backed by SQLite with zero server processes.  Phase 5 upgrades the
  URI env var to point at a self-hosted Milvus pod; the `pymilvus.MilvusClient`
  API is identical in both modes.
- **Security invariant** — chunk-level RBAC must filter forbidden chunks before
  they ever enter the LLM's context window.  Post-filtering (check after
  retrieval) is not acceptable.  This requires the filter to run inside the
  Milvus vector search, which in turn requires `allowed_roles` to be a
  first-class Milvus field with a type that supports `ARRAY_CONTAINS`.
- **Zero re-ingest** — altering a Milvus collection schema (in most Milvus
  versions) requires dropping and recreating the collection, which forces a
  full re-ingest of all documents.  A collection created with the complete
  schema from day one avoids this cost.

---

## Decision

### Milvus Lite in dev, full Milvus in Phase 5

`MilvusClient(uri=path)` activates Milvus Lite when the URI is a filesystem
path (e.g. `milvus_finrag.db`).  Phase 5 changes the URI env var to
`http://milvus-service:19530`; no code changes required.

This follows NVIDIA's recommended architecture for the chain-server: keep
Milvus behind an environment-variable-controlled URI, deploy the NIMs and
Milvus on Kubernetes only when proving the GPU story.

### Full schema at collection creation

All 13 fields from the Chunk model are created at collection creation, even
though only a subset are populated in Phase 1:

| Phase | Fields populated |
|-------|-----------------|
| 1 (now) | chunk_id, doc_id, doc_name, page_number, section, org_id (default), allowed_roles (default), sensitivity_level (default), text, embedding, content_type, source_modality, caption (empty) |
| 2 | org_id, allowed_roles, sensitivity_level (real values from JWT) |
| 6 | caption (VLM-generated text for chart chunks) |

**Why not add fields later?**  Milvus does not support ALTER COLLECTION to add
fields after creation (without recreating the collection).  The plan forbids
costly re-ingests.  Paying a small upfront cost (default/empty values for
Phase-2+ fields) is far cheaper than a production re-ingest when Phase 2 ships.

### allowed_roles as ARRAY(VARCHAR)

Phase 2 uses this Milvus filter expression:
```
ARRAY_CONTAINS(allowed_roles, user_role) AND org_id == "{org_id}"
```

This filter runs as a pre-filter inside the ANN vector search, meaning Milvus
evaluates it on the index's candidate set before computing distances.  Forbidden
chunks are excluded at the vector-index level — they never become retrieval
candidates, never enter the reranker, and never reach the LLM context window.

Alternatives considered:
- **VARCHAR (JSON string)** — would require `LIKE` or a UDF scan; cannot use
  `ARRAY_CONTAINS`; does not filter inside ANN search.
- **Multiple boolean fields (is_owner, is_finance, …)** — requires schema
  change for every new role; does not generalise.
- **Separate ACL table** — cannot be pushed into the Milvus vector search; forces
  post-filtering, which violates the security invariant.

### COSINE metric + AUTOINDEX

**Why COSINE?**  nv-embedqa-e5-v5 produces L2-normalised vectors.  Cosine
similarity over normalised vectors is equivalent to dot-product and is the
metric recommended by NVIDIA for NeMo Retriever embeddings.  Using L2 distance
on normalised vectors would produce equivalent ranking but with worse numeric
interpretability.

**Why AUTOINDEX?**  `AUTOINDEX` delegates the concrete index type to Milvus:
- Milvus Lite (dev): chooses HNSW.
- Zilliz Cloud (optional): AUTOINDEX maps to an optimised cloud-native index.
- Self-hosted Milvus on GPU (Phase 5): AUTOINDEX can use IVF_SQ8 or HNSW_SQ.

Hardcoding `HNSW` with tuned `M` / `efConstruction` parameters would require
re-benchmarking for each deployment mode.  AUTOINDEX handles this transparently
with acceptable defaults for the Phase 1-4 development cycle.

### Upsert semantics

`MilvusClient.upsert()` replaces a row with a matching primary key
(`chunk_id`).  `chunk_id` is a deterministic SHA-256 prefix of
`doc_id:page:index` (see `ingest/models.py`).  This means:

- Re-ingesting the same document with the same chunking parameters produces
  identical `chunk_id` values → upsert replaces the old rows cleanly.
- Re-ingesting after a text edit (which changes chunk content but not
  position) also produces the same IDs → the update is applied.
- Inserting from two concurrent workers is safe because upsert is atomic on
  the primary key.

**Consequence:** if the chunking parameters change (e.g. `chunk_size` is
increased in `system_config`), the chunk positions shift and new `chunk_ids`
are generated, leaving stale old chunks in the collection.  The recommended
practice for a parameter change is to drop the collection and re-ingest, which
is a deliberate operator action (not a code change).

---

## Consequences

**Positive:**
- Phase 2 RBAC requires no schema migration — only a change to how `org_id` and
  `allowed_roles` are populated at ingest time.
- Milvus Lite tests run fully in-process without a server, Docker, or network.
- AUTOINDEX adapts to both laptop dev and GPU production without code changes.

**Negative / accepted trade-offs:**
- `caption` is an empty string in Phase 1.  A 65 535-char VARCHAR with a mostly
  empty value is minor overhead but not zero.
- The schema has no `bm25_sparse` field yet.  BM25/sparse vectors will be added
  in the BM25 slice (Phase 1 slice 4) via `add_field` — this is the ONE
  exception to the no-ALTER rule, and it requires collection recreation.  The
  slice must document a re-ingest step.

---

## How to switch to a real Milvus server

```bash
# .env
MILVUS_URI=http://milvus.internal:19530
MILVUS_COLLECTION=finrag_chunks
```

No code changes.  `MilvusStore()` reads the URI from settings.
