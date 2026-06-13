"""
api.test_app — FastAPI TestClient tests + adversarial auth suite.

Standard tests:
  - GET /healthz → 200
  - POST /auth/login happy path → token
  - POST /auth/login wrong password → 401
  - Protected endpoint without token → 401
  - Protected endpoint with valid token → 200/201

ADVERSARIAL AUTH TESTS (the core security proof):

  1. FORGED ROLE: a user with role=hr cannot access restricted data.  Even if
     they craft a request, there is no role field to elevate — the role comes
     only from the JWT.  The query endpoint echoes the token's role; assert it
     stays "hr".

  2. TOKEN TAMPERING: take a valid hr token, flip the role claim to "owner"
     WITHOUT re-signing → the signature check rejects it (401).  This is the
     key proof: you cannot self-promote without the signing secret.

  3. CROSS-TENANT: an acme-token user hits /query.  The response org_id is
     forced to "acme" from the token — there is NO request field to specify
     "globex".  Globex data is unreachable by construction.

  4. WRONG SECRET: a token signed with a different secret → 401.

  5. EXPIRED TOKEN: an expired token on /query → 401.

  6. NON-OWNER CREATE USER: role=employee and role=hr tokens calling
     /admin/users → 403; only owner can provision.
"""

from __future__ import annotations

import base64
import json
import time

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from api.app import create_app
from api.security import create_access_token
from api.users import UserStore, get_user_store
from config.settings import Settings, get_settings
from rbac.roles import Role

# ── Test fixtures ─────────────────────────────────────────────────────────────

_SECRET = "test-strong-secret-32-chars-abcde"


