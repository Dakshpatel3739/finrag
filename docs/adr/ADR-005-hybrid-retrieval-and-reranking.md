# ADR-005 — Hybrid Retrieval and Reranking

**Status:** Accepted  
**Date:** 2026-06-12  
**Scope:** retrieval/bm25.py, retrieval/fusion.py, retrieval/reranker.py, retrieval/search.py, retrieval/vector_store.py (dense_search)

---

## Context

Phase 1 slice 4 turns a query string into a ranked list of relevant chunks ready for
the generation step.  The FINRAG_MASTER_PLAN mandates:

1. Hybrid retrieval: BM25 lexical + dense vector + RRF fusion — not dense-only.
2. Cross-encoder reranking via NVIDIA NIM before chunks reach the LLM.
3. RBAC filters at retrieval time, inside the Milvus query — never in the prompt.
4. All NIM endpoints env-driven; swapping models = env change, no code change.
5. config-driven `top_k`, `rerank_n`, `rrf_k` — never hardcoded.

---

## Decision

### 1. Retrieval pipeline

```
query → embed (input_type="query") → dense_search (top_k)
                                   → bm25_search (top_k)
                                   → rrf_fuse → rerank (rerank_n) → chunks
```

Each stage is a separate function with a well-defined interface so any stage
can be upgraded, swapped, or evaluated in isolation.

### 2. Dense search with filter_expr (Phase 2 RBAC hook)

`MilvusStore.dense_search(query_vector, top_k, filter_expr=None)`

The `filter_expr` parameter accepts a Milvus boolean expression string and
passes it directly to `MilvusClient.search(filter=...)`.  This means the filter
runs **inside** the ANN search — not as a post-filter — so forbidden chunks are
excluded at the index level and never enter the candidate pool.

Phase 2 will call:
```python
store.dense_search(
    query_vector,
    top_k,
    filter_expr='org_id == "{org_id}" AND ARRAY_CONTAINS(allowed_roles, "{role}")',
)
```

Phase 1 passes `filter_expr=None` (unrestricted).

The `filter_expr` parameter also threads through `document_search`, so the
extension point is one argument at the API boundary — nothing deeper needs to change.

### 3. BM25 lexical retrieval (rank-bm25, in-memory)

**Why in-memory BM25 instead of Milvus native sparse:**
Milvus 2.4 supports sparse/BM25 vectors natively, but Milvus Lite (used in Phases
1-4 dev) does not expose them through the MilvusClient API.  rank-bm25 gives a
correct BM25Okapi implementation that runs in-process with zero server overhead and
zero schema changes.

Phase 5 / production can swap `BM25Index` for Milvus native BM25 sparse vectors:
1. Add a sparse vector field to the Milvus schema.
2. Tokenise + sparsify texts at ingest time.
3. Replace `bm25_index.search()` with a Milvus sparse-vector search query.
4. Keep the same `(chunk_id, score)` interface so `rrf_fuse` is unchanged.

**Tokenisation:** whitespace `.lower().split()`.  Sufficient for financial documents
where queries and passages share vocabulary.  Upgrade (spaCy, tiktoken) is a
drop-in change inside `BM25Index.__init__()`.

**Index lifetime:** built once per ingest batch; immutable.  Phase 2 scopes the
index to the authorised corpus at request time (or rebuilds per-org at startup).

### 4. RRF fusion

`rrf_fuse(dense_ids, bm25_ids, k=60) -> list[str]`

Formula: `score(d) = Σ_r 1 / (k + rank_r(d))`, ranks 1-indexed.

**Why RRF over weighted score combination:**
Dense cosine scores and BM25 scores live in different numerical ranges and
distributions.  A weighted combination requires per-corpus calibration of α.
RRF uses only rank positions — calibration-free and robust across system pairs.
(Cormack, Clarke & Buettcher 2009.)

**Why k=60:** The original RRF paper recommends k=60 as a robust default.
It is exposed in `system_config` (key `rrf_k`, default 60) and can be tuned
without redeploy.

