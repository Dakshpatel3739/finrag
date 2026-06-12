"""
config.settings — static, environment-driven configuration.

Reads from environment variables (and an optional .env file).  Only
infrastructure-level settings live here — API keys, service URLs, deploy
mode.  Runtime-tunable retrieval parameters (top_k, chunk_size, …) belong
in system_config, because they must be changeable without a redeploy.

Invariant: this module never touches the database.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# DEPLOY_MODE controls which NIM endpoints the application uses:
#   "hosted"      — NVIDIA hosted NIM API at build.nvidia.com (dev / Mode B)
#   "self_hosted" — self-hosted NIMs on EKS GPU cluster (Phase 5 / Mode A burst)
DeployMode = Literal["hosted", "self_hosted"]


class Settings(BaseSettings):
    """Application settings sourced from environment variables.

    All fields map 1-to-1 to the keys documented in .env.example.
    pydantic-settings resolves them case-insensitively, so the env vars
    may be upper- or lower-case.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── NVIDIA NIM ─────────────────────────────────────────────────────────
    # Single API key used for all three NIM services.
    nim_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="NVIDIA NIM API key — obtain from https://build.nvidia.com",
    )

    # Base URLs for each NIM service (no trailing slash).
    # In "hosted" mode all three default to the NVIDIA hosted API endpoint.
    # In "self_hosted" mode override these to your cluster's ClusterIP/NodePort.
    nim_llm_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="Base URL for the LLM NIM (llama-3.1-8b-instruct)",
    )
    nim_embed_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="Base URL for the NeMo Retriever Embedding NIM",
    )
    # WHY different base URL for reranking: the hosted NeMo Retriever Reranking NIM
    # lives at ai.api.nvidia.com/v1/retrieval/nvidia, not integrate.api.nvidia.com/v1.
    # The reranker appends /reranking to this base.
    # For self-hosted Phase 5 NIMs, override to http://nim-rerank:8000/v1/retrieval/nvidia.
    nim_rerank_base_url: str = Field(
        default="https://ai.api.nvidia.com/v1/retrieval/nvidia",
        description="Base URL for the NeMo Retriever Reranking NIM",
    )

    # Model identifiers (passed as the `model` parameter to the NIM endpoint)
    nim_llm_model: str = Field(default="meta/llama-3.1-8b-instruct")
    nim_embed_model: str = Field(default="nvidia/nv-embedqa-e5-v5")
    nim_rerank_model: str = Field(default="nvidia/rerank-qa-mistral-4b")

    # ── Runtime config DB ──────────────────────────────────────────────────
    # SQLite file used by system_config for tunable retrieval params (top_k, etc.)
    config_db_path: str = Field(
        default="finrag_config.db",
        description="Path to the SQLite DB for system_config (top_k, rerank_n, rrf_k …)",
    )

    # ── Milvus ─────────────────────────────────────────────────────────────
    # In dev use Milvus Lite — point MILVUS_URI at a local .db file path.
    # In production point at your Milvus server: http://milvus-service:19530
    milvus_uri: str = Field(
        default="milvus_finrag.db",
        description=(
            "Milvus Lite: path to a local .db file (e.g. 'milvus_finrag.db'). "
            "Milvus server: 'http://host:19530'."
        ),
    )
    milvus_collection: str = Field(default="finrag_chunks")

    # ── Deploy mode ────────────────────────────────────────────────────────
    deploy_mode: DeployMode = Field(
        default="hosted",
        description="'hosted' = NVIDIA hosted NIM API; 'self_hosted' = EKS GPU cluster NIMs",
    )

    # ── Auth (wired in Phase 3, declared now so imports never break) ───────
    jwt_secret: SecretStr = Field(
        default=SecretStr("change-me-before-production"),
        description="HS256 signing key for JWT tokens — MUST be changed in production",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiry_seconds: int = Field(default=3600)

    # ── API server ─────────────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance.

    The cache is populated on first call and reused for the process lifetime.
    In tests, invalidate with ``get_settings.cache_clear()`` before patching
    env vars.
    """
    return Settings()
