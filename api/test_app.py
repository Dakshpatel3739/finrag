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

RAG WIRING TESTS (Phase 4 /query integration):

  A. Authed /query returns structured QuerySource list (doc_name, page_number,
     chunk_id) when answer_query finds relevant chunks.

  B. ADVERSARIAL RBAC: HR role querying a corpus that contains only restricted
     chunks sees no sources — the Milvus ARRAY_CONTAINS filter and BM25
     post-filter both exclude restricted chunks from HR's result set.

  C. IDENTITY INVARIANT: org_id and role passed in the request body are ignored;
     the values echoed in the response come from the JWT token only.

  D. EMPTY-CORPUS BOOT: app with empty BM25 / empty store still returns the
     graceful "cannot answer" shape, not a 500.
"""

from __future__ import annotations

import base64
import json
import shutil
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from api.app import create_app, get_bm25, get_store
from api.security import create_access_token
from api.users import UserStore, get_user_store
from config.settings import Settings, get_settings
from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
from rbac.roles import Role, sensitivity_to_default_roles
from retrieval.bm25 import BM25Index, build_bm25_index
from retrieval.vector_store import MilvusStore

# ── Test fixtures ─────────────────────────────────────────────────────────────

_SECRET = "test-strong-secret-32-chars-abcde"
_TEST_DIM = 8


def _test_settings() -> Settings:
    return Settings.model_validate(
        {
            "jwt_secret": SecretStr(_SECRET),
            "jwt_algorithm": "HS256",
            "jwt_expiry_seconds": 1800,
        }
    )


def _fake_embedding(seed: int = 0) -> list[float]:
    return [float((seed + i) % 10) / 10.0 for i in range(_TEST_DIM)]


def _make_chunk(
    idx: int,
    text: str,
    doc_name: str,
    page: int,
    org_id: str,
    sensitivity: SensitivityLevel,
) -> Chunk:
    roles = [str(r) for r in sensitivity_to_default_roles(sensitivity)]
    return Chunk(
        chunk_id=make_chunk_id(f"{org_id}_api_test", page, idx),
        doc_id=f"{org_id}_api_doc",
        doc_name=doc_name,
        page_number=page,
        section="Test",
        org_id=org_id,
        allowed_roles=roles,
        sensitivity_level=sensitivity,
        text=text,
        content_type=ContentType.TEXT,
        embedding=_fake_embedding(seed=idx),
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


def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch JWT settings to the test secret and clear the settings cache.

    MUST be called BEFORE create_access_token in any test that calls /query.
    WHY: create_access_token signs with get_settings().jwt_secret; the server
    verifies with the same function.  If the cache holds the real secret when
    the token is signed but the test secret when the token is verified (or
    vice-versa), every request returns 401 with 'Signature verification failed'.
    """
    monkeypatch.setattr("api.security.get_settings", _test_settings)
    monkeypatch.setattr("api.app.get_settings", _test_settings)
    get_settings.cache_clear()


