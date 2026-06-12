"""
config.system_config — runtime-tunable retrieval and generation parameters.

Values are persisted in a SQLite table (system_config) so they can be changed
at runtime without a code redeploy.  Changes are auditable (each row is a
timestamped upsert).  Falls back to compiled-in defaults when a DB row is
absent.

Why SQLite and not env vars?
  env vars require a process restart; the plan mandates tuning top_k / chunk_size
  without redeploy.  This module is the only place that touches this table.

Schema
------
    key        TEXT PRIMARY KEY
    value      TEXT NOT NULL
    updated_at TEXT NOT NULL  (ISO-8601 UTC)

Public API
----------
    init_config_db(path)          — create table + seed defaults
    set_config(path, key, value)  — upsert a value
    get_config(path, key)         — return int value (all current keys are ints)

All current config keys store integer values.  When a string-typed key is
needed in a future phase, extend ConfigKey and add an overload that returns str.

RBAC INVARIANT: nothing in this module touches allowed_roles or org_id — those
are immutable chunk metadata, not runtime config.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal

# ---------------------------------------------------------------------------
# Recognised config keys
# ---------------------------------------------------------------------------

# All current keys are integer-valued.
ConfigKey = Literal["top_k", "rerank_n", "chunk_size", "chunk_overlap", "rrf_k"]

_DEFAULTS: Final[dict[str, int]] = {
    "top_k": 20,
    "rerank_n": 5,
    "chunk_size": 512,
    "chunk_overlap": 64,
    "rrf_k": 60,
}

_VALID_KEYS: frozenset[str] = frozenset(_DEFAULTS)

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS system_config (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init_config_db(path: str | Path) -> None:
    """Create the system_config table and seed compiled-in defaults.

    Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS and
    INSERT OR IGNORE so existing overrides are never clobbered.

    Args:
        path: Filesystem path for the SQLite database file.
              Pass ``":memory:"`` in tests for an in-process throwaway DB.
    """
    with sqlite3.connect(str(path)) as conn:
        conn.execute(_DDL)
        now = _now()
        conn.executemany(
            "INSERT OR IGNORE INTO system_config (key, value, updated_at) VALUES (?, ?, ?)",
            [(k, str(v), now) for k, v in _DEFAULTS.items()],
        )
        conn.commit()


def set_config(path: str | Path, key: ConfigKey, value: int | str) -> None:
    """Persist *value* for *key* (upsert).

    Args:
        path:  Path to the SQLite DB (same value passed to init_config_db).
        key:   A valid ConfigKey literal.
        value: The new value.  Ints are stored as their string representation.

    Raises:
        ValueError: If *key* is not a recognised ConfigKey.
    """
    _assert_valid_key(key)
    with sqlite3.connect(str(path)) as conn:
        conn.execute(
            """
            INSERT INTO system_config (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                                           updated_at = excluded.updated_at
            """,
            (key, str(value), _now()),
        )
        conn.commit()


def get_config(path: str | Path, key: ConfigKey) -> int:
    """Return the current integer value for *key*.

    Checks the DB first; falls back to the compiled-in default.

    Args:
        path: Path to the SQLite DB.
        key:  A valid ConfigKey literal.

    Returns:
        The current integer value for the key.

    Raises:
        ValueError: If *key* is not a recognised ConfigKey.
        KeyError:   If the DB has no row and there is no compiled-in default
                    (should never happen for the keys defined above).
    """
    _assert_valid_key(key)
    with sqlite3.connect(str(path)) as conn:
        row = conn.execute("SELECT value FROM system_config WHERE key = ?", (key,)).fetchone()

    if row:
        return int(row[0])
    if key in _DEFAULTS:
        return _DEFAULTS[key]
    raise KeyError(f"No config value found for key: {key!r}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()


def _assert_valid_key(key: str) -> None:
    """Raise ValueError for unrecognised keys (defensive guard)."""
    if key not in _VALID_KEYS:
        raise ValueError(f"Unknown config key: {key!r}. Valid keys: {sorted(_VALID_KEYS)}")
