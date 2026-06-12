"""
generation test fixtures.

Provides an isolated Milvus Lite database and a small seeded store+index
for generation integration tests.

Milvus Lite runs fully in-process (no server, no network) — these fixtures
work in default CI without @pytest.mark.slow.
"""

from __future__ import annotations

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
from retrieval.bm25 import build_bm25_index
from retrieval.vector_store import MilvusStore

_TEST_DIM = 8
_TEST_COLLECTION = "test_generation_chunks"


@pytest.fixture
def milvus_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Return a temporary Milvus Lite database path scoped to one test."""
    db_path = tmp_path / "finrag_gen_test.db"
    yield db_path
    if db_path.exists():
        shutil.rmtree(str(db_path), ignore_errors=True)


def _fake_embedding(dim: int = _TEST_DIM, seed: int = 0) -> list[float]:
    """Return a deterministic unit-ish embedding for testing."""
    return [float((seed + i) % 10) / 10.0 for i in range(dim)]


def make_test_chunk(
    idx: int,
    text: str,
    doc_name: str = "test_doc.pdf",
    page: int = 0,
) -> Chunk:
    """Build a Chunk with a fake embedding, ready to insert."""
    return Chunk(
        chunk_id=make_chunk_id("gen_test_doc", page, idx),
        doc_id="gen_test_doc",
        doc_name=doc_name,
        page_number=page,
        section="Test Section",
        org_id="dev",
        text=text,
        content_type=ContentType.TEXT,
        sensitivity_level=SensitivityLevel.INTERNAL,
        embedding=_fake_embedding(seed=idx),
    )


@pytest.fixture
def seeded_store_and_index(
    milvus_db: Path,
) -> tuple[MilvusStore, object]:
    """Return a MilvusStore + BM25Index seeded with 3 test chunks."""
    from retrieval.bm25 import BM25Index

    chunks = [
        make_test_chunk(0, "The company reported total revenue of $26 billion.", page=1),
        make_test_chunk(1, "Operating income increased by 15% compared to last year.", page=2),
        make_test_chunk(2, "Net income was $5.4 billion for the fiscal year.", page=3),
    ]

    store = MilvusStore(uri=str(milvus_db), collection_name=_TEST_COLLECTION)
    store.ensure_collection(dim=_TEST_DIM)
    store.insert_chunks(chunks)

    bm25_index: BM25Index = build_bm25_index(chunks)
    return store, bm25_index