def _make_authed_client(
    monkeypatch: pytest.MonkeyPatch,
    mock_store: MilvusStore | None = None,
    mock_bm25: BM25Index | None = None,
) -> TestClient:
    """Create a TestClient with mocked store/bm25 for /query tests.

    Callers MUST call _patch_settings(monkeypatch) before creating any tokens.
    """
    application = create_app(skip_secret_check=True)

    # Inject store and bm25 via dependency_overrides so the route doesn't 503.
    # WHY: skip_secret_check=True means lifespan skips MilvusStore bootstrap;
    # tests inject their own store/bm25 here.
    _store = mock_store
    _bm25 = mock_bm25 if mock_bm25 is not None else build_bm25_index([])
    application.dependency_overrides[get_store] = lambda: _store
    application.dependency_overrides[get_bm25] = lambda: _bm25

    return TestClient(application)


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
    from generation.citations import AnswerWithCitations, CitationSource

    _patch_settings(monkeypatch)
    token = create_access_token(user_id="u1", org_id="acme", role="owner")
    client = _make_authed_client(monkeypatch)

    with patch(
        "api.app.answer_query",
        new_callable=AsyncMock,
        return_value=AnswerWithCitations(
            answer="Revenue was $1B.",
            sources=[CitationSource(doc_name="10k.pdf", page_number=1, chunk_id="abc123")],
        ),
    ):
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
    answer_query will receive role=hr and restrict accordingly.
    """
    from generation.citations import AnswerWithCitations

    _patch_settings(monkeypatch)
    hr_token = create_access_token(user_id="hr-user", org_id="acme", role="hr")
    client = _make_authed_client(monkeypatch)

    with patch(
        "api.app.answer_query",
        new_callable=AsyncMock,
        return_value=AnswerWithCitations(answer="No context.", sources=[]),
    ):
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
    from generation.citations import AnswerWithCitations

    _patch_settings(monkeypatch)
    acme_token = create_access_token(user_id="acme-user", org_id="acme", role="owner")
    client = _make_authed_client(monkeypatch)

    with patch(
        "api.app.answer_query",
        new_callable=AsyncMock,
        return_value=AnswerWithCitations(answer="Acme only.", sources=[]),
    ) as mock_aq:
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
    # answer_query was called with org_id from token, not from body
    _, call_kwargs = mock_aq.call_args
    assert call_kwargs["org_id"] == "acme", (
        "IDENTITY INVARIANT FAILURE: answer_query received org_id != token's org_id."
    )


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


# ═══════════════════════════════════════════════════════════════════════════════
# RAG WIRING TESTS (Phase 4 /query integration)
# ═══════════════════════════════════════════════════════════════════════════════


# ── Test A: structured sources returned ───────────────────────────────────────


def test_query_returns_structured_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    """RAG WIRING A — /query maps AnswerWithCitations to list[QuerySource].

    Verifies that:
    - The response has doc_name, page_number, chunk_id in each source.
    - The answer text passes through unchanged.
    - org_id and role echo from the token, not from any request field.
    """
    from generation.citations import AnswerWithCitations, CitationSource

    _patch_settings(monkeypatch)
    owner_token = create_access_token(user_id="u1", org_id="acme", role="owner")
    client = _make_authed_client(monkeypatch)

    expected_source = CitationSource(
        doc_name="annual_report.pdf",
        page_number=5,
        chunk_id="deadbeef01234567",
    )
    with patch(
        "api.app.answer_query",
        new_callable=AsyncMock,
        return_value=AnswerWithCitations(
            answer="Revenue was $26 billion [1].",
            sources=[expected_source],
        ),
    ):
        r = client.post(
            "/query",
            json={"question": "What is revenue?"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "Revenue was $26 billion [1]."
    assert data["org_id"] == "acme"
    assert data["role"] == "owner"
    assert len(data["sources"]) == 1
    src = data["sources"][0]
    assert src["doc_name"] == "annual_report.pdf"
    assert src["page_number"] == 5
    assert src["chunk_id"] == "deadbeef01234567"


# ── Test B: ADVERSARIAL RBAC — HR cannot see restricted sources ───────────────


def test_adversarial_rbac_hr_no_restricted_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ADVERSARIAL RBAC B — HR role never receives restricted sources.

    Architecture:
    - A real Milvus Lite store contains one RESTRICTED chunk (allowed_roles=
      ["owner","finance"]) and one INTERNAL chunk (allowed_roles includes "hr").
    - HR token calls /query.
    - Milvus ARRAY_CONTAINS filter excludes the restricted chunk from dense hits.
    - BM25 post-filter in document_search excludes the restricted chunk from
      lexical hits.
    - The restricted doc_name must not appear anywhere in the response sources.

    NIM calls (embed_texts, rerank, generate) are mocked — only the Milvus
    RBAC filter and BM25 post-filter are exercised.
    """
    collection = "api_rbac_test"
    fake_vec = [1.0] + [0.0] * (_TEST_DIM - 1)

    restricted_chunk = _make_chunk(
        idx=0,
        text="Executive compensation table: CEO salary $34,200,000.",
        doc_name="restricted_doc.pdf",
        page=1,
        org_id="acme",
        sensitivity=SensitivityLevel.RESTRICTED,
    )
    restricted_chunk = restricted_chunk.model_copy(update={"embedding": fake_vec})

    internal_chunk = _make_chunk(
        idx=1,
        text="Annual report highlights revenue growth.",
        doc_name="internal_doc.pdf",
        page=2,
        org_id="acme",
        sensitivity=SensitivityLevel.INTERNAL,
    )
    internal_chunk = internal_chunk.model_copy(update={"embedding": fake_vec})

    db_path = tmp_path / "rbac_api_test.db"
    store = MilvusStore(uri=str(db_path), collection_name=collection)
    store.ensure_collection(dim=_TEST_DIM)
    store.insert_chunks([restricted_chunk, internal_chunk])
    bm25 = build_bm25_index([restricted_chunk, internal_chunk])

    _patch_settings(monkeypatch)
    hr_token = create_access_token(user_id="hr-user", org_id="acme", role="hr")
    client = _make_authed_client(monkeypatch, mock_store=store, mock_bm25=bm25)

    embed_target = "retrieval.search.embed_texts"
    rerank_target = "retrieval.search.rerank"
    gen_target = "generation.answer.generate"

    async def _fake_embed(texts: list[str], **kwargs: Any) -> list[list[float]]:
        return [fake_vec for _ in texts]

    async def _fake_rerank(query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]:
        return chunks[:top_n]

    with (
        patch(embed_target, side_effect=_fake_embed),
        patch(rerank_target, side_effect=_fake_rerank),
        patch(
            gen_target,
            new_callable=AsyncMock,
            return_value="I cannot answer this question from the provided documents.",
        ),
    ):
        r = client.post(
            "/query",
            json={"question": "salary compensation"},
            headers={"Authorization": f"Bearer {hr_token}"},
        )

    assert r.status_code == 200
    data = r.json()
    # HR must not receive any restricted source in the response
    source_doc_names = {s["doc_name"] for s in data["sources"]}
    assert "restricted_doc.pdf" not in source_doc_names, (
        "SECURITY FAILURE: HR role received a restricted source in the query response. "
        f"Sources returned: {data['sources']}"
    )

    # Cleanup
    if db_path.exists():
        shutil.rmtree(str(db_path), ignore_errors=True)


