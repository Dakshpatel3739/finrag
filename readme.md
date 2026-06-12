# FinRAG

A production-grade multi-tenant financial document RAG platform with chunk-level RBAC, built on the NVIDIA NIM stack and deployed on AWS GPU.

## What it does

An org owner uploads financial PDFs (10-Ks, earnings reports, internal memos). The system parses, chunks, and indexes them with full metadata. Users query in natural language and receive cited, grounded answers — with access strictly gated by role at retrieval time. Sensitive chunks (e.g. salary tables) are physically excluded from the vector query for unauthorized roles; they never enter the LLM context.

## Architecture

```
PDF Upload
    │
    ▼
[Ingest — Docling]
  text + tables-as-markdown
    │
    ▼
[Chunker]
  recursive/semantic split
  tags: chunk_id, doc_id, doc_name, page_number, section,
        org_id, allowed_roles[], sensitivity_level,
        content_type, source_modality
    │
    ├──────────────────────────────┐
    ▼                              ▼
[NeMo Retriever Embedding NIM]  [BM25 Index]
  dense float vectors             sparse lexical
    │                              │
    └──────────┬───────────────────┘
               ▼
         [Milvus]
   vector store + metadata filter
   RBAC: ARRAY_CONTAINS(allowed_roles, role)
         + org_id == user_org_id
               │
               ▼
    [Hybrid RRF Fusion]
    dense + BM25 results merged
               │
               ▼
   [Reranking NIM — cross-encoder]
               │
               ▼
    [LLM NIM — llama-3.1-8b-instruct]
    citations enforced (doc_name + page_number)
               │
               ▼
          Cited Answer
```

**Security invariant:** the RBAC filter is a Milvus WHERE clause applied before any vectors are scored. Forbidden chunks are excluded at the database level — they never appear in results, never enter the reranker, and never reach the LLM prompt.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| PDF parsing | Docling |
| Embedding | NVIDIA NeMo Retriever Embedding NIM |
| Reranking | NVIDIA Reranking NIM (cross-encoder) |
| LLM | NVIDIA NIM — llama-3.1-8b-instruct |
| Vector store | Milvus Lite (dev) / self-hosted (Phase 5) |
| Hybrid retrieval | BM25 + dense + RRF fusion |
| API | FastAPI + pydantic v2 |
| Auth | JWT with role claims |
| Eval | RAGAS |
| Lint/types | ruff + mypy --strict |
| Tests | pytest |
| CI | GitHub Actions |
| Observability | structlog + Prometheus/Grafana (Phase 5) |
| GPU deploy | EKS + NIM Operator + Helm + HPA + DCGM (Phase 5) |

## Deploy Modes

| Mode | Description | Cost |
|------|-------------|------|
| A — GPU burst | 3 NIMs on EKS, Prometheus/Grafana/HPA, Locust load test, capture proof, tear down | ~$10-30 one-time |
| B — always-on | Hosted NIM API on CPU box | ~$15-20/mo |

## Getting Started

### Prerequisites
- Python 3.11+
- Docker
- A [build.nvidia.com](https://build.nvidia.com) API key (free credits for dev)

### Setup

```bash
# Clone and enter
git clone https://github.com/<your-org>/finrag
cd finrag

# Install deps
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your NIM API key, Milvus connection, etc.

# Run tests
pytest

# Start API
uvicorn api.main:app --reload
```

## Project Structure

```
finrag/
├── plan.md              # phases + architecture invariants
├── readme.md            # this file
├── .env.example         # every required key, documented
├── pyproject.toml       # deps + ruff + mypy + pytest config
├── .github/workflows/   # CI: ruff + mypy + pytest on every PR
├── docs/adr/            # architecture decision records
├── config/              # system_config schema + get_config()
├── ingest/              # PDF → chunks (Docling)
├── retrieval/           # hybrid BM25 + dense + RRF
├── rbac/                # metadata filter builder + role logic
├── generation/          # LLM NIM + citation enforcement
├── eval/                # RAGAS + RBAC leak-test suite
├── api/                 # FastAPI app
├── deploy/              # Dockerfiles + K8s/Helm (Phase 5)
└── data/                # sample 10-Ks (gitignored)
```

## Phases

See [plan.md](plan.md) for the full phase-by-phase build plan.

## Resume

> Built and deployed a production-grade multi-tenant financial RAG platform on AWS using NVIDIA NIM microservices (LLM + embedding + reranking on GPU), with hybrid retrieval (BM25 + dense + RRF + cross-encoder reranking), chunk-level RBAC enforced at retrieval time, Milvus vector store, Kubernetes orchestration with HPA autoscaling, Prometheus/Grafana observability, and RAGAS evaluation.
