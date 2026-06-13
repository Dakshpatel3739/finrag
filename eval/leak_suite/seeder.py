"""eval.leak_suite.seeder — deterministic Milvus Lite corpus for RBAC leak tests.

Builds a LeakTestCorpus with:
  - Two orgs: "acme" and "globex"
  - All three sensitivity levels: public, internal, restricted
  - Multiple chunks per sensitivity level (wider coverage than Phase 2 corpus)
  - One "inconsistent" chunk: sensitivity_level=public but allowed_roles
    deliberately restricted to ["owner","finance"] only, testing that
    allowed_roles is the authoritative gate (stricter than policy default wins)

WHY fixed embeddings:
    We are testing the RBAC FILTER, not semantic retrieval quality.
    All chunks and the query share the same unit vector so Milvus COSINE
    similarity == 1.0 for every chunk.  The Milvus ARRAY_CONTAINS filter is
    the ONLY thing that differentiates results.  This removes non-determinism
    from vector ordering and makes the corpus repeatable across environments.

WHY a separate corpus from rbac/conftest.py:
    The eval corpus is eval-grade: more chunks, more sensitivity combinations,
    the inconsistent-chunk case, and structured for parametrised testing.
    The rbac/ corpus is minimal — just enough to prove Phase 2 invariants.
"""

from __future__ import annotations

from dataclasses import dataclass

from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
from rbac.roles import sensitivity_to_default_roles

# Fixed unit vector — Milvus COSINE distance == 1.0 for every chunk/query pair.
# Changing the filter is the only way to change which chunks are returned.
_FAKE_VEC: list[float] = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
_DIM: int = len(_FAKE_VEC)
_COLLECTION: str = "eval_leak_suite"


def _make_chunk(
    idx: int,
    text: str,
    org_id: str,
    sensitivity: SensitivityLevel,
    doc_name: str = "eval_test.pdf",
    page: int = 0,
    allowed_roles_override: list[str] | None = None,
) -> Chunk:
    """Build a deterministic test chunk with the given RBAC metadata.

    allowed_roles_override lets tests craft deliberately inconsistent chunks
    (e.g. sensitivity_level=public but allowed_roles=["owner","finance"]).
    """
    roles = (
        allowed_roles_override
        if allowed_roles_override is not None
        else [str(r) for r in sensitivity_to_default_roles(sensitivity)]
    )
    return Chunk(
        chunk_id=make_chunk_id(f"{org_id}_eval_seed_{idx}", page, idx),
        doc_id=f"{org_id}_eval_doc",
        doc_name=doc_name,
        page_number=page,
        section="EvalTest",
        org_id=org_id,
        sensitivity_level=sensitivity,
        allowed_roles=roles,
        text=text,
        content_type=ContentType.TEXT,
        embedding=list(_FAKE_VEC),
    )


@dataclass
class LeakTestCorpus:
    """Comprehensive multi-org, multi-sensitivity RBAC test corpus.

    Structured so tests can reference individual chunks by name and assert
    specific chunk_ids in (or absent from) retrieval results.
    """

    # ── acme org ─────────────────────────────────────────────────────────────
    acme_public_1: Chunk  # allowed_roles: all 4
    acme_public_2: Chunk  # allowed_roles: all 4
    acme_internal_1: Chunk  # allowed_roles: all 4
    acme_internal_2: Chunk  # allowed_roles: all 4
    acme_restricted_1: Chunk  # allowed_roles: owner, finance ONLY
    acme_restricted_2: Chunk  # allowed_roles: owner, finance ONLY

    # ── globex org ────────────────────────────────────────────────────────────
    globex_public_1: Chunk  # allowed_roles: all 4
    globex_restricted_1: Chunk  # allowed_roles: owner, finance ONLY

    # ── Defense-in-depth chunk ────────────────────────────────────────────────
    # sensitivity_level=public (policy says all 4 roles), but allowed_roles is
    # deliberately narrowed to ["owner","finance"].  Tests that allowed_roles
    # is the authoritative gate — stricter than the sensitivity_level default wins.
    acme_inconsistent: Chunk

    @property
    def all_chunks(self) -> list[Chunk]:
        """All chunks in insertion order."""
        return [
            self.acme_public_1,
            self.acme_public_2,
            self.acme_internal_1,
            self.acme_internal_2,
            self.acme_restricted_1,
            self.acme_restricted_2,
            self.globex_public_1,
            self.globex_restricted_1,
            self.acme_inconsistent,
        ]

    @property
    def acme_restricted_ids(self) -> set[str]:
        """chunk_ids that are restricted for acme (hr/employee must NEVER see)."""
        return {self.acme_restricted_1.chunk_id, self.acme_restricted_2.chunk_id}

    @property
    def globex_chunk_ids(self) -> set[str]:
        """All chunk_ids belonging to globex (cross-tenant: acme users must NEVER see)."""
        return {self.globex_public_1.chunk_id, self.globex_restricted_1.chunk_id}

    @property
    def acme_public_ids(self) -> set[str]:
        """chunk_ids that are public for acme (all roles MUST be able to see)."""
        return {self.acme_public_1.chunk_id, self.acme_public_2.chunk_id}


