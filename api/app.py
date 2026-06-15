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

LIFESPAN STORE BOOTSTRAP:
    At startup the lifespan opens a MilvusStore and scans the persisted corpus
    to build an in-memory BM25Index.  This ensures hybrid retrieval's lexical
    half works on a fresh process, not just right after in-process ingest.
    The bootstrap tolerates an empty or absent collection — /query will return
    the graceful "cannot answer" refusal rather than a 500.  If Milvus init
    fails entirely, the app still boots and /query surfaces a 503.

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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from api.identity import Identity, get_current_identity
from api.security import create_access_token
from api.users import DuplicateUserError, UserStore, get_user_store
from config.settings import get_settings
from generation.answer import answer_query
from rbac.roles import Role
from retrieval.bm25 import BM25Index, build_bm25_index
from retrieval.vector_store import MilvusStore

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


class QuerySource(BaseModel):
    """A single verified citation source in the query response."""

    doc_name: str
    page_number: int
    chunk_id: str


class QueryResponse(BaseModel):
    """Query result with org/role echoed from token (never from request)."""

    answer: str
    org_id: str
    role: str
    sources: list[QuerySource]


# ── App-state dependencies ────────────────────────────────────────────────────
#
# WHY module-level (not inside create_app):
#     FastAPI resolves Depends() by function identity.  Defining get_store and
#     get_bm25 here lets tests override them via
#     app.dependency_overrides[get_store] = lambda: my_test_store
#     without needing to re-import from inside the closure.


def get_store(request: Request) -> MilvusStore:
    """Retrieve the long-lived MilvusStore from app.state.

    Raises:
        HTTPException 503: If the store was not initialised at startup (e.g.
            Milvus was unavailable when the process booted).  Callers receive
            a clean error rather than an AttributeError or 500.
    """
    store: MilvusStore | None = getattr(request.app.state, "store", None)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store unavailable — Milvus did not initialise at startup.",
        )
    return store


def get_bm25(request: Request) -> BM25Index:
    """Retrieve the long-lived BM25Index from app.state.

    Raises:
        HTTPException 503: If the index was not built at startup.
    """
    bm25: BM25Index | None = getattr(request.app.state, "bm25", None)
    if bm25 is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BM25 index unavailable — corpus scan did not complete at startup.",
        )
    return bm25


# ── App factory ───────────────────────────────────────────────────────────────


def create_app(*, skip_secret_check: bool = False) -> FastAPI:
    """Build and return the FastAPI application.

    Args:
        skip_secret_check: Set True in tests to bypass the startup secret
                           assertion and the Milvus bootstrap (tests inject
                           store/bm25 via dependency_overrides instead).
    """

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        """Run startup validation and Milvus + BM25 bootstrap.

        WHY in lifespan (not at import time):
            Module-level execution runs during test collection, before test
            fixtures can patch JWT_SECRET.  Lifespan runs only when the
            ASGI server actually starts, allowing tests to create the app
            without triggering the production secret check.

        WHY skip store init when skip_secret_check=True:
            In test mode, tests inject store/bm25 via dependency_overrides.
            Bootstrapping a real MilvusStore would write to the default
            milvus_finrag.db path and slow down the test suite unnecessarily.
        """
        if not skip_secret_check:
            _assert_strong_jwt_secret()
            try:
                store = MilvusStore()
                corpus = store.list_all_chunks()
                bm25 = build_bm25_index(corpus)
                _app.state.store = store
                _app.state.bm25 = bm25
                _app.state.corpus_size = len(corpus)
                if len(corpus) == 0:
                    logger.warning(
                        "lifespan.empty_corpus",
                        msg="BM25 index built over empty corpus — ingest has not run yet.",
                    )
                else:
                    logger.info(
                        "lifespan.store_ready",
                        corpus_size=len(corpus),
                    )
            except Exception as exc:
                logger.error(
                    "lifespan.store_init_failed",
                    error=str(exc),
                    msg="Milvus bootstrap failed; /query will return 503 until resolved.",
                )
                # Do not re-raise — the app boots; /query surfaces a clean 503.
        yield

    application = FastAPI(
        title="FinRAG chain-server",
        description="Multi-tenant financial RAG with JWT auth and chunk-level RBAC.",
        version="0.4.0",
        lifespan=lifespan,
    )

    # ── CORS (local dev UI) ───────────────────────────────────────────────────
    # WHY: the static frontend (web/) is served from a different origin
    # (localhost:5500) than this API (localhost:8000), so the browser requires
    # explicit CORS allow-listing. Scoped to known local origins, not "*".
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
        store: Annotated[MilvusStore, Depends(get_store)],
        bm25: Annotated[BM25Index, Depends(get_bm25)],
    ) -> QueryResponse:
        """Answer a question using RBAC-filtered retrieval.

        Maps to chain-server generate (FINRAG_NVIDIA_ARCHITECTURE.md §2).

        WHY org_id and role come from token (not body):
            This is the critical invariant.  The query is scoped to
            identity.org_id and identity.role — values the caller cannot
            forge.  A user with an "acme" token CANNOT reach "globex" data
            because there is no request field to specify a different org.
            Isolation is structural, not just a policy check.
        """
        logger.info(
            "query.request",
            user_id=identity.user_id,
            org_id=identity.org_id,  # WHY: from token, not body
            role=str(identity.role),  # WHY: from token, not body
            query_preview=body.question[:80],
        )
        result = await answer_query(
            query=body.question,
            store=store,
            bm25_index=bm25,
            org_id=identity.org_id,  # WHY: from verified JWT, never from body
            role=identity.role,  # WHY: from verified JWT, never from body
        )
        # "I cannot answer" refusal passes through as-is with empty sources.
        # The web UI detects this phrase and renders its no-context path.
        sources = [
            QuerySource(
                doc_name=s.doc_name,
                page_number=s.page_number,
                chunk_id=s.chunk_id,
            )
            for s in result.sources
        ]
        return QueryResponse(
            answer=result.answer,
            org_id=identity.org_id,  # echoed to prove it comes from token
            role=str(identity.role),  # echoed to prove it comes from token
            sources=sources,
        )

    return application


# ── Module-level app instance (for uvicorn) ───────────────────────────────────

app = create_app()
