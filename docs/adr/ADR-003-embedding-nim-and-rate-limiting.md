# ADR-003 — Embedding NIM, Asymmetric Input Types, and Rate Limiting

**Status:** Accepted  
**Date:** 2026-06-12  
**Scope:** ingest/nim_client.py, ingest/embedder.py

---

## Context

Phase 1 requires converting text chunks into dense float vectors so they can be
stored in Milvus and searched with cosine similarity.  The architecture mandates
NVIDIA NIM exclusively (no OpenAI/Gemini).  The chosen embedding model is
`nvidia/nv-embedqa-e5-v5` (NeMo Retriever Embedding NIM), accessible via
the NVIDIA hosted API at `https://integrate.api.nvidia.com/v1`.

Three constraints shape the design:

1. **Asymmetric model** — `nv-embedqa-e5-v5` is trained with separate projection
   heads for documents ("passage") and search queries ("query").  Passage and
   query vectors live in different learned subspaces; computing cosine similarity
   between a passage vector and a query vector produces meaningless scores.
   Every call to `/embeddings` must carry an `input_type` field set to either
   `"passage"` or `"query"`.

2. **Free-tier rate limit** — the NVIDIA hosted API enforces 40 requests per
   minute (RPM).  A naive loop over individual text chunks would immediately
   saturate this limit.

3. **Reliability** — transient 429 (rate limit) and 5xx (server error) responses
   must not surface as unhandled exceptions.  The embedding step should be
   self-healing within a bounded retry budget.

---

## Decision

### Model: nvidia/nv-embedqa-e5-v5

`nv-embedqa-e5-v5` is NVIDIA's production QA embedding model, based on
E5-large-v2 with NeMo-specific fine-tuning for retrieval tasks.  It produces
1024-dimensional vectors.

Alternatives considered:
- `nvidia/nv-embed-v1` — general-purpose, symmetric (no input_type distinction).
  Rejected: lower accuracy on financial QA benchmarks; does not require the
  retrieval-specific passage/query separation that this architecture uses.
- OpenAI `text-embedding-3-large` — violates the "NIM only" architecture invariant.

### Explicit input_type parameter

`nim_client.embed_texts()` and `embedder.embed_chunks()` both expose `input_type`
as an explicit, required-to-name parameter rather than inferring it.  This is
intentional:

- **Passage** (`input_type="passage"`) — used when ingesting document chunks.
- **Query** (`input_type="query"`) — used by the retrieval slice when embedding
  user search queries.

Silent defaults would risk sending query vectors to a passage-indexed Milvus
collection or vice versa.  The explicit parameter makes every call site
self-documenting and auditable.

### Batching

Texts are split into batches of up to `_DEFAULT_BATCH_SIZE = 50` per HTTP
request.  The NVIDIA free-tier limit is approximately 50 texts per request;
50 was chosen as the ceiling to avoid request-body-too-large errors while
minimising the total number of round trips.

Batching is implemented in `nim_client.embed_texts()`, not in `embedder.embed_chunks()`,
so the batching logic is testable independently and can be reused when the
retrieval slice calls `embed_texts(..., input_type="query")`.

### Rate limiting: proactive inter-request sleep

After each batch request (except the last), `embed_texts` sleeps for
`_MIN_INTERVAL_S = 60 / 36 ≈ 1.667 seconds`.  This paces requests at 36 RPM —
10% below the 40 RPM cap.

**Why proactive throttling instead of pure retry?**
- 429 retries use exponential backoff starting at 1 second, doubling per attempt.
  A burst of 40 requests in one second would trigger 40 simultaneous 429s, each
  needing a retry — burning 2× the total requests and adding latency.
- Proactive sleep costs one constant delay per batch.  For the typical ingest
  volume (tens to hundreds of chunks), this is 1–5 seconds of total added
  latency, far preferable to a retry cascade.
- The 36 RPM budget leaves headroom for a single concurrent caller without
  immediately hitting the limit.

**Why `asyncio.sleep` instead of a semaphore?**
In Phase 1, ingest is a single-tenant, single-process operation.  A simple sleep
is correct and easy to test (mock `asyncio.sleep`).  When Phase 5 adds concurrent
API workers, a token-bucket semaphore on the `httpx.AsyncClient` will replace
the sleep without changing callers.

### Retry strategy

Retryable conditions: `429 Too Many Requests`, `5xx Server Error`,
`httpx.TimeoutException`, `httpx.NetworkError`.

Non-retryable: all other 4xx (e.g. 401 Unauthorized, 400 Bad Request) — these
indicate a configuration or request-shape problem that retrying will not fix.

Backoff: `1s → 2s → 4s` (base × 2^attempt).  Maximum 3 attempts total.  After
exhausting retries, `EmbeddingError` is raised.

**Why `EmbeddingError` extends `IngestError` (not `Exception`)?**
Callers can catch `IngestError` to handle any ingest-pipeline failure uniformly,
or catch `EmbeddingError` to handle embedding specifically (e.g. to fall back to
a sparse-only retrieval mode in a degraded state).  Bare `Exception` would be
invisible to intermediate layers.

### Order guarantee

A pre-allocated `results: list[list[float] | None]` list is indexed by the
original text position.  Each batch's NIM response is sorted by the response
`index` field before being slotted back.  This guarantees `chunk[i]` receives
`vector[i]` even if:
- the NIM reorders items within a batch response, or
- a future implementation parallelises batch requests.

`embedder.embed_chunks()` additionally validates that `len(vectors) == len(chunks)`
and that all vectors share the same dimension before writing to the Chunk objects.

---

## Consequences

**Positive:**
- Ingest tests run without network (embed_texts is mocked).
- The retrieval slice can call `embed_texts(..., input_type="query")` without
  any new infrastructure — the same client handles both passage and query paths.
- Rate-limiting and retry are fully unit-tested without sleeping (asyncio.sleep
  is mocked in tests).

**Negative / accepted trade-offs:**
- `_MIN_INTERVAL_S ≈ 1.667 s` of added latency per batch of 50 chunks means
  a 500-chunk ingest takes ~16 seconds of sleep.  This is acceptable in Phase 1
  (single user, background job).  Phase 5 self-hosted NIMs have no RPM cap.
- The 50-text batch ceiling is empirical; if NVIDIA raises or lowers it, update
  `_DEFAULT_BATCH_SIZE` in `nim_client.py`.

---

## How to run the live test

```
NIM_API_KEY=nvapi-... pytest ingest/test_nim_client.py -m slow -v
```

Expected output: two non-empty float vectors of equal length (1024 dimensions
for nv-embedqa-e5-v5).