# ── Test C: IDENTITY INVARIANT — body fields ignored ─────────────────────────


def test_identity_invariant_body_fields_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """IDENTITY INVARIANT C — org_id and role from body are silently ignored.

    Phase-3 invariant: even if a client injects org_id or role in the request
    body (or extra JSON keys), the response must echo the token's values only.
    answer_query must receive org_id and role from the JWT, not from the body.
    """
    from generation.citations import AnswerWithCitations

    _patch_settings(monkeypatch)
    finance_token = create_access_token(user_id="f1", org_id="acme", role="finance")
    client = _make_authed_client(monkeypatch)

    with patch(
        "api.app.answer_query",
        new_callable=AsyncMock,
        return_value=AnswerWithCitations(answer="Revenue data.", sources=[]),
    ) as mock_aq:
        r = client.post(
            "/query",
            # Body attempts to inject org_id="globex" and role="owner"
            json={
                "question": "financial summary",
                "org_id": "globex",
                "role": "owner",
            },
            headers={"Authorization": f"Bearer {finance_token}"},
        )

    assert r.status_code == 200
    data = r.json()
    # Response must echo token values, not body values
    assert data["org_id"] == "acme", (
        f"IDENTITY FAILURE: org_id in response was {data['org_id']!r}, expected 'acme' from token."
    )
    assert data["role"] == "finance", (
        f"IDENTITY FAILURE: role in response was {data['role']!r}, expected 'finance' from token."
    )
    # answer_query was called with token's identity, not body fields
    _, call_kwargs = mock_aq.call_args
    assert call_kwargs["org_id"] == "acme"
    assert str(call_kwargs["role"]) == "finance"


# ── Test D: EMPTY-CORPUS BOOT ─────────────────────────────────────────────────


def test_empty_corpus_boot_returns_graceful_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EMPTY-CORPUS BOOT D — app with empty BM25/store returns graceful refusal.

    When the BM25 index has no chunks (corpus hasn't been ingested yet), the
    pipeline must not crash.  answer_query returns the "cannot answer" refusal
    with empty sources, and the API returns 200 with that shape.
    """
    _patch_settings(monkeypatch)
    owner_token = create_access_token(user_id="u1", org_id="acme", role="owner")

    application = create_app(skip_secret_check=True)
    empty_bm25 = build_bm25_index([])

    # Use a MagicMock for the store — the mock answer_query won't actually call it
    from unittest.mock import MagicMock

    mock_store = MagicMock(spec=MilvusStore)
    application.dependency_overrides[get_store] = lambda: mock_store
    application.dependency_overrides[get_bm25] = lambda: empty_bm25
    client = TestClient(application)

    from generation.citations import AnswerWithCitations

    with patch(
        "api.app.answer_query",
        new_callable=AsyncMock,
        return_value=AnswerWithCitations(
            answer="I cannot answer this question from the provided documents.",
            sources=[],
        ),
    ):
        r = client.post(
            "/query",
            json={"question": "What is revenue?"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

    assert r.status_code == 200
    data = r.json()
    assert "cannot answer" in data["answer"].lower()
    assert data["sources"] == []
