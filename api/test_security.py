"""
api.test_security — unit tests for password hashing and JWT primitives.

Tests:
  - Hash round-trips (hash → verify succeeds)
  - Wrong password fails verification
  - Hash is not plaintext
  - Hash is not a fast hash (sha/md5 prefix check)
  - Token create → decode round-trips claims
  - Expired token is rejected (TokenExpiredError)
  - Tampered token rejected (flip a claim byte / re-sign with wrong key)
  - Malformed token (not a JWT) rejected
"""

from __future__ import annotations

import time
from datetime import UTC
from unittest.mock import patch

import pytest

from api.security import (
    InvalidTokenError,
    TokenExpiredError,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from config.settings import Settings, get_settings

# ── Helpers ───────────────────────────────────────────────────────────────────


def _override_settings(**kwargs: object) -> Settings:
    """Return a Settings object with fields overridden (bypasses env file)."""
    from pydantic import SecretStr

    base = {
        "jwt_secret": SecretStr("test-secret-key-that-is-long-enough-32chars"),
        "jwt_algorithm": "HS256",
        "jwt_expiry_seconds": 1800,
    }
    base.update(kwargs)
    return Settings.model_validate(base)


# ── Password hashing ──────────────────────────────────────────────────────────


def test_hash_round_trip_succeeds() -> None:
    pw = "CorrectHorseBatteryStaple"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True


def test_wrong_password_fails() -> None:
    hashed = hash_password("correct-password")
    assert verify_password("wrong-password", hashed) is False


def test_hash_is_not_plaintext() -> None:
    pw = "supersecret"
    hashed = hash_password(pw)
    assert pw not in hashed


def test_hash_is_not_fast_hash() -> None:
    """Ensure the output is an argon2 or bcrypt hash, not a fast sha/md5 digest.

    Fast hashes (sha256, md5) produce hex strings of fixed length without a
    recognisable prefix.  Argon2 hashes begin with '$argon2'; bcrypt with '$2b$'.
    Reject any hash that lacks these prefixes.
    """
    pw = "password123"
    hashed = hash_password(pw)
    assert hashed.startswith("$argon2") or hashed.startswith("$2b$"), (
        f"Expected slow hash prefix ($argon2 or $2b$), got: {hashed[:10]}"
    )


def test_two_hashes_of_same_password_differ() -> None:
    """Salt is per-hash; same password must produce distinct stored values."""
    pw = "same-password"
    h1 = hash_password(pw)
    h2 = hash_password(pw)
    assert h1 != h2


# ── JWT ───────────────────────────────────────────────────────────────────────


def test_token_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.security.get_settings", lambda: _override_settings())
    get_settings.cache_clear()

    token = create_access_token(user_id="u1", org_id="acme", role="owner")
    claims = decode_token(token)

    assert claims["sub"] == "u1"
    assert claims["org_id"] == "acme"
    assert claims["role"] == "owner"


def test_token_contains_exp_and_iat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.security.get_settings", lambda: _override_settings())
    get_settings.cache_clear()

    token = create_access_token(user_id="u1", org_id="acme", role="owner")
    claims = decode_token(token)
    assert "exp" in claims
    assert "iat" in claims


def test_expired_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A token with expiry 1 second in the past must raise TokenExpiredError."""
    monkeypatch.setattr(
        "api.security.get_settings",
        lambda: _override_settings(jwt_expiry_seconds=-1),
    )
    get_settings.cache_clear()

    # Freeze time so the token's exp is definitely in the past
    now = time.time()
    with patch("api.security.datetime") as mock_dt:
        from datetime import datetime

        mock_dt.now.return_value = datetime.fromtimestamp(now - 10, tz=UTC)
        mock_dt.fromtimestamp = datetime.fromtimestamp
        token = create_access_token(user_id="u1", org_id="acme", role="owner")

    with pytest.raises(TokenExpiredError):
        decode_token(token)


def test_wrong_secret_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A token signed with secret A cannot be decoded with secret B."""
    from pydantic import SecretStr

    monkeypatch.setattr(
        "api.security.get_settings",
        lambda: _override_settings(
            jwt_secret=SecretStr("secret-A-long-enough-to-pass-32-char-check")
        ),
    )
    get_settings.cache_clear()
    token = create_access_token(user_id="u1", org_id="acme", role="owner")

    monkeypatch.setattr(
        "api.security.get_settings",
        lambda: _override_settings(
            jwt_secret=SecretStr("secret-B-long-enough-to-pass-32-char-check")
        ),
    )
    get_settings.cache_clear()

    with pytest.raises(InvalidTokenError):
        decode_token(token)


def test_tampered_payload_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flipping a byte in the payload (without re-signing) must be rejected.

    This is the key proof: a user holding a valid HR token cannot change the
    role claim to 'owner' without re-signing, and they don't have the secret.
    """
    monkeypatch.setattr("api.security.get_settings", lambda: _override_settings())
    get_settings.cache_clear()

    token = create_access_token(user_id="u1", org_id="acme", role="hr")
    # JWT is header.payload.signature (base64url-encoded parts, dot-separated)
    parts = token.split(".")
    assert len(parts) == 3

    # Flip the last char of the payload (base64url encoded claims)
    payload_b64 = parts[1]
    flipped = payload_b64[:-1] + ("A" if payload_b64[-1] != "A" else "B")
    tampered = f"{parts[0]}.{flipped}.{parts[2]}"

    with pytest.raises(InvalidTokenError):
        decode_token(tampered)


def test_malformed_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A random string that is not a JWT must raise InvalidTokenError."""
    monkeypatch.setattr("api.security.get_settings", lambda: _override_settings())
    get_settings.cache_clear()

    with pytest.raises(InvalidTokenError):
        decode_token("not.a.jwt.at.all")


def test_missing_claim_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A token missing a required claim (org_id, role, sub) must be rejected."""
    from jose import jwt as jose_jwt
    from pydantic import SecretStr

    secret = "test-secret-key-that-is-long-enough-32chars"
    monkeypatch.setattr(
        "api.security.get_settings",
        lambda: _override_settings(jwt_secret=SecretStr(secret)),
    )
    get_settings.cache_clear()

    import time as _time

    # Token with 'role' missing
    payload = {"sub": "u1", "org_id": "acme", "exp": _time.time() + 3600}
    token = jose_jwt.encode(payload, secret, algorithm="HS256")

    with pytest.raises(InvalidTokenError, match="missing required claim"):
        decode_token(token)