def build_leak_corpus() -> LeakTestCorpus:
    """Return a deterministic LeakTestCorpus seeded with all sensitivity/org combos.

    The corpus is fully deterministic: same chunk_ids, same embeddings, same
    allowed_roles on every call.  Tests that use this corpus are reproducible
    across machines and CI runs.
    """
    return LeakTestCorpus(
        acme_public_1=_make_chunk(
            0,
            "NVIDIA total revenue for fiscal year 2024 was $26.97 billion.",
            "acme",
            SensitivityLevel.PUBLIC,
            page=1,
        ),
        acme_public_2=_make_chunk(
            1,
            "Data Center segment driven by H100 and A100 GPU demand in fiscal 2024.",
            "acme",
            SensitivityLevel.PUBLIC,
            page=2,
        ),
        acme_internal_1=_make_chunk(
            2,
            "Internal R&D budget increase of 15 percent planned for next fiscal year.",
            "acme",
            SensitivityLevel.INTERNAL,
            page=3,
        ),
        acme_internal_2=_make_chunk(
            3,
            "Internal headcount projection: 2,000 additional hires in engineering by Q3.",
            "acme",
            SensitivityLevel.INTERNAL,
            page=4,
        ),
        acme_restricted_1=_make_chunk(
            4,
            (
                "Executive compensation table: CEO salary $1,100,000 base. "
                "Total CEO compensation including equity awards $34,200,000."
            ),
            "acme",
            SensitivityLevel.RESTRICTED,
            page=5,
        ),
        acme_restricted_2=_make_chunk(
            5,
            (
                "Named executive officer salary schedule: CFO base $850,000. "
                "Annual equity grant $12,800,000. Total named officer compensation $89,400,000."
            ),
            "acme",
            SensitivityLevel.RESTRICTED,
            page=6,
        ),
        globex_public_1=_make_chunk(
            6,
            "Globex Corporation Q4 earnings exceeded analyst expectations.",
            "globex",
            SensitivityLevel.PUBLIC,
            doc_name="globex_report.pdf",
            page=1,
        ),
        globex_restricted_1=_make_chunk(
            7,
            "Globex CEO total compensation package totals $18,500,000 annually.",
            "globex",
            SensitivityLevel.RESTRICTED,
            doc_name="globex_report.pdf",
            page=5,
        ),
        # WHY this chunk exists:
        #   Defense-in-depth test case.  sensitivity_level=public would normally
        #   give all 4 roles access (per _POLICY in rbac.roles).  But the
        #   allowed_roles field is deliberately set to ["owner","finance"] only —
        #   simulating a document that was mislabeled at the sensitivity_level axis
        #   but had its allowed_roles set correctly (more strictly).
        #   The RBAC filter uses ARRAY_CONTAINS(allowed_roles, role), so the
        #   stricter allowed_roles wins and hr/employee are blocked even though
        #   sensitivity_level would normally permit them.
        acme_inconsistent=_make_chunk(
            8,
            (
                "This section was mislabeled public but scoped to finance review only. "
                "Salary benchmarking data for board compensation committee use."
            ),
            "acme",
            SensitivityLevel.PUBLIC,
            allowed_roles_override=["owner", "finance"],
            page=7,
        ),
    )
