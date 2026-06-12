"""
retrieval.vector_store — Milvus collection management and chunk insertion.

Wraps pymilvus.MilvusClient to provide a high-level interface for:
  - Creating the FinRAG collection with the FULL Phase-1 schema (idempotent).
  - Upserting embedded Chunk objects into the collection.

WHY full schema from day one:
  The FINRAG_MASTER_PLAN mandates that every Milvus field exists at collection
  creation.  Later phases (2 = RBAC, 3 = auth, 6 = multimodal) only populate
  fields — they never ALTER the collection schema.  Re-creating a Milvus
  collection with a new schema forces a full re-ingest of all documents.
  By paying a small upfront cost (a few extra nullable/default fields), we
  make all future phases zero-downtime from a schema perspective.

WHY allowed_roles is ARRAY(VARCHAR):
  Phase 2 adds a retrieval-time RBAC filter:
      ARRAY_CONTAINS(allowed_roles, user_role)
  This filter runs INSIDE the Milvus vector search — not in a post-filter step —
  which means forbidden chunks never enter the LLM's context window.
  ARRAY_CONTAINS requires the field to be DataType.ARRAY.  A serialised
  JSON string would make the filter impossible without a table scan.

WHY COSINE metric:
  nv-embedqa-e5-v5 produces L2-normalised vectors.  Cosine similarity over
  normalised vectors is equivalent to dot product and is the recommended metric
  for NeMo Retriever embeddings (see NVIDIA docs + ADR-003).

Public API
----------
    MilvusStore(uri, collection_name)
        .ensure_collection(dim)   — idempotent schema + index creation
        .insert_chunks(chunks)    — validate, map, upsert; returns insert count
        .drop_collection()        — teardown (tests + reindex)
        .collection_exists()      — predicate
"""

from __future__ import annotations

import time
from typing import Any

import structlog
from pymilvus import DataType, MilvusClient

from config.settings import get_settings
from ingest.models import Chunk
from retrieval.errors import VectorStoreError

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# VARCHAR field lengths — sized to fit realistic values with a safety margin.
_MAX_SHORT = 64  # chunk_id, doc_id, org_id, sensitivity_level, content_type
_MAX_MEDIUM = 512  # doc_name, section, source_modality
_MAX_LONG = 65535  # text, caption — Milvus VARCHAR ceiling

# ARRAY field limits — must be ≥ the max roles a chunk could carry.
# Phase 2 expects at most a handful of roles per chunk; 16 is generous.
_MAX_ROLES_CAPACITY = 16
_MAX_ROLE_LENGTH = 64