def _test_settings() -> Settings:
    return Settings.model_validate(
        {
            "jwt_secret": SecretStr(_SECRET),
            "jwt_algorithm": "HS256",
            "jwt_expiry_seconds": 1800,
        }
    )


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient backed by a fresh in-memory user store and test JWT settings."""
    # Patch settings everywhere they are used
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    monkeypatch.setattr("api.app.get_settings", _test_settings)
    get_settings.cache_clear()

    # Fresh in-memory user store per test
    store = UserStore(db_path=":memory:")
    get_user_store.cache_clear()
    monkeypatch.setattr("api.app.get_user_store", lambda: store)
    monkeypatch.setattr("api.users.get_user_store", lambda: store)

    application = create_app(skip_secret_check=True)
    # Override the app's dependency to also use the in-memory store

    application.dependency_overrides[get_user_store] = lambda: store

    return TestClient(application, raise_server_exceptions=True)


def _token(org_id: str, role: str, monkeypatch: pytest.MonkeyPatch) -> str:
    """Helper: create a signed token using the test secret."""
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()
    return create_access_token(user_id=f"user-{org_id}-{role}", org_id=org_id, role=role)


def _seed_owner(store: UserStore) -> None:
    """Seed an acme owner into the store."""
    store.create_user(
        email="owner@acme.com", password="Str0ng!Pass", org_id="acme", role=Role.OWNER
    )


# ── Healthz ───────────────────────────────────────────────────────────────────


def test_healthz(app: TestClient) -> None:
    r = app.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ── Login ─────────────────────────────────────────────────────────────────────


def test_login_happy_path(app: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Seed a user into the store
    store = UserStore(db_path=":memory:")
    store.create_user(email="alice@acme.com", password="Secret1234", org_id="acme", role=Role.OWNER)
    monkeypatch.setattr("api.app.get_user_store", lambda: store)

    application = create_app(skip_secret_check=True)
    application.dependency_overrides[get_user_store] = lambda: store
    client = TestClient(application)

    r = client.post("/auth/login", json={"email": "alice@acme.com", "password": "Secret1234"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(app: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    store = UserStore(db_path=":memory:")
    store.create_user(
        email="alice@acme.com", password="RealPassword", org_id="acme", role=Role.OWNER
    )
    monkeypatch.setattr("api.app.get_user_store", lambda: store)

    application = create_app(skip_secret_check=True)
    application.dependency_overrides[get_user_store] = lambda: store
    client = TestClient(application)

    r = client.post("/auth/login", json={"email": "alice@acme.com", "password": "WrongPassword"})
    assert r.status_code == 401


def test_login_unknown_email(app: TestClient) -> None:
    r = app.post("/auth/login", json={"email": "nobody@acme.com", "password": "whatever"})
    assert r.status_code == 401


# ── Protected endpoints without token ─────────────────────────────────────────


def test_query_without_token_is_401(app: TestClient) -> None:
    r = app.post("/query", json={"question": "What is revenue?"})
    assert r.status_code == 401


def test_upload_without_token_is_401(app: TestClient) -> None:
    r = app.post("/documents/upload", json={"doc_name": "10k.pdf", "text": "hello"})
    assert r.status_code == 401


def test_admin_create_user_without_token_is_401(app: TestClient) -> None:
    r = app.post(
        "/admin/users",
        json={"email": "new@acme.com", "password": "StrongPass1!", "role": "employee"},
    )
    assert r.status_code == 401


# ── Protected endpoints with valid token ──────────────────────────────────────


def test_query_with_valid_token_is_200(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    token = create_access_token(user_id="u1", org_id="acme", role="owner")
    app = create_app(skip_secret_check=True)
    client = TestClient(app)

    r = client.post(
        "/query",
        json={"question": "What is revenue?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


def test_upload_with_valid_token_is_200(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    token = create_access_token(user_id="u1", org_id="acme", role="owner")
    app = create_app(skip_secret_check=True)
    client = TestClient(app)

    r = client.post(
        "/documents/upload",
        json={"doc_name": "10k.pdf", "text": "Annual revenue was $1B."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL AUTH TESTS
# ═══════════════════════════════════════════════════════════════════════════════


# ── Adversarial #1: FORGED ROLE ───────────────────────────────────────────────


def test_adversarial_forged_role_stays_hr(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADVERSARIAL #1 — FORGED ROLE: An HR user cannot elevate their role.

    Even if an HR user crafts a request to /query, there is no 'role' field
    in the request body.  The role in the response is the one from the JWT.
    Assert the response echoes 'hr', not 'owner'.  The RBAC filter in
    answer_query (Phase 4 wiring) will receive role=hr and restrict
    accordingly.
    """
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    hr_token = create_access_token(user_id="hr-user", org_id="acme", role="hr")
    app = create_app(skip_secret_check=True)
    client = TestClient(app)

    # Attempt to pass role in the body — no such field in QueryRequest, so it's
    # ignored by pydantic.  The response must show role="hr" from the token.
    r = client.post(
        "/query",
        json={"question": "What are the salary tables?", "role": "owner", "org_id": "acme"},
        headers={"Authorization": f"Bearer {hr_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    # The role echoed back is from the token, never from the request body
    assert data["role"] == "hr", (
        f"SECURITY FAILURE: role in response was {data['role']!r}, expected 'hr'. "
        "Identity must come only from the JWT, not the request body."
    )
    assert data["org_id"] == "acme"


# ── Adversarial #2: TOKEN TAMPERING ───────────────────────────────────────────


def test_adversarial_tampered_role_claim_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADVERSARIAL #2 — TOKEN TAMPERING: Flipping role to 'owner' without re-signing.

    An attacker holds a valid HR token.  They decode the payload, change
    role='owner', re-encode without re-signing (keeping the original signature).
    The HMAC signature check must reject this with 401.

    This is the key security proof: the ONLY way to forge a role is to know
    the JWT_SECRET.
    """
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    hr_token = create_access_token(user_id="hr-user", org_id="acme", role="hr")
    app = create_app(skip_secret_check=True)
    client = TestClient(app)

    # Tamper: decode payload, flip role, re-encode, keep original signature
    header_b64, payload_b64, signature = hr_token.split(".")

    # Decode the payload (add padding if needed)
    padding = "=" * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 else ""
    payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
    payload_dict = json.loads(payload_bytes)

    # Escalate role claim to 'owner'
    payload_dict["role"] = "owner"
    tampered_payload = (
        base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).rstrip(b"=").decode()
    )
    tampered_token = f"{header_b64}.{tampered_payload}.{signature}"

    r = client.post(
        "/query",
        json={"question": "salary tables"},
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert r.status_code == 401, (
        "SECURITY FAILURE: Tampered token (role flipped to 'owner' without re-signing) "
        f"was accepted with status {r.status_code}. "
        "Signature verification must reject any token whose payload has been modified."
    )


# ── Adversarial #3: CROSS-TENANT ──────────────────────────────────────────────


def test_adversarial_cross_tenant_impossible(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADVERSARIAL #3 — CROSS-TENANT: acme token cannot reach globex data.

    An acme user calls /query.  The response org_id is forced to 'acme' from
    the token.  There is NO request field to specify 'globex'.  Isolation is
    structural — it is impossible to craft a request that scopes a query to a
    different org, because org_id has no request representation.
    """
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    acme_token = create_access_token(user_id="acme-user", org_id="acme", role="owner")
    app = create_app(skip_secret_check=True)
    client = TestClient(app)

    # Attempt to scope to globex via every possible vector
    r = client.post(
        "/query",
        # Body has no org_id field, but even if it did, it would be ignored
        json={"question": "globex financials", "org_id": "globex"},
        headers={
            "Authorization": f"Bearer {acme_token}",
            "X-Org-Id": "globex",  # custom header — ignored
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["org_id"] == "acme", (
        f"SECURITY FAILURE: org_id in response was {data['org_id']!r}. "
        "Cross-tenant isolation breach: acme token scoped to globex. "
        "org_id must come ONLY from the JWT, never from request input."
    )
    # Role also comes from token
    assert data["role"] == "owner"


# ── Adversarial #4: WRONG SECRET ──────────────────────────────────────────────


def test_adversarial_wrong_secret_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADVERSARIAL #4 — WRONG SECRET: Token signed with a different secret → 401."""
    from jose import jwt as jose_jwt

    wrong_secret = "wrong-secret-completely-different-abc123"

    # Sign token with the wrong secret
    payload = {
        "sub": "attacker",
        "org_id": "acme",
        "role": "owner",
        "exp": time.time() + 3600,
        "iat": time.time(),
    }
    bad_token = jose_jwt.encode(payload, wrong_secret, algorithm="HS256")

    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    app = create_app(skip_secret_check=True)
    client = TestClient(app)

    r = client.post(
        "/query",
        json={"question": "financials"},
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert r.status_code == 401, (
        f"SECURITY FAILURE: Token signed with wrong secret accepted (status {r.status_code}). "
        "HS256 signature must be verified against the server's JWT_SECRET."
    )


# ── Adversarial #5: EXPIRED TOKEN ─────────────────────────────────────────────


def test_adversarial_expired_token_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADVERSARIAL #5 — EXPIRED TOKEN: expired token on /query → 401."""
    from jose import jwt as jose_jwt

    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    # Craft an already-expired token
    payload = {
        "sub": "u1",
        "org_id": "acme",
        "role": "owner",
        "exp": time.time() - 10,  # expired 10 seconds ago
        "iat": time.time() - 1810,
    }
    expired_token = jose_jwt.encode(payload, _SECRET, algorithm="HS256")

    app = create_app(skip_secret_check=True)
    client = TestClient(app)

    r = client.post(
        "/query",
        json={"question": "revenue"},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert r.status_code == 401, (
        f"SECURITY FAILURE: Expired token accepted (status {r.status_code}). "
        "Short-lived tokens protect against stolen-token abuse — exp must be enforced."
    )


# ── Adversarial #6: NON-OWNER CREATE USER ─────────────────────────────────────


@pytest.mark.parametrize("role", ["employee", "hr", "finance"])
def test_adversarial_non_owner_cannot_create_user(
    role: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ADVERSARIAL #6 — NON-OWNER CREATE USER: Only owner can provision users.

    An employee, hr, or finance token calling POST /admin/users must receive
    403.  Allowing non-owners to provision accounts would be a privilege
    escalation path.
    """
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    token = create_access_token(user_id=f"{role}-user", org_id="acme", role=role)
    app = create_app(skip_secret_check=True)
    store = UserStore(db_path=":memory:")
    app.dependency_overrides[get_user_store] = lambda: store
    client = TestClient(app)

    r = client.post(
        "/admin/users",
        json={"email": "new@acme.com", "password": "StrongPass1!", "role": "employee"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403, (
        f"SECURITY FAILURE: role={role} was allowed to create users (status {r.status_code}). "
        "Only org owners may provision users — non-owner access to /admin/users is a "
        "privilege escalation path."
    )


def test_owner_can_create_user_in_own_org(monkeypatch: pytest.MonkeyPatch) -> None:
    """Owner-only provisioning: owner creates user; new user's org_id = owner's org_id."""
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    owner_token = create_access_token(user_id="owner-1", org_id="acme", role="owner")
    app = create_app(skip_secret_check=True)
    store = UserStore(db_path=":memory:")
    app.dependency_overrides[get_user_store] = lambda: store
    client = TestClient(app)

    r = client.post(
        "/admin/users",
        json={"email": "newhr@acme.com", "password": "StrongPass1!", "role": "hr"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["org_id"] == "acme"  # WHY: forced from token, never from request
    assert data["role"] == "hr"
    assert data["email"] == "newhr@acme.com"


def test_owner_cannot_create_user_in_other_org(monkeypatch: pytest.MonkeyPatch) -> None:
    """Owner's new user is always in owner's org, even if body tries to set another org.

    The CreateUserRequest has no org_id field, so it is structurally impossible
    to set org_id to 'globex' when the owner's token says 'acme'.
    """
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    get_settings.cache_clear()

    acme_owner_token = create_access_token(user_id="owner-acme", org_id="acme", role="owner")
    app = create_app(skip_secret_check=True)
    store = UserStore(db_path=":memory:")
    app.dependency_overrides[get_user_store] = lambda: store
    client = TestClient(app)

    # Even if globex is added to the body, CreateUserRequest ignores unknown fields
    r = client.post(
        "/admin/users",
        json={
            "email": "spy@globex.com",
            "password": "StrongPass1!",
            "role": "employee",
            "org_id": "globex",  # extra field — must be ignored
        },
        headers={"Authorization": f"Bearer {acme_owner_token}"},
    )
    assert r.status_code == 201
    data = r.json()
    # org_id MUST be "acme" (from token), never "globex" (from body)
    assert data["org_id"] == "acme", (
        f"SECURITY FAILURE: org_id was {data['org_id']!r}. "
        "New user's org_id must be forced to the owner's org_id from the JWT."
    )
