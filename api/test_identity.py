"""
api.test_identity — unit tests for the get_current_identity FastAPI dependency.

Tests:
  - Valid token returns correct Identity (user_id, org_id, role)
  - Missing token → 401
  - Expired token → 401
  - Invalid/tampered token → 401
  - Malformed token → 401
  - Unknown role in otherwise valid token → 401
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api.identity import Identity, get_current_identity
from api.security import create_access_token
from config.settings import Settings, get_settings
from rbac.roles import Role

# ── Helpers ───────────────────────────────────────────────────────────────────


def _strong_settings() -> Settings:
    from pydantic import SecretStr

    return Settings.model_validate(
        {
            "jwt_secret": SecretStr("test-secret-key-that-is-long-enough-32chars"),
            "jwt_algorithm": "HS256",
            "jwt_expiry_seconds": 1800,
        }
    )


def _make_token(user_id: str, org_id: str, role: str, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr("api.security.get_settings", _strong_settings)
    get_settings.cache_clear()
    return create_access_token(user_id=user_id, org_id=org_id, role=role)


# ── Tests ─────────────────────────────────────────────────────────────────────


async def test_valid_token_returns_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.security.get_settings", _strong_settings)
    monkeypatch.setattr("api.identity.decode_token.__module__", "api.security")
    get_settings.cache_clear()

    token = create_access_token(user_id="u1", org_id="acme", role="owner")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Patch decode_token to use the same strong settings
    import api.identity as identity_mod
    import api.security as security_mod

    monkeypatch.setattr(identity_mod, "decode_token", security_mod.decode_token)
    monkeypatch.setattr("api.security.get_settings", _strong_settings)
    get_settings.cache_clear()

    identity = await get_current_identity(credentials=creds)

    assert isinstance(identity, Identity)
    assert identity.user_id == "u1"
    assert identity.org_id == "acme"
    assert identity.role == Role.OWNER


async def test_missing_token_raises_401() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_identity(credentials=None)
    assert exc_info.value.status_code == 401


async def test_expired_token_raises_401(monkeypatch: pytest.MonkeyPatch) -> None:
    import time

    from jose import jwt as jose_jwt
    from pydantic import SecretStr

    secret = "test-secret-key-that-is-long-enough-32chars"
    # Create an already-expired token
    payload = {
        "sub": "u1",
        "org_id": "acme",
        "role": "owner",
        "exp": time.time() - 10,
        "iat": time.time() - 3610,
    }
    expired_token = jose_jwt.encode(payload, secret, algorithm="HS256")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)

    monkeypatch.setattr(
        "api.security.get_settings",
        lambda: Settings.model_validate(
            {"jwt_secret": SecretStr(secret), "jwt_algorithm": "HS256", "jwt_expiry_seconds": 1800}
        ),
    )
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_identity(credentials=creds)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


async def test_bad_signature_raises_401(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic import SecretStr

    monkeypatch.setattr(
        "api.security.get_settings",
        lambda: Settings.model_validate(
            {
                "jwt_secret": SecretStr("signer-secret-long-enough-32-chars-abc"),
                "jwt_algorithm": "HS256",
                "jwt_expiry_seconds": 1800,
            }
        ),
    )
    get_settings.cache_clear()
    token = create_access_token(user_id="u1", org_id="acme", role="owner")

    # Now switch to a different secret for verification
    monkeypatch.setattr(
        "api.security.get_settings",
        lambda: Settings.model_validate(
            {
                "jwt_secret": SecretStr("verifier-secret-long-enough-32-chars-xyz"),
                "jwt_algorithm": "HS256",
                "jwt_expiry_seconds": 1800,
            }
        ),
    )
    get_settings.cache_clear()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_identity(credentials=creds)
    assert exc_info.value.status_code == 401


async def test_malformed_token_raises_401(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic import SecretStr

    monkeypatch.setattr(
        "api.security.get_settings",
        lambda: Settings.model_validate(
            {
                "jwt_secret": SecretStr("test-secret-key-that-is-long-enough-32chars"),
                "jwt_algorithm": "HS256",
                "jwt_expiry_seconds": 1800,
            }
        ),
    )
    get_settings.cache_clear()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="this-is-not-a-jwt")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_identity(credentials=creds)
    assert exc_info.value.status_code == 401


async def test_unknown_role_raises_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """A token with role='superadmin' (not in Role enum) must be rejected."""
    import time

    from jose import jwt as jose_jwt
    from pydantic import SecretStr

    secret = "test-secret-key-that-is-long-enough-32chars"
    payload = {
        "sub": "u1",
        "org_id": "acme",
        "role": "superadmin",  # not a valid Role value
        "exp": time.time() + 3600,
        "iat": time.time(),
    }
    token = jose_jwt.encode(payload, secret, algorithm="HS256")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    monkeypatch.setattr(
        "api.security.get_settings",
        lambda: Settings.model_validate(
            {"jwt_secret": SecretStr(secret), "jwt_algorithm": "HS256", "jwt_expiry_seconds": 1800}
        ),
    )
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_identity(credentials=creds)
    assert exc_info.value.status_code == 401
