"""
rbac test fixtures.

Provides an isolated Milvus Lite database and a helper that seeds a realistic
multi-org, multi-sensitivity corpus for adversarial RBAC tests.

All fixtures run fully in-process (no server, no network) and are safe for
default CI without @pytest.mark.slow.
"""

from __future__ import annotations

import shutil
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

import pytest

from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
from rbac.roles import sensitivity_to_default_roles
from retrieval.bm25 import BM25Index, build_bm25_index
from retrieval.vector_store import MilvusStore

_TEST_DIM = 8
_COLLECTION = "test_rbac_chunks"

# A normalised fake embedding — all chunks and the query share this vector so
# Milvus COSINE similarity == 1.0 for every chunk.  The RBAC filter is the
# only thing that differentiates results.
_FAKE_VEC: list[float] = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


def _make_chunk(
    idx: int,
    text: str,
    org_id: str,
    sensitivity: SensitivityLevel,
    doc_name: str = "corp_report.pdf",
    page: int = 0,
    section: str = "Finance",
) -> Chunk:
    """Build a Chunk with real RBAC metadata and a fake embedding."""
    roles = [str(r) for r in sensitivity_to_default_roles(sensitivity)]
    return Chunk(
        chunk_id=make_chunk_id(f"{org_id}_rbac_test", page, idx),
        doc_id=f"{org_id}_rbac_doc",
        doc_name=doc_name,
        page_number=page,
        section=section,
        org_id=org_id,
        sensitivity_level=sensitivity,
        allowed_roles=roles,
        text=text,
        content_type=ContentType.TEXT,
        embedding=list(_FAKE_VEC),
    )


@dataclass
class RBACCorpus:
    """Test corpus with realistic multi-org, multi-sensitivity chunks."""

    # acme org chunks
    acme_public: Chunk
    acme_internal: Chunk
    acme_restricted: Chunk  # salary table — allowed_roles=[owner, finance] only

    # globex org chunk (cross-tenant isolation test)
    globex_restricted: Chunk

    # Convenience accessors
    @property
    def all_chunks(self) -> list[Chunk]:
        return [
            self.acme_public,
            self.acme_internal,
            self.acme_restricted,
            self.globex_restricted,
        ]

    @property
    def acme_chunks(self) -> list[Chunk]:
        return [self.acme_public, self.acme_internal, self.acme_restricted]


def build_test_corpus() -> RBACCorpus:
    """Return a realistic 4-chunk RBAC corpus."""
    return RBACCorpus(
        acme_public=_make_chunk(
            idx=0,
            text="NVIDIA reported total revenue of $22 billion in Q4 fiscal year 2024.",
            org_id="acme",
            sensitivity=SensitivityLevel.PUBLIC,
            page=1,
            section="Revenue",
        ),
        acme_internal=_make_chunk(
            idx=1,
            text="Internal budget forecast for next fiscal year is $2 billion in R&D.",
            org_id="acme",
            sensitivity=SensitivityLevel.INTERNAL,
            page=2,
            section="Budget",
        ),
        acme_restricted=_make_chunk(
            idx=2,
            text=(
                "Executive compensation table: CEO salary $15,000,000 annual. "
                "CFO salary $8,500,000 annual. Board member compensation $750,000. "
                "Total executive compensation expense $32,400,000."
            ),
            org_id="acme",
            sensitivity=SensitivityLevel.RESTRICTED,
            page=3,
            section="Executive Compensation",
        ),
        globex_restricted=_make_chunk(
            idx=3,
            text="Globex CEO total compensation package is $10,200,000 annually.",
            org_id="globex",
            sensitivity=SensitivityLevel.RESTRICTED,
            page=5,
            section="Executive Compensation",
            doc_name="globex_report.pdf",
        ),
    )


@pytest.fixture
def milvus_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Return a temporary Milvus Lite database path scoped to one test."""
    db_path = tmp_path / "finrag_rbac_test.db"
    yield db_path
    if db_path.exists():
        shutil.rmtree(str(db_path), ignore_errors=True)


@pytest.fixture
def rbac_store_and_index(milvus_db: Path) -> tuple[MilvusStore, BM25Index, RBACCorpus]:
    """Return a seeded MilvusStore + BM25Index + corpus for adversarial tests.

    ALL four chunks (two orgs, three sensitivity levels) are inserted into
    the store and indexed by BM25.  The RBAC filter is what restricts access —
    not the index contents.  This simulates a production store where multiple
    tenants share a single collection.
    """
    corpus = build_test_corpus()

    store = MilvusStore(uri=str(milvus_db), collection_name=_COLLECTION)
    store.ensure_collection(dim=_TEST_DIM)
    store.insert_chunks(corpus.all_chunks)

    # BM25 built over the full corpus — filtering happens in document_search.
    bm25 = build_bm25_index(corpus.all_chunks)

    return store, bm25, corpus
