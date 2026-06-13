"""
api.identity — Identity model and the get_current_identity FastAPI dependency.

This module is the SOLE gateway through which identity enters the system.

THE ONE INVARIANT (non-negotiable):
    Every endpoint that touches data MUST depend on get_current_identity().
    org_id and role NEVER come from the request body, query params, or any
    header other than the verified JWT.  If they did, the RBAC model from
    Phase 2 would be entirely defeated — any caller could claim any org or
    role.

    WHY this is the only place identity is established:
        Centralising identity extraction in a single FastAPI dependency means:
        a) There is exactly one code path that parses and validates the token.
        b) All audit logging of auth decisions flows through one function.
        c) Any endpoint that skips this dependency is immediately visible in
           review as a policy violation.

Public API
----------
    Identity          — pydantic v2 model: user_id, org_id, role
    get_current_identity — FastAPI dependency → Identity or raises 401
"""

from __future__ import annotations

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.security import InvalidTokenError, TokenExpiredError, decode_token
from rbac.roles import Role

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)


# ── Identity model ────────────────────────────────────────────────────────────


class Identity:
    """Verified identity extracted from a JWT.

    Instances are created only by get_current_identity() after full token
    verification.  There is no public constructor — the only valid source
    of an Identity is a successfully decoded token.

    Attributes:
        user_id: Opaque user identifier (JWT ``sub`` claim).
        org_id:  Tenant identifier — RBAC filter anchor.
        role:    User's role — used for chunk-level access decisions.
    """

    __slots__ = ("org_id", "role", "user_id")

    def __init__(self, user_id: str, org_id: str, role: Role) -> None:
        self.user_id = user_id
        self.org_id = org_id
        self.role = role

    def __repr__(self) -> str:
        return f"Identity(user_id={self.user_id!r}, org_id={self.org_id!r}, role={self.role!r})"


# ── FastAPI dependency ────────────────────────────────────────────────────────


async def get_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008
) -> Identity:
    """FastAPI dependency: extract and verify identity from the Bearer token.

    WHY this is the identity gate:
        This function is the ONLY place in the codebase where org_id and role
        are resolved from a request.  All protected endpoints declare this as
        a dependency.  No endpoint reads org_id/role from the body or params —
        doing so would allow a caller to impersonate any org or escalate their
        role, defeating the Phase 2 RBAC entirely.

    Structured-logs every auth decision (success and failure) to form a
    security audit trail.

    Args:
        credentials: HTTPBearer credential extractor (auto-injected by FastAPI).

    Returns:
        A verified Identity with user_id, org_id, and role.

    Raises:
        HTTPException(401): Missing token, expired token, bad signature,
                            malformed token, or unknown role value.
    """
    if credentials is None:
        logger.warning("identity.missing_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        claims = decode_token(token)
    except TokenExpiredError as exc:
        logger.warning("identity.expired_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InvalidTokenError as exc:
        # Log at WARNING with reason — this is a security audit event.
        # A tampered token (e.g. role claim flipped without re-signing)
        # hits this branch with "Signature verification failed".
        logger.warning("identity.invalid_token", reason=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Map role string to typed Role enum; reject unknown values.
    try:
        role = Role(claims["role"])
    except ValueError as exc:
        logger.warning("identity.unknown_role", role=claims.get("role"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token contains unknown role",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    identity = Identity(
        user_id=str(claims["sub"]),
        org_id=str(claims["org_id"]),
        role=role,
    )
    logger.info(
        "identity.verified",
        user_id=identity.user_id,
        org_id=identity.org_id,
        role=str(identity.role),
    )
    return identity
