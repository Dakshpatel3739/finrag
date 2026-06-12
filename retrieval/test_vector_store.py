"""
Tests for retrieval.vector_store — MilvusStore schema, insert, and upsert.

All tests use Milvus Lite (in-process, no server, no network) via the
milvus_db fixture (retrieval/conftest.py).  These are NOT marked @slow and
run in default CI.

Test coverage:
  - ensure_collection creates the collection with the exact expected schema
    including allowed_roles as DataType.ARRAY with element_type VARCHAR.
  - insert_chunks with fabricated embeddings writes the correct row count.
  - allowed_roles round-trips as a list after insert + query.
  - All metadata fields survive the insert → query round-trip.
  - Inserting a chunk with embedding=None raises VectorStoreError.
  - ensure_collection is idempotent (no error on second call).
  - Upserting the same chunk_id twice deduplicates (count stays 1).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pymilvus import DataType

from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
from retrieval.errors import VectorStoreError
from retrieval.vector_store import MilvusStore

# Use a small but realistic embedding dimension for tests
_TEST_DIM = 8
_TEST_COLLECTION = "test_chunks"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_embedding(dim: int = _TEST_DIM) -> list[float]:
    """Return a deterministic unit-ish vector of length *dim*."""
    return [0.1 * (i % 10) for i in range(dim)]


def _make_chunk(
    index: int,
    *,
    roles: list[str] | None = None,
    embed: bool = True,
) -> Chunk:
    """Build a Chunk with optional fabricated embedding."""
    chunk = Chunk(
        chunk_id=make_chunk_id("doc_test", 0, index),
        doc_id="doc_test",
        doc_name="test_financial.pdf",
        page_number=index,
        section="Revenue",
        org_id="acme",
        allowed_roles=roles if roles is not None else ["owner", "finance"],
        sensitivity_level=SensitivityLevel.INTERNAL,
        text=f"Revenue for period {index} was $4.2B.",
        content_type=ContentType.TEXT,
        source_modality="docling-text",
    )
    if embed:
        return chunk.model_copy(update={"embedding": _fake_embedding()})
    return chunk


def _make_store(milvus_db: Path) -> MilvusStore:
    return MilvusStore(uri=str(milvus_db), collection_name=_TEST_COLLECTION)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_ensure_collection_creates_collection(milvus_db: Path) -> None:
    """ensure_collection must create the collection."""
    store = _make_store(milvus_db)
    assert not store.collection_exists()

    store.ensure_collection(dim=_TEST_DIM)

    assert store.collection_exists()
    store.drop_collection()


def test_ensure_collection_has_all_required_fields(milvus_db: Path) -> None:
    """The collection schema must include every field from the Chunk model."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    from pymilvus import MilvusClient

    client = MilvusClient(uri=str(milvus_db))
    info = client.describe_collection(_TEST_COLLECTION)
    fields = {f["name"]: f for f in info["fields"]}

    expected_names = {
        "chunk_id",
        "doc_id",
        "doc_name",
        "page_number",
        "section",
        "org_id",
        "allowed_roles",
        "sensitivity_level",
        "text",
        "embedding",
        "content_type",
        "source_modality",
        "caption",
    }
    assert expected_names == set(fields), (
        f"Schema mismatch. Missing: {expected_names - set(fields)}, "
        f"Extra: {set(fields) - expected_names}"
    )
    store.drop_collection()


def test_allowed_roles_is_array_field(milvus_db: Path) -> None:
    """allowed_roles MUST be DataType.ARRAY with element_type VARCHAR.

    This is the single most important schema assertion — Phase 2 RBAC uses
    ARRAY_CONTAINS(allowed_roles, user_role) inside the Milvus vector search.
    A non-ARRAY field would make that filter impossible.
    """
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    from pymilvus import MilvusClient

    client = MilvusClient(uri=str(milvus_db))
    info = client.describe_collection(_TEST_COLLECTION)
    fields = {f["name"]: f for f in info["fields"]}

    ar = fields["allowed_roles"]
    assert ar["type"] == DataType.ARRAY, f"allowed_roles must be ARRAY (22), got {ar['type']}"
    assert ar.get("element_type") == DataType.VARCHAR, (
        f"allowed_roles element_type must be VARCHAR (21), got {ar.get('element_type')}"
    )
    store.drop_collection()


def test_embedding_field_dim_matches_input(milvus_db: Path) -> None:
    """The embedding field dimension must match the dim passed to ensure_collection."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    from pymilvus import MilvusClient

    client = MilvusClient(uri=str(milvus_db))
    info = client.describe_collection(_TEST_COLLECTION)
    fields = {f["name"]: f for f in info["fields"]}

    emb = fields["embedding"]
    assert emb["type"] == DataType.FLOAT_VECTOR
    assert emb["params"]["dim"] == _TEST_DIM
    store.drop_collection()


def test_page_number_is_int64(milvus_db: Path) -> None:
    """page_number must be INT64 (not VARCHAR) so range filters work."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    from pymilvus import MilvusClient

    client = MilvusClient(uri=str(milvus_db))
    info = client.describe_collection(_TEST_COLLECTION)
    fields = {f["name"]: f for f in info["fields"]}

    assert fields["page_number"]["type"] == DataType.INT64
    store.drop_collection()


