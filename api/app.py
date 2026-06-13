"""
api.app — FinRAG FastAPI chain-server.

This is the HTTP entrypoint for the FinRAG system.  It maps to the three
chain-server methods from FINRAG_NVIDIA_ARCHITECTURE.md §2, extended with
JWT auth and RBAC:

  uploadDocument → POST /documents/upload
  generate       → POST /query
  documentSearch → (internal, surfaced via /query)

IDENTITY INVARIANT (enforced at every data endpoint):
    org_id and role are NEVER accepted from request bodies, query params, or
    custom headers.  They come ONLY from the verified JWT via
    get_current_identity().  WHY: accepting identity from user-controlled input
    would defeat the entire Phase 2 RBAC model — any caller could set
    org_id="globex" or role="owner" on the request and read data they are not
    entitled to.  Isolating identity in the JWT (which the server signs) and
    extracting it via a mandatory FastAPI dependency makes this structurally
    impossible, not just policy.

STARTUP CHECK (JWT_SECRET):
    The app refuses to start (via lifespan) if jwt_secret is the placeholder
    default.  A weak or default secret makes the HS256 signature meaningless.

TODO (refresh tokens):
    The /auth/refresh endpoint is a deliberate scope cut for Phase 3.
    Rationale: access tokens are short-lived (default 30 min / set by
    JWT_EXPIRY_SECONDS).  Adding refresh tokens requires a server-side token
    store (to support revocation) and adds surface area for token theft.  Phase
    3 establishes the access-token flow; refresh tokens should be added in a
    dedicated slice when the UI is wired (Phase 3 UI / Phase 4).

Public mounts
-------------
    POST /auth/login           → LoginResponse
    POST /admin/users          → UserCreatedResponse  (owner only)
    POST /documents/upload     → UploadResponse       (any authenticated user)
    POST /query                → QueryResponse        (any authenticated user)
    GET  /healthz              → {"status": "ok"}
"""

import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from api.identity import Identity, get_current_identity
from api.security import create_access_token
from api.users import DuplicateUserError, UserStore, get_user_store
from config.settings import get_settings
from rbac.roles import Role

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ── Startup validation ────────────────────────────────────────────────────────

_PLACEHOLDER_SECRET = "change-me-before-production"