class MilvusStore:
    """Thin wrapper around MilvusClient for the FinRAG chunk collection.

    In development (Phases 1-4) the URI is a local .db file path, which
    activates Milvus Lite — a fully embedded SQLite-backed Milvus that needs
    no server process.  In production (Phase 5) the URI points at a real
    Milvus server and the API is identical; only the URI env var changes.

    Args:
        uri:             Milvus URI.  Defaults to settings.milvus_uri.
                         Pass a tmp_path string in tests for isolation.
        collection_name: Collection name.  Defaults to settings.milvus_collection.
    """

    def __init__(
        self,
        uri: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        settings = get_settings()
        self._uri = uri or settings.milvus_uri
        self._collection_name = collection_name or settings.milvus_collection
        self._client: MilvusClient = MilvusClient(uri=self._uri)
        logger.debug("vector_store.connected", uri=self._uri, collection=self._collection_name)

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    def ensure_collection(self, dim: int) -> None:
        """Create the FinRAG collection if it doesn't exist.  Idempotent.

        Creates the full Phase-1 chunk schema (all fields including RBAC
        placeholders), builds an AUTOINDEX with COSINE metric on the embedding
        field, and loads the collection into memory so it is immediately
        queryable.

        Calling this twice with the same dim is safe — the second call is a
        no-op if the collection already exists.

        Args:
            dim: Embedding dimension from the first embedded chunk.
                 nv-embedqa-e5-v5 produces 1024-dimensional vectors.

        Raises:
            VectorStoreError: If collection creation fails unexpectedly.
        """
        if self._client.has_collection(self._collection_name):
            logger.info(
                "vector_store.collection_exists",
                collection=self._collection_name,
                dim=dim,
            )
            return

        schema = self._client.create_schema(auto_id=False, enable_dynamic_field=False)

        # ── Identity fields ────────────────────────────────────────────
        schema.add_field("chunk_id", DataType.VARCHAR, max_length=_MAX_SHORT, is_primary=True)
        schema.add_field("doc_id", DataType.VARCHAR, max_length=_MAX_SHORT)
        schema.add_field("doc_name", DataType.VARCHAR, max_length=_MAX_MEDIUM)
        schema.add_field("page_number", DataType.INT64)
        schema.add_field("section", DataType.VARCHAR, max_length=_MAX_MEDIUM)

        # ── Access / RBAC fields ───────────────────────────────────────
        # WHY these fields exist in Phase 1: Phase 2 will populate real values
        # from the uploader's JWT.  Adding the fields now means no collection
        # re-creation (and no re-ingest of all documents) when Phase 2 ships.
        schema.add_field("org_id", DataType.VARCHAR, max_length=_MAX_SHORT)

        # WHY ARRAY: Phase 2 uses ARRAY_CONTAINS(allowed_roles, user_role) as a
        # Milvus metadata filter inside the vector search.  A string field would
        # require a full table scan or post-filtering — both of which defeat the
        # security guarantee that forbidden chunks never reach the LLM.
        schema.add_field(
            "allowed_roles",
            DataType.ARRAY,
            element_type=DataType.VARCHAR,
            max_capacity=_MAX_ROLES_CAPACITY,
            max_length=_MAX_ROLE_LENGTH,
        )
        schema.add_field("sensitivity_level", DataType.VARCHAR, max_length=_MAX_SHORT)

        # ── Retrieval fields ───────────────────────────────────────────
        schema.add_field("text", DataType.VARCHAR, max_length=_MAX_LONG)
        # dim is detected from the first embedded chunk, not hardcoded — see ADR-003
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=dim)

        # ── Multimodal fields ──────────────────────────────────────────
        schema.add_field("content_type", DataType.VARCHAR, max_length=_MAX_SHORT)
        schema.add_field("source_modality", DataType.VARCHAR, max_length=_MAX_MEDIUM)
        # caption is empty for text/table chunks; populated in Phase 6 (VLM)
        schema.add_field("caption", DataType.VARCHAR, max_length=_MAX_LONG)

        # ── Index ──────────────────────────────────────────────────────
        # WHY AUTOINDEX + COSINE: AUTOINDEX lets Milvus choose the best structure
        # (HNSW in Lite, IVF_FLAT in Zilliz, TensorRT index on GPU in Phase 5).
        # COSINE matches nv-embedqa-e5-v5 which produces L2-normalised vectors.
        index_params = self._client.prepare_index_params()
        index_params.add_index("embedding", index_type="AUTOINDEX", metric_type="COSINE")

        self._client.create_collection(
            self._collection_name,
            schema=schema,
            index_params=index_params,
        )
        logger.info(
            "vector_store.collection_created",
            collection=self._collection_name,
            dim=dim,
            fields=13,
        )

    # ------------------------------------------------------------------
    # Data mutation
    # ------------------------------------------------------------------

    def insert_chunks(self, chunks: list[Chunk]) -> int:
        """Validate, map, and upsert chunks into the collection.

        Uses upsert (not insert) so re-ingesting a document with the same
        chunk_ids is idempotent — existing rows are replaced rather than
        duplicated.  Deterministic chunk_ids (SHA-256 of doc_id+page+index,
        see ingest/models.py) make re-ingest safe.

        Args:
            chunks: Embedded Chunk objects.  Every chunk MUST have a non-None
                    embedding field.

        Returns:
            Number of rows written (as reported by Milvus upsert_count).

        Raises:
            VectorStoreError: If any chunk has a None embedding, or if the
                              Milvus upsert fails.
        """
        if not chunks:
            return 0

        log = logger.bind(collection=self._collection_name, chunk_count=len(chunks))
        log.info("vector_store.insert_start")
        t0 = time.monotonic()

        rows = [self._chunk_to_row(c) for c in chunks]  # raises VectorStoreError on None embedding
        result = self._client.upsert(self._collection_name, data=rows)
        count: int = int(result["upsert_count"])

        elapsed = time.monotonic() - t0
        log.info("vector_store.insert_done", upsert_count=count, elapsed_s=round(elapsed, 3))
        return count

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    def drop_collection(self) -> None:
        """Drop the collection if it exists.  Safe to call on non-existent collection."""
        if self._client.has_collection(self._collection_name):
            self._client.drop_collection(self._collection_name)
            logger.info("vector_store.collection_dropped", collection=self._collection_name)

    def collection_exists(self) -> bool:
        """Return True if the collection exists in this Milvus instance."""
        result: bool = self._client.has_collection(self._collection_name)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _chunk_to_row(chunk: Chunk) -> dict[str, Any]:
        """Map a Chunk to a flat dict suitable for Milvus upsert.

        Args:
            chunk: A schema-complete Chunk with a populated embedding field.

        Returns:
            Dict with keys matching the collection field names.

        Raises:
            VectorStoreError: If chunk.embedding is None (not yet embedded).
        """
        if chunk.embedding is None:
            raise VectorStoreError(
                f"Chunk {chunk.chunk_id!r} has no embedding. "
                "Run embed_chunks() before insert_chunks()."
            )
        return {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "doc_name": chunk.doc_name,
            "page_number": chunk.page_number,
            "section": chunk.section,
            "org_id": chunk.org_id,
            # allowed_roles is list[str] — Milvus ARRAY field accepts Python lists
            "allowed_roles": chunk.allowed_roles,
            "sensitivity_level": chunk.sensitivity_level.value,
            "content_type": chunk.content_type.value,
            "source_modality": chunk.source_modality,
            # caption may be None in Phase 1; Milvus VARCHAR stores empty string
            "caption": chunk.caption or "",
            "text": chunk.text,
            "embedding": chunk.embedding,
        }
