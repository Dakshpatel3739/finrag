"""eval.leak_suite conftest — pytest fixtures for the RBAC leak-test suite.

Provides a seeded MilvusStore + BM25Index + LeakTestCorpus per test function.
Each test gets a fresh isolated Milvus Lite database in a tmp_path so tests
are fully independent and can run in parallel.
"""

from __future__ import annotations

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

from eval.leak_suite.seeder import _COLLECTION, _DIM, LeakTestCorpus, build_leak_corpus
from retrieval.bm25 import BM25Index, build_bm25_index
from retrieval.vector_store import MilvusStore


@pytest.fixture
def leak_milvus_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Yield a temporary Milvus Lite database path scoped to one test."""
    db_path = tmp_path / "eval_leak_test.db"
    yield db_path
    if db_path.exists():
        shutil.rmtree(str(db_path), ignore_errors=True)


@pytest.fixture
def eval_store_and_index(
    leak_milvus_db: Path,
) -> tuple[MilvusStore, BM25Index, LeakTestCorpus]:
    """Return a seeded MilvusStore + BM25Index + LeakTestCorpus.

    ALL 9 chunks (two orgs, three sensitivity levels, one inconsistent chunk)
    are inserted into the Milvus collection and indexed by BM25.  The RBAC
    filter is the only access control mechanism — the store itself holds all
    chunks regardless of sensitivity.  This mirrors the production multi-tenant
    single-collection architecture.
    """
    corpus = build_leak_corpus()

    store = MilvusStore(uri=str(leak_milvus_db), collection_name=_COLLECTION)
    store.ensure_collection(dim=_DIM)
    store.insert_chunks(corpus.all_chunks)

    # BM25 built over the FULL corpus — RBAC filtering happens in document_search.
    bm25 = build_bm25_index(corpus.all_chunks)

    return store, bm25, corpus