def _assert_strong_jwt_secret() -> None:
    """Fail loud on startup if JWT_SECRET is the placeholder or too short.

    WHY fail-loud (not a warning):
        A default or weak HS256 secret makes ALL token signatures forgeable.
        Running in production with the placeholder would silently undermine
        the entire auth model.  Crashing on startup is the only safe behaviour.
    """
    settings = get_settings()
    secret = settings.jwt_secret.get_secret_value()
    if secret == _PLACEHOLDER_SECRET:
        raise RuntimeError(
            "JWT_SECRET is the placeholder default.  "
            "Set a strong secret (>= 32 bytes of entropy) in your environment.  "
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    if len(secret) < 32:
        raise RuntimeError(f"JWT_SECRET is too short ({len(secret)} chars); minimum is 32 bytes.")


# ── Request / response models (module-level so FastAPI can resolve them) ──────
#
# WHY module-level (not inside create_app):
#     FastAPI uses type introspection to build OpenAPI schemas and to determine
#     whether a parameter is a request body vs a query parameter.  Classes
#     defined inside a closure are not reliably resolved by FastAPI's
#     dependency injection machinery.


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """JWT access token returned on successful login."""

    access_token: str
    token_type: str = "bearer"


class CreateUserRequest(BaseModel):
    """New-user creation request from an org owner.

    WHY no org_id field:
        org_id is forced to the owner's org_id from the JWT.  Accepting
        org_id in the request body would allow an owner to create users
        in arbitrary orgs, breaking tenant isolation.
    """

    email: EmailStr
    password: str = Field(min_length=8)
    role: Role


class UserCreatedResponse(BaseModel):
    """Summary of the newly created user."""

    user_id: str
    email: str
    org_id: str
    role: str


class UploadRequest(BaseModel):
    """Document upload request.

    WHY no org_id field:
        org_id comes from the token.  A user cannot tag a document as
        belonging to a different org.
    """

    doc_name: str = Field(min_length=1)
    text: str = Field(min_length=1)


class UploadResponse(BaseModel):
    """Summary of the ingest operation."""

    doc_id: str
    doc_name: str
    org_id: str
    chunks_ingested: int


class QueryRequest(BaseModel):
    """Natural-language query request.

    WHY no org_id / role fields:
        These come ONLY from the verified JWT via get_current_identity().
        Accepting them from the request body would allow any caller to
        read another org's data or self-promote their role — defeating
        the RBAC model entirely.
    """

    question: str = Field(min_length=1)


class QueryResponse(BaseModel):
    """Query result with org/role echoed from token (never from request)."""

    answer: str
    org_id: str
    role: str
    sources: list[str]


# ── App factory ───────────────────────────────────────────────────────────────


def create_app(*, skip_secret_check: bool = False) -> FastAPI:
    """Build and return the FastAPI application.

    Args:
        skip_secret_check: Set True in tests to bypass the startup secret
                           assertion (tests use a local strong secret anyway).
    """

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        """Run startup validation before accepting requests.

        WHY in lifespan (not at import time):
            Module-level execution runs during test collection, before test
            fixtures can patch JWT_SECRET.  Lifespan runs only when the
            ASGI server actually starts, allowing tests to create the app
            without triggering the production secret check.
        """
        if not skip_secret_check:
            _assert_strong_jwt_secret()
        yield

    application = FastAPI(
        title="FinRAG chain-server",
        description="Multi-tenant financial RAG with JWT auth and chunk-level RBAC.",
        version="0.3.0",
        lifespan=lifespan,
    )

    # ── Structured logging middleware ─────────────────────────────────────────

    @application.middleware("http")
    async def logging_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[JSONResponse]],
    ) -> JSONResponse:
        """Emit a structured log line per request: request_id, path, status, latency."""
        request_id = str(uuid.uuid4())[:8]
        t0 = time.monotonic()
        response = await call_next(request)
        elapsed_ms = round((time.monotonic() - t0) * 1000, 1)
        logger.info(
            "http.request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            elapsed_ms=elapsed_ms,
        )
        return response

    # ── Endpoints ─────────────────────────────────────────────────────────────

    @application.get("/healthz", tags=["ops"])
    async def healthz() -> dict[str, str]:
        """Liveness probe — returns 200 when the service is up."""
        return {"status": "ok"}

    @application.post("/auth/login", response_model=LoginResponse, tags=["auth"])
    async def login(
        body: LoginRequest,
        store: Annotated[UserStore, Depends(get_user_store)],
    ) -> LoginResponse:
        """Authenticate with email + password and receive a JWT access token.

        On success returns a short-lived access token (exp from JWT_EXPIRY_SECONDS).
        On failure returns 401 — same message for bad email and bad password to
        avoid leaking which one is wrong.
        """
        record = store.authenticate(email=str(body.email), password=body.password)
        if record is None:
            logger.warning("auth.login_failed", email=body.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        token = create_access_token(
            user_id=record.user_id,
            org_id=record.org_id,
            role=record.role,
        )
        logger.info("auth.login_ok", user_id=record.user_id, org_id=record.org_id)
        return LoginResponse(access_token=token)

    @application.post(
        "/admin/users",
        response_model=UserCreatedResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["admin"],
    )
    async def admin_create_user(
        body: CreateUserRequest,
        identity: Annotated[Identity, Depends(get_current_identity)],
        store: Annotated[UserStore, Depends(get_user_store)],
    ) -> UserCreatedResponse:
        """Create a new user in the calling owner's org.

        WHY org_id is NOT in the request:
            The new user's org_id is forced to the calling owner's org_id (from
            their JWT).  This guarantees an owner can only provision users within
            their own tenant — there is no request field to forge a different org.

        WHY owner-only:
            Only org owners manage user provisioning.  Allowing HR or employees to
            create accounts would be a privilege escalation path.

        Raises:
            403: Caller is not an owner.
            409: Email already registered.
        """
        # WHY identity.org_id (not body.org_id): org_id comes ONLY from the token.
        if identity.role != Role.OWNER:
            logger.warning(
                "admin.create_user_forbidden",
                user_id=identity.user_id,
                role=str(identity.role),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only org owners can create users",
            )
        try:
            record = store.create_user(
                email=str(body.email),
                password=body.password,
                org_id=identity.org_id,  # WHY: forced from token, never from body
                role=body.role,
            )
        except DuplicateUserError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        return UserCreatedResponse(
            user_id=record.user_id,
            email=record.email,
            org_id=record.org_id,
            role=record.role,
        )

    @application.post("/documents/upload", response_model=UploadResponse, tags=["documents"])
    async def upload_document(
        body: UploadRequest,
        identity: Annotated[Identity, Depends(get_current_identity)],
    ) -> UploadResponse:
        """Ingest a document into the calling user's org.

        Maps to chain-server uploadDocument (FINRAG_NVIDIA_ARCHITECTURE.md §2).

        WHY org_id comes from token (not body):
            A user cannot tag a document as belonging to a different org.
            The token's org_id is the authoritative tenant label for all
            ingested data.

        NOTE: Full Milvus ingest (ingest_and_store) is wired in Phase 4 eval
        slice.  Phase 3 validates the auth/identity flow; returns a stub
        response with correct identity derivation.
        """
        doc_id = str(uuid.uuid4())
        logger.info(
            "documents.upload",
            doc_id=doc_id,
            doc_name=body.doc_name,
            org_id=identity.org_id,  # WHY: always from token, never from body
            user_id=identity.user_id,
        )
        # TODO(Phase 4): wire ingest_and_store(doc_name=body.doc_name, text=body.text,
        #                org_id=identity.org_id, role=identity.role)
        return UploadResponse(
            doc_id=doc_id,
            doc_name=body.doc_name,
            org_id=identity.org_id,  # WHY: from token, not request
            chunks_ingested=0,  # placeholder until Phase 4 wiring
        )

    @application.post("/query", response_model=QueryResponse, tags=["query"])
    async def run_query(
        body: QueryRequest,
        identity: Annotated[Identity, Depends(get_current_identity)],
    ) -> QueryResponse:
        """Answer a question using RBAC-filtered retrieval.

        Maps to chain-server generate (FINRAG_NVIDIA_ARCHITECTURE.md §2).

        WHY org_id and role come from token (not body):
            This is the critical invariant.  The query is scoped to
            identity.org_id and identity.role — values the caller cannot
            forge.  A user with an "acme" token CANNOT reach "globex" data
            because there is no request field to specify a different org.
            Isolation is structural, not just a policy check.

        NOTE: Full Milvus retrieval (answer_query) is wired in Phase 4.
        Phase 3 validates identity derivation and returns a stub response.
        """
        logger.info(
            "query.request",
            user_id=identity.user_id,
            org_id=identity.org_id,  # WHY: from token, not body
            role=str(identity.role),  # WHY: from token, not body
            query_preview=body.question[:80],
        )
        # TODO(Phase 4): wire answer_query(query=body.question, store=..., bm25_index=...,
        #                org_id=identity.org_id, role=identity.role)
        return QueryResponse(
            answer="Query endpoint wired. Full RAG response available in Phase 4.",
            org_id=identity.org_id,  # echoed to prove it comes from token
            role=str(identity.role),  # echoed to prove it comes from token
            sources=[],
        )

    return application


# ── Module-level app instance (for uvicorn) ───────────────────────────────────

app = create_app()
