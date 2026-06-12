# FinRAG — Build Plan

> Living document. Update the CURRENT marker as phases complete.

---

## Architecture Invariants (non-negotiable)

1. **RBAC filters run inside the Milvus vector query — NEVER in the prompt.** Forbidden chunks must never enter the LLM context window. The filter is a metadata WHERE clause using `ARRAY_CONTAINS(allowed_roles, user_role)`.
2. `allowed_roles` is an **ARRAY** on each chunk — Milvus `ARRAY_CONTAINS` filter. No separate ACL table.
3. Roles are denormalized onto every chunk so the filter executes at retrieval time.
4. All embeddings, reranking, and LLM inference via **NVIDIA NIM** (no OpenAI/Gemini). Dev → hosted NIM API (build.nvidia.com); Phase 5 → self-hosted on EKS GPU.
5. One codebase, two deploy modes switched by env vars: Mode A GPU burst (EKS), Mode B always-on CPU.
6. GitHub is the single source of truth. Every phase ships as a PR.

---

## Chunk Metadata Schema (set once, never retrofitted)

| Group | Field | Type | Notes |
|-------|-------|------|-------|
| Identity | chunk_id | string (PK) | UUID |
| Identity | doc_id | string | parent document |
| Identity | doc_name | string | filename for citations |
| Identity | page_number | int | for citations |
| Identity | section | string | heading/section |
| Access | org_id | string | tenant isolation |
| Access | allowed_roles | array\<string\> | RBAC gate |
| Access | sensitivity_level | string | public/internal/restricted |
| Retrieval | text | string | chunk text |
| Retrieval | embedding | float vector | NeMo NIM |
| Retrieval | sparse/bm25 | sparse | hybrid lexical |
| Multimodal | content_type | string | text/table/chart |
| Multimodal | source_modality | string | extraction method |
| Multimodal | caption | string | VLM caption (Phase 6) |

---

## Phases

### Phase 1 — Core Text RAG Loop ← **CURRENT**
Single tenant, no auth. End-to-end: ingest → chunk → embed → Milvus → hybrid retrieve → rerank → cited answer.

- [ ] PDF parsing (text + tables-as-markdown via Docling)
- [ ] Recursive/semantic chunking; all schema fields tagged (dummy org/roles)
- [ ] Embed via NeMo Retriever embedding NIM
- [ ] Store in Milvus Lite (all schema fields from day one)
- [ ] Hybrid retrieval: BM25 + dense + RRF fusion
- [ ] Rerank with reranking NIM (cross-encoder)
- [ ] Generate with LLM NIM, enforce citations (doc_name + page_number)
- [ ] Tests: unit for each module + integration for the full pipeline

**Demo:** upload a 10-K, ask a question, get a cited answer.

### Phase 2 — Chunk-Level RBAC
- [ ] Populate real org_id + allowed_roles + sensitivity_level at ingest
- [ ] Metadata filter in Milvus query (ARRAY_CONTAINS + org_id)
- [ ] Adversarial leak tests: HR-role queries must never retrieve restricted chunks

### Phase 3 — Auth + Multi-Tenancy
- [ ] JWT with role claims, org isolation, role assignment
- [ ] Demo: two orgs, two roles, isolated data

### Phase 4 — Evaluation
- [ ] Golden QA dataset (financial Qs + ground truth)
- [ ] RAGAS: faithfulness, answer relevance, context precision/recall
- [ ] RBAC leak-test suite (automated adversarial)
- [ ] Deliverable: eval report with scores

### Phase 5 — GPU Deployment (BURST)
- [ ] 3 NIMs on EKS via NIM Operator
- [ ] Milvus on cluster, Prometheus + Grafana (DCGM GPU metrics), HPA
- [ ] Locust load test → capture HPA scaling
- [ ] Capture: nvidia-smi, dashboards, NIM logs, scaling screenshots → TEAR DOWN

### Phase 6 — Multimodal v2 (stretch)
- [ ] Chart images → VLM caption → embed caption as text (content_type='chart')

### UI (after Phase 3)
Login, document upload + loaded-docs view, query box, cited-answer display with source highlighting, role/admin panel. Built with Claude Design, connects to FastAPI.
