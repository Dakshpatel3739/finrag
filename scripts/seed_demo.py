"""
scripts.seed_demo — Ingest the two Adani Energy demo PDFs into Milvus.

Run with:
    python -m scripts.seed_demo

Prerequisites:
    - NIM_API_KEY set in environment (live embedding NIM is called).
    - data/adani-energy-fy2026.pdf and data/adani-energy-internal.pdf present.
    - Milvus Lite db path configured (default: milvus_finrag.db in cwd).

NOTE: This script makes real calls to the NVIDIA Embedding NIM and is NOT
run in CI.  Add @pytest.mark.slow if you ever want to wrap it in a test.

Sensitivity policy (single source of truth in rbac/roles.py):
    RESTRICTED → allowed_roles = ["owner", "finance"]   (adani-energy-fy2026.pdf)
    INTERNAL   → allowed_roles = ["owner", "finance", "hr", "employee"] (adani-energy-internal.pdf)
The allowed_roles are derived from the sensitivity level by ingest_and_store →
assign_access → sensitivity_to_default_roles.  They are NOT hardcoded here.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from ingest.models import SensitivityLevel
from ingest.pipeline import ingest_and_store

_ORG_ID = "demo-org"

_DOCS: list[tuple[Path, SensitivityLevel]] = [
    (
        Path("data/adani-energy-fy2026.pdf"),
        SensitivityLevel.RESTRICTED,  # owner + finance only
    ),
    (
        Path("data/adani-energy-internal.pdf"),
        SensitivityLevel.INTERNAL,  # all roles
    ),
]


async def _seed() -> None:
    total = 0
    for pdf_path, sensitivity in _DOCS:
        if not pdf_path.exists():
            print(f"  SKIP  {pdf_path} — file not found")
            continue
        print(f"  Ingesting {pdf_path.name} ({sensitivity.value}) …")
        rows = await ingest_and_store(
            path=pdf_path,
            org_id=_ORG_ID,
            sensitivity_level=sensitivity,
        )
        print(f"  → {rows} rows stored")
        total += rows
    print(f"\nDone. Total rows stored: {total}")


if __name__ == "__main__":
    print(f"Seeding demo corpus for org '{_ORG_ID}' …")
    asyncio.run(_seed())
