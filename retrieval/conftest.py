"""
retrieval test fixtures.

Provides an isolated Milvus Lite database path for each test.
Milvus Lite runs fully in-process (no server, no network) — these tests
run in default CI without any @pytest.mark.slow decoration.

The db_path fixture creates a fresh .db directory under the system temp
path and removes it after each test so collections don't bleed between
tests.
"""

from __future__ import annotations

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def milvus_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Return a temporary Milvus Lite database path scoped to one test.

    Milvus Lite creates a directory (not a file) at the given path.  The
    fixture removes it after the test regardless of pass/fail, so each test
    starts with a clean, empty Milvus instance.

    Yields:
        A Path that does not yet exist (Milvus Lite creates it on first use).
    """
    db_path = tmp_path / "finrag_test.db"
    yield db_path
    # Milvus Lite creates a directory; remove the whole tree on teardown
    if db_path.exists():
        shutil.rmtree(str(db_path), ignore_errors=True)
