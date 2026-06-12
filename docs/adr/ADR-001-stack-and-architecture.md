# ADR-001 — Stack and Architecture Decisions

**Status:** Accepted  
**Date:** 2026-06-12  
**Scope:** Whole project

---

## Context

FinRAG is a portfolio project proving production RAG engineering at a senior/staff level. The choices here optimize for:

1. Resume signal (NVIDIA GPU stack, enterprise-grade security model, real eval)
2. Demo reliability (always-on live link after the GPU burst phase)
3. Cost discipline (near $0 dev, ~$10-30 GPU burst, ~$15-20/mo always-on)

---

## Decisions

### 1. NVIDIA NIM for all inference (embedding + reranking + LLM)

**Decision:** Use NVIDIA NeMo Retriever Embedding NIM, NVIDIA Reranking NIM, and a hosted LLM NIM (llama-3.1-8b-instruct) for all inference. Dev uses the hosted NIM API at build.nvidia.com. Phase 5 self-hosts all three on EKS GPU.

**Why:** The resume signal is the full GPU stack. Any other provider (OpenAI, Gemini, Cohere) removes the NVIDIA NIM deploy story. Hosted NIM API in dev gives free credits so cost is near zero before Phase 5.

**Consequences:** NIM API is OpenAI-compatible, so we use the `openai` Python SDK pointing at NIM endpoints. Switching from hosted → self-hosted is an env var change only.

---

### 2. Milvus as the vector store

**Decision:** Milvus Lite (local file) in dev, self-hosted on EKS in Phase 5.

**Why:** Milvus supports sparse vectors natively (needed for BM25 hybrid retrieval), has a production-grade `ARRAY_CONTAINS` filter operator (our RBAC mechanism), and runs as a single embedded file in dev with no infrastructure overhead. Zilliz Cloud (managed Milvus) is an easy drop-in for the always-on demo.

**Alternatives considered:**
- pgvector: no native sparse support, no array-contains operator
- Pinecone/Weaviate: proprietary, no self-hosted option matching Phase 5 requirements
- Qdrant: good alternative but fewer companies deploy it alongside NVIDIA stacks

---

### 3. RBAC as a Milvus metadata filter — not in the prompt

**Decision:** The `allowed_roles` field is an `array<string>` denormalized onto every chunk. Every retrieval query includes a Milvus WHERE clause: `ARRAY_CONTAINS(allowed_roles, user_role) AND org_id == user_org_id`. Forbidden chunks are excluded before any vector scoring.

**Why (security invariant):** If RBAC were enforced in the LLM prompt ("ignore any chunks not allowed for HR"), it would be defeatable by prompt injection. Filtering must happen at the database level so forbidden chunks physically never enter the context window. This is the only place that provides a security boundary.

**Why denormalized:** A separate ACL join table would require a join at query time inside the vector search, which Milvus does not support. Denormalizing the roles onto the chunk trades some storage for a correct, fast, single-pass filter.

**Consequences:** Changing a chunk's permissions requires re-upsert. Acceptable: permission changes are rare; re-upsert is O(changed chunks), not O(all chunks).

---

### 4. Hybrid retrieval: BM25 + dense vectors + RRF fusion

**Decision:** Retrieve candidates with both BM25 (sparse, lexical) and dense (NeMo embedding) separately, then fuse with Reciprocal Rank Fusion (RRF, k=60), then rerank the top-N fused results with a cross-encoder NIM.

**Why:** Dense retrieval misses exact-match terms (ticker symbols, legal clause numbers, specific dollar figures). BM25 misses semantic similarity. RRF is a robust, parameter-light fusion method that consistently outperforms either alone on heterogeneous document types like financial filings. The cross-encoder reranker then re-scores the fused top-N with full query–chunk attention, recovering precision.

**Alternatives considered:**
- Dense only: insufficient recall for financial documents with specific named entities
- Late-interaction (ColBERT): higher quality but no NIM offering and GPU-intensive at index time

---

### 5. Docling for PDF parsing

**Decision:** Docling for PDF → markdown conversion, with tables extracted as markdown tables (not ignored or flattened).

**Why:** Tables in financial filings (income statements, segment breakdowns) carry critical information. Docling preserves table structure as markdown, which embeds well and renders legibly in citations. Alternative (pypdf, pdfminer) loses table structure.

---

### 6. Runtime-tunable config via SQLite system_config

**Decision:** Retrieval tuning parameters (top_k, rerank_n, chunk_size, rrf_k) are stored in a SQLite `system_config` table with typed accessors. Secrets and infra settings remain in env vars.

**Why:** Being able to tune retrieval quality without a redeploy is important for a RAG system where the right parameters depend on the document corpus. Changes are auditable (DB row with a key). In Phase 5 this can be promoted to a Postgres table or a config service.

---

### 7. Two-mode deploy, one codebase

**Decision:** `DEPLOY_MODE` env var switches between `mode_a_gpu` (3 NIMs on EKS) and `mode_b_cpu` (hosted NIM API on a cheap CPU box). No code differences between modes.

**Why:** The GPU burst (Mode A) exists solely to capture resume proof (nvidia-smi, HPA scaling, Grafana dashboards) and then tear down to control cost. The always-on demo (Mode B) runs indefinitely at low cost. One codebase avoids drift between the two environments.
