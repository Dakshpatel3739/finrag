"""
Tests for config.system_config — runtime-tunable parameter store.

All tests use a temporary DB path (pytest tmp_path fixture) so they are
fully isolated and leave no artefacts on disk.
"""

from pathlib import Path

import pytest

from config.system_config import get_config, init_config_db, set_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_db(tmp_path: Path) -> str:
    """Return a path string for a fresh DB with defaults seeded."""
    db = str(tmp_path / "test.db")
    init_config_db(db)
    return db


# ---------------------------------------------------------------------------
# init_config_db
# ---------------------------------------------------------------------------


def test_defaults_seeded_on_init(tmp_path: Path) -> None:
    """All compiled-in defaults must be present after init."""
    db = make_db(tmp_path)
    assert get_config(db, "top_k") == 20
    assert get_config(db, "rerank_n") == 5
    assert get_config(db, "chunk_size") == 512
    assert get_config(db, "chunk_overlap") == 64
    assert get_config(db, "rrf_k") == 60


def test_init_is_idempotent(tmp_path: Path) -> None:
    """Calling init_config_db twice must not reset manual overrides."""
    db = make_db(tmp_path)
    set_config(db, "top_k", 99)
    init_config_db(db)  # second call — must not clobber
    assert get_config(db, "top_k") == 99


# ---------------------------------------------------------------------------
# set_config / get_config round-trips
# ---------------------------------------------------------------------------


def test_set_and_get_int(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    set_config(db, "top_k", 42)
    assert get_config(db, "top_k") == 42


def test_set_string_value_returned_as_int(tmp_path: Path) -> None:
    """set_config accepts a string representation; get_config returns int."""
    db = make_db(tmp_path)
    set_config(db, "rerank_n", "7")
    result = get_config(db, "rerank_n")
    assert result == 7
    assert isinstance(result, int)


def test_get_config_returns_int_type(tmp_path: Path) -> None:
    """Integer keys must return int, not str, even for default values."""
    db = make_db(tmp_path)
    result = get_config(db, "chunk_size")
    assert isinstance(result, int)


def test_multiple_updates_last_wins(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    set_config(db, "rrf_k", 30)
    set_config(db, "rrf_k", 45)
    assert get_config(db, "rrf_k") == 45


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_unknown_key_raises_value_error_on_get(tmp_path: Path) -> None:
    """Passing an unrecognised key to get_config must raise ValueError."""
    db = make_db(tmp_path)
    with pytest.raises(ValueError, match="Unknown config key"):
        get_config(db, "nonexistent_key")  # type: ignore[arg-type]


def test_unknown_key_raises_value_error_on_set(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    with pytest.raises(ValueError, match="Unknown config key"):
        set_config(db, "bad_key", 1)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# DB isolation
# ---------------------------------------------------------------------------


def test_separate_dbs_are_isolated(tmp_path: Path) -> None:
    """Two different DB paths must not share state."""
    db1 = str(tmp_path / "a.db")
    db2 = str(tmp_path / "b.db")
    init_config_db(db1)
    init_config_db(db2)
    set_config(db1, "top_k", 77)
    assert get_config(db2, "top_k") == 20  # unchanged default