def test_ensure_collection_is_idempotent(milvus_db: Path) -> None:
    """Calling ensure_collection twice must not raise and must not duplicate."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)
    store.ensure_collection(dim=_TEST_DIM)  # second call — must be a no-op

    assert store.collection_exists()
    store.drop_collection()


# ---------------------------------------------------------------------------
# Insert tests
# ---------------------------------------------------------------------------


def test_insert_chunks_returns_correct_count(milvus_db: Path) -> None:
    """insert_chunks must return the number of rows written."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    chunks = [_make_chunk(i) for i in range(5)]
    count = store.insert_chunks(chunks)

    assert count == 5
    store.drop_collection()


def test_insert_empty_list_returns_zero(milvus_db: Path) -> None:
    """Inserting an empty list must return 0 without error."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    count = store.insert_chunks([])

    assert count == 0
    store.drop_collection()


def test_insert_chunk_without_embedding_raises(milvus_db: Path) -> None:
    """A chunk with embedding=None must raise VectorStoreError before any Milvus call."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    chunk_no_emb = _make_chunk(0, embed=False)
    assert chunk_no_emb.embedding is None

    with pytest.raises(VectorStoreError, match="no embedding"):
        store.insert_chunks([chunk_no_emb])

    store.drop_collection()


# ---------------------------------------------------------------------------
# Round-trip / data-integrity tests
# ---------------------------------------------------------------------------


def test_allowed_roles_round_trips_as_list(milvus_db: Path) -> None:
    """allowed_roles must survive insert → query as a Python list.

    This confirms the ARRAY field stores and retrieves multi-role lists
    correctly — critical for Phase 2 ARRAY_CONTAINS filter.
    """
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    original_roles = ["owner", "finance", "analyst"]
    chunk = _make_chunk(0, roles=original_roles)
    store.insert_chunks([chunk])

    from pymilvus import MilvusClient

    client = MilvusClient(uri=str(milvus_db))
    rows = client.query(
        _TEST_COLLECTION,
        filter=f'chunk_id == "{chunk.chunk_id}"',
        output_fields=["chunk_id", "allowed_roles"],
    )

    assert len(rows) == 1
    retrieved_roles = list(rows[0]["allowed_roles"])
    assert sorted(retrieved_roles) == sorted(original_roles), (
        f"allowed_roles mismatch: expected {original_roles}, got {retrieved_roles}"
    )
    store.drop_collection()


def test_metadata_round_trip(milvus_db: Path) -> None:
    """All scalar metadata fields must survive insert → query unchanged."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    chunk = _make_chunk(7)
    store.insert_chunks([chunk])

    from pymilvus import MilvusClient

    client = MilvusClient(uri=str(milvus_db))
    rows = client.query(
        _TEST_COLLECTION,
        filter=f'chunk_id == "{chunk.chunk_id}"',
        output_fields=[
            "chunk_id",
            "doc_id",
            "doc_name",
            "page_number",
            "section",
            "org_id",
            "sensitivity_level",
            "content_type",
            "source_modality",
            "text",
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["chunk_id"] == chunk.chunk_id
    assert row["doc_id"] == chunk.doc_id
    assert row["doc_name"] == chunk.doc_name
    assert row["page_number"] == chunk.page_number
    assert row["section"] == chunk.section
    assert row["org_id"] == chunk.org_id
    assert row["sensitivity_level"] == chunk.sensitivity_level.value
    assert row["content_type"] == chunk.content_type.value
    assert row["source_modality"] == chunk.source_modality
    assert row["text"] == chunk.text
    store.drop_collection()


def test_upsert_deduplicates_on_same_chunk_id(milvus_db: Path) -> None:
    """Inserting the same chunk_id twice must not create duplicates."""
    store = _make_store(milvus_db)
    store.ensure_collection(dim=_TEST_DIM)

    chunk = _make_chunk(0)
    store.insert_chunks([chunk])

    # Insert again — upsert must replace, not append
    chunk_v2 = chunk.model_copy(
        update={"text": "Updated revenue text.", "embedding": [0.9] * _TEST_DIM}
    )
    store.insert_chunks([chunk_v2])

    from pymilvus import MilvusClient

    client = MilvusClient(uri=str(milvus_db))
    rows = client.query(
        _TEST_COLLECTION,
        filter='chunk_id >= ""',
        output_fields=["chunk_id", "text"],
    )

    # Only ONE row for this chunk_id
    matching = [r for r in rows if r["chunk_id"] == chunk.chunk_id]
    assert len(matching) == 1
    assert matching[0]["text"] == "Updated revenue text."
    store.drop_collection()


def test_collection_exists_false_before_creation(milvus_db: Path) -> None:
    """collection_exists must return False before ensure_collection is called."""
    store = _make_store(milvus_db)
    assert not store.collection_exists()


def test_drop_collection_is_idempotent(milvus_db: Path) -> None:
    """drop_collection on a non-existent collection must not raise."""
    store = _make_store(milvus_db)
    store.drop_collection()  # no collection exists — must be a no-op
    store.ensure_collection(dim=_TEST_DIM)
    store.drop_collection()
    store.drop_collection()  # second drop — also a no-op
    assert not store.collection_exists()