### 5. Reranking NIM

`rerank(query, chunks, top_n) -> list[Chunk]`

The reranker calls `{NIM_RERANK_BASE_URL}/reranking` with:
```json
{"model": "<NIM_RERANK_MODEL>",
 "query": {"text": "<query>"},
 "passages": [{"text": "<chunk_text>"}, ...]}
```
and sorts by `logit` score descending.

**Why a separate reranking step:**
Bi-encoder embedding models (like nv-embedqa-e5-v5) encode query and passage
independently — fast at retrieval scale, but they miss nuanced query-passage
interactions.  A cross-encoder reranker (nv-rerankqa-mistral-4b-v3) sees both
query and passage at once and produces far more accurate relevance scores.
The standard pattern: cheap bi-encoder retrieves `top_k` candidates, expensive
cross-encoder reranks to `rerank_n` — best of both worlds.

**Model / URL env-driven:**  `NIM_RERANK_BASE_URL` and `NIM_RERANK_MODEL` are
env vars read from settings.  In Phase 5, these point to the self-hosted reranking
NIM pod.  Swapping to a different reranking model = one env var change.

**Retry strategy:** mirrors `ingest/nim_client.py` — 429/5xx → exponential backoff
(1s, 2s, 4s), max 3 retries, then `RerankError`.  Non-retryable 4xx raises
immediately.

### 6. input_type="query" for query embedding

WHY this is a dedicated note in the ADR:
`nv-embedqa-e5-v5` is an asymmetric QA model.  Document chunks are embedded at
ingest time with `input_type="passage"`.  Using `input_type="passage"` for queries
produces query vectors in a different subspace, making cosine distances meaningless
and silently destroying recall.  This is the most common production mistake with
asymmetric NeMo Retriever models.

`document_search` always passes `input_type="query"` to `embed_texts`.  The
`test_embed_called_with_input_type_query` test guards against regression.

### 7. config-driven parameters

| Parameter | system_config key | Default | Purpose |
|-----------|-------------------|---------|---------|
| dense candidate set | `top_k` | 20 | number of chunks from dense + BM25 |
| rerank shortlist | `rerank_n` | 5 | chunks returned after reranking |
| RRF smoothing | `rrf_k` | 60 | RRF k constant |

`document_search` calls `init_config_db` + `get_config` at entry, so parameters
are always current without process restart.

---

## Alternatives Considered

### Dense-only retrieval (no BM25)
- Simpler but misses exact-match queries where a key term (e.g. a ticker symbol
  or specific line-item name) appears verbatim in the document.
- BM25 adds ~2ms in-process latency; the benefit is significant for financial docs
  where users ask for exact figures or section titles.

### Score normalisation + weighted sum instead of RRF
- Requires per-corpus calibration.  RRF is calibration-free and consistently
  outperforms weighted sum across benchmarks.
- Weighted sum is a future option for Phase 4 eval-driven tuning.

### Post-retrieval RBAC filter (Python-side)
- Violates the non-negotiable invariant: "forbidden chunks must never enter the
  LLM context window."
- Post-filter can be defeated by prompt injection if the check happens after the
  LLM has already seen the chunk.  The filter must run inside Milvus.

---

## Consequences

**Positive:**
- Phase 2 RBAC requires only one argument change at the API boundary
  (`filter_expr` in `document_search`); nothing inside the pipeline changes.
- BM25 and dense search can each be evaluated and improved independently.
- Swapping the reranking model = one env var, zero code changes.
- RRF k is runtime-tunable without redeploy.

**Negative / accepted trade-offs:**
- BM25 index is in-memory and must be rebuilt after each ingest batch.  For Phase
  1-4 corpus sizes (<100K chunks) this is negligible.  Phase 5 replaces with Milvus
  native sparse.
- Each `document_search` call pays two NIM round trips (embed + rerank).  Latency
  is acceptable for interactive use; Phase 5 can batch or cache embeddings.
