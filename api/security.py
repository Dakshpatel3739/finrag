"""
api.security — password hashing and JWT primitives.

This module owns all cryptographic operations:
  - Slow password hashing (argon2 via passlib) for storage and verification.
  - JWT creation and verified decode (HS256 via python-jose).

WHY argon2 (slow hash, not sha/md5):
    Fast hashes let an attacker test billions of candidate passwords per second
    on a GPU after stealing the hash database.  Argon2 is memory-hard and
    CPU-hard by design — even with a leaked DB, offline brute-force is
    computationally infeasible.  Salt is generated automatically per-hash by
    the passlib CryptContext.

WHY HS256 (symmetric HMAC):
    FinRAG is a single-issuer service — the same process issues and verifies
    tokens.  HS256 is simpler and faster than RSA/ECDSA for this topology.
    The secret MUST be >= 32 bytes of high-entropy randomness (see startup
    check in app.py).

WHY short-lived access tokens (30 min default):
    Short expiry bounds the window of misuse if a token is stolen.  The cost
    is that clients must re-authenticate periodically.  Refresh tokens extend
    usability without widening the stolen-token window.

Public API
----------
    hash_password(plain) -> str
    verify_password(plain, hashed) -> bool
    create_access_token(identity) -> str
    decode_token(token) -> dict[str, Any]

    AuthError          — base auth exception
    TokenExpiredError  — token past exp
    InvalidTokenError  — bad signature / malformed / missing claims
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from config.settings import get_settings

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# WHY bcrypt fallback: argon2 requires the argon2-cffi C extension.  If the
# extension is unavailable (e.g. a stripped container) passlib falls back to
# bcrypt, which is also a slow hash.  Both defeat offline brute-force.
_PWD_CONTEXT = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


# ── Exceptions ────────────────────────────────────────────────────────────────


class AuthError(Exception):
    """Base class for all authentication errors."""


class TokenExpiredError(AuthError):
    """JWT access token has passed its exp claim."""


class InvalidTokenError(AuthError):
    """JWT is malformed, has a bad signature, or is missing required claims."""


# ── Password hashing ─────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Return the argon2 hash of *plain*.

    The CryptContext generates a unique random salt per call and encodes it
    into the returned hash string — callers never manage salts directly.

    Args:
        plain: The raw password string (UTF-8).

    Returns:
        A passlib hash string that encodes algorithm, params, salt, and digest.
    """
    return str(_PWD_CONTEXT.hash(plain))


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison of *plain* against a stored *hashed* value.

    WHY constant-time: a naive ``hmac(plain) == stored`` comparison leaks
    timing information about how many prefix bytes match.  The passlib
    verify() function uses a constant-time compare to prevent this
    side-channel.

    Args:
        plain:  Candidate password from the login request.
        hashed: Stored hash string (from hash_password).

    Returns:
        True if the password matches; False otherwise.
    """
    return bool(_PWD_CONTEXT.verify(plain, hashed))


# ── JWT ───────────────────────────────────────────────────────────────────────


def create_access_token(
    user_id: str,
    org_id: str,
    role: str,
) -> str:
    """Sign and return a short-lived JWT access token.

    Claims embedded:
      sub  — user_id (the token subject)
      org_id, role — identity claims; these are the ONLY authoritative source
                     of org_id/role in the system.  No endpoint may accept
                     these from request input.
      iat  — issued-at (UTC)
      exp  — expiry (UTC, now + jwt_expiry_seconds from settings)

    WHY identity claims in JWT (not a DB lookup on every request):
        Embedding org_id + role avoids a DB round-trip per request.  The
        signature guarantees the claims are unmodified since issuance.
        Revocation (e.g. role change) takes effect at next login — acceptable
        given short token lifetimes.

    Args:
        user_id: Opaque unique identifier for the user.
        org_id:  Tenant identifier — embedded so endpoints cannot be given a
                 different org by the caller.
        role:    User's role string (e.g. "owner", "hr").

    Returns:
        A compact JWT string (header.payload.signature).
    """
    settings = get_settings()
    now = datetime.now(tz=UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "org_id": org_id,
        "role": role,
        "iat": now,
        "exp": now.timestamp() + settings.jwt_expiry_seconds,
    }
    token: str = jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    logger.debug("security.token_created", user_id=user_id, org_id=org_id, role=role)
    return token


def decode_token(token: str) -> dict[str, Any]:
    """Decode and fully verify a JWT access token.

    Verification steps performed by python-jose:
      1. Signature verification (HS256 with jwt_secret).
      2. Expiry check (exp claim).
      3. Structural well-formedness.

    Required claims: sub, org_id, role.  Missing claims → InvalidTokenError.

    Args:
        token: Compact JWT string from the Authorization header.

    Returns:
        Verified payload dict with at minimum: sub, org_id, role, exp, iat.

    Raises:
        TokenExpiredError:  exp is in the past.
        InvalidTokenError:  bad signature, malformed, or missing claims.
    """
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as exc:
        logger.warning("security.token_expired")
        raise TokenExpiredError("Access token has expired") from exc
    except JWTError as exc:
        # Covers: bad signature, malformed header/payload, invalid algorithm
        logger.warning("security.token_invalid", reason=str(exc))
        raise InvalidTokenError(f"Token verification failed: {exc}") from exc

    # Validate required identity claims are present
    for claim in ("sub", "org_id", "role"):
        if claim not in payload:
            logger.warning("security.token_missing_claim", claim=claim)
            raise InvalidTokenError(f"Token missing required claim: {claim}")

    return payload
