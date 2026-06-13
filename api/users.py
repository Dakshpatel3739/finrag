"""
api.users — minimal but real SQLite user store.

Schema: users(user_id TEXT PK, email TEXT UNIQUE, org_id TEXT, role TEXT,
              password_hash TEXT)

WHY owner-only provisioning:
    Only a user with role=owner may create new users, and only within their
    own org.  This is how a client self-provisions their team: the org owner
    invites employees and HR staff.  The org_id on the new user is FORCED to
    the owner's org_id (from their JWT) — not taken from the request body.
    This prevents an owner from accidentally (or maliciously) creating users
    in a different tenant's org.  The system scales to any user count without
    admin intervention: owner invites as many users as needed, each inherits
    the org automatically.

WHY SQLite for Phase 3:
    SQLite gives us a real persistent store with proper uniqueness constraints
    and transactional writes without the operational overhead of Postgres.  The
    interface is abstracted (UserStore class + module-level functions) so
    migration to Postgres is a one-file change.

Public API
----------
    UserRecord          — dataclass: user_id, email, org_id, role, password_hash
    UserStore           — manages the SQLite connection + DDL
    get_user_store()    — returns the process-singleton UserStore
    create_user(...)    — insert user; raises DuplicateUserError on dup email
    get_user_by_email() — lookup by email; returns None if absent
    authenticate(...)   — verify credentials; returns Identity or None
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from functools import lru_cache

import structlog

from api.security import hash_password, verify_password
from config.settings import get_settings
from rbac.roles import Role

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS users (
    user_id       TEXT PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    org_id        TEXT NOT NULL,
    role          TEXT NOT NULL,
    password_hash TEXT NOT NULL
);
"""


# ── Exceptions ────────────────────────────────────────────────────────────────


class DuplicateUserError(Exception):
    """Raised when a create_user call would violate the UNIQUE email constraint."""


class UserStoreError(Exception):
    """Raised on unexpected SQLite errors in the user store."""


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class UserRecord:
    """A user row as returned from the store.

    password_hash is included so authenticate() can call verify_password
    without a second DB query.  Never expose this field over the API.
    """

    user_id: str
    email: str
    org_id: str
    role: str
    password_hash: str


# ── Store ─────────────────────────────────────────────────────────────────────


class UserStore:
    """SQLite-backed user store.

    Thread-safety: SQLite connections are not thread-safe for concurrent
    writes.  FastAPI runs on a single process; concurrent requests that write
    the user table (create_user) go through SQLite's built-in serialisation.
    For multi-process deployments, migrate to a network DB (Postgres).
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        """Initialise the store and apply DDL.

        Args:
            db_path: File path for the SQLite database, or ":memory:" for
                     in-process tests.
        """
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(_DDL)
        self._conn.commit()

    def create_user(
        self,
        email: str,
        password: str,
        org_id: str,
        role: Role,
    ) -> UserRecord:
        """Hash password and insert a new user row.

        WHY hash here (not in the caller):
            Ensures the plain password NEVER leaves this method without being
            hashed — it cannot accidentally be stored or logged by the caller.

        Args:
            email:    Unique email address.
            password: Plain-text password (will be argon2-hashed immediately).
            org_id:   Tenant identifier.
            role:     User's role.

        Returns:
            The newly created UserRecord.

        Raises:
            DuplicateUserError: email already exists.
            UserStoreError:     unexpected DB error.
        """
        user_id = str(uuid.uuid4())
        pw_hash = hash_password(password)
        try:
            self._conn.execute(
                "INSERT INTO users (user_id, email, org_id, role, password_hash) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, email.lower(), org_id, str(role), pw_hash),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DuplicateUserError(f"Email already registered: {email}") from exc
        except sqlite3.Error as exc:
            raise UserStoreError(f"DB error: {exc}") from exc

        record = UserRecord(
            user_id=user_id,
            email=email.lower(),
            org_id=org_id,
            role=str(role),
            password_hash=pw_hash,
        )
        logger.info("users.created", user_id=user_id, email=email, org_id=org_id, role=str(role))
        return record

    def get_user_by_email(self, email: str) -> UserRecord | None:
        """Look up a user by email address (case-insensitive).

        Args:
            email: The email address to look up.

        Returns:
            UserRecord if found, None otherwise.
        """
        cur = self._conn.execute(
            "SELECT user_id, email, org_id, role, password_hash FROM users WHERE email = ?",
            (email.lower(),),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return UserRecord(
            user_id=row[0],
            email=row[1],
            org_id=row[2],
            role=row[3],
            password_hash=row[4],
        )

    def authenticate(self, email: str, password: str) -> UserRecord | None:
        """Verify credentials and return the UserRecord on success.

        Uses constant-time password comparison via verify_password.  Returns
        None (not an exception) to avoid leaking whether the email exists vs
        the password is wrong — both return the same result to the caller.

        Args:
            email:    Login email.
            password: Plain-text candidate password.

        Returns:
            UserRecord if credentials match; None otherwise.
        """
        record = self.get_user_by_email(email)
        if record is None:
            return None
        if not verify_password(password, record.password_hash):
            return None
        return record


# ── Process singleton ─────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_user_store() -> UserStore:
    """Return the process-singleton UserStore.

    Uses the config_db_path from settings with a ``_users`` suffix so the
    user store is a separate file from the system_config SQLite DB.

    In tests, call get_user_store.cache_clear() and re-patch as needed.
    """
    settings = get_settings()
    db_path = settings.config_db_path.replace(".db", "_users.db")
    return UserStore(db_path=db_path)
