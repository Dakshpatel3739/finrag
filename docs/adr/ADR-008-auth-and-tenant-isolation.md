# ADR-008 — Auth and Tenant Isolation

**Status:** Accepted
**Date:** 2026-06-13
**Phase:** 3

---

## Context

Phase 2 implemented chunk-level RBAC enforced at retrieval time.  However, the
`(org_id, role)` pair was passed as function arguments — callers were trusted to
provide correct values.  In a real HTTP deployment, this means the API layer
could accept `org_id` and `role` from the request, which would allow any caller
to impersonate any tenant or escalate their role.

Phase 3 makes identity **unforgeable** by requiring that it flow exclusively from
a cryptographically-signed JWT.

---

## The Core Invariant

**The API layer NEVER accepts `org_id` or `role` from request bodies, query params,
or custom headers.  Identity comes ONLY from the verified JWT.**

If `org_id` or `role` could be set in a request, the entire RBAC model from Phase 2
is defeated.  Any caller could claim `role="owner"` or `org_id="globex"` and bypass
all access controls.  The JWT signature makes claims unforgeable without the secret.

---

## Decisions

### 1. JWT / HS256

**Chosen:** `python-jose` with HS256 (HMAC-SHA256).

**Rationale:** FinRAG is a single-issuer service — the same process that issues tokens
also verifies them.  HS256 is simpler and faster than asymmetric algorithms (RS256,
ES256), which are warranted only when tokens must be verified by a separate party
(e.g. a microservice that does not hold the private key).  For this architecture, the
added complexity of asymmetric keys provides no benefit.

**Trade-off:** HS256 requires the secret to be kept confidential.  A leaked secret
allows an attacker to forge arbitrary tokens.  Mitigated by: (a) startup assertion
that rejects a short or placeholder secret, (b) short token lifetime (see §3).

**Alternatives considered:**
- RS256: Appropriate for distributed multi-issuer systems.  Overkill here.
- Opaque tokens + server-side session store: Enables instant revocation but
  requires a persistent session DB and adds per-request latency for lookup.
  Deferred to a future slice if revocation is required.

---

### 2. Short-lived access tokens (30 min default)

**Chosen:** `jwt_expiry_seconds=1800` (30 minutes), configurable via `JWT_EXPIRY_SECONDS`.

**Rationale:** If a token is stolen (e.g. from a browser memory dump, log file, or
network intercept), short expiry bounds the misuse window.  A 30-minute token means
an attacker has at most 30 minutes to use a captured token before it expires.

**Refresh token decision (deliberate scope cut):**
Phase 3 implements access tokens only.  Refresh tokens require a server-side revocation
store to be meaningful (otherwise a stolen refresh token simply extends the attack
window).  Adding a refresh flow is scoped to the UI integration slice (post-Phase 3),
when the full login UX is designed.  Until then, users re-authenticate at token expiry.

---

### 3. Argon2 password hashing (via passlib)

**Chosen:** `passlib[argon2]` with `bcrypt` fallback.

**Rationale:** Fast hashes (SHA-256, MD5, bcrypt at low cost factors) allow offline
brute-force at billions of guesses/second using a GPU after a database breach.
Argon2 is memory-hard and CPU-hard by design — it is the winner of the Password
Hashing Competition (2015) and is the recommended choice in OWASP guidelines.

**Why passlib over calling argon2-cffi directly:**
passlib encodes algorithm, version, parameters, salt, and hash into a single portable
string.  It handles salt generation, algorithm negotiation, and parameter tuning
transparently.  Callers never touch raw salts or binary digests.

**Alternatives considered:**
- bcrypt: Good but older; vulnerable to the `$2x$` prefix bug in some implementations.
  Retained as passlib's fallback if argon2-cffi is unavailable.
- scrypt: Also memory-hard; less standardised tooling than argon2.
- PBKDF2-HMAC: NIST-approved; not memory-hard; GPU-parallelisable.

---

### 4. Identity-only invariant (the threat model)

**Threat:** A caller crafts a request with `{"org_id": "globex", "role": "owner"}` in
the body, gaining access to a different tenant's restricted data.

**Mitigation — isolation by construction:**
The `QueryRequest`, `UploadRequest`, and `CreateUserRequest` pydantic models have **no
`org_id` or `role` fields**.  There is no request representation for these values at
all.  FastAPI will 422-reject (extra fields ignored) any attempt to inject them.
`get_current_identity()` is the mandatory dependency on every data endpoint; it is the
only code path that produces an `Identity`.  An endpoint that forgets this dependency
is immediately visible in review as a policy violation.

**The cross-tenant proof:**
An `acme` token user calling `/query` receives `org_id="acme"` in the response because
that is what the token contains.  There is no path through the code where `org_id` can
be `"globex"` for an `acme` token — it would require forging the JWT signature.

---

### 5. Owner-only user provisioning

**Chosen:** Only `role=owner` may call `POST /admin/users`.

**Rationale:** User provisioning is a privileged operation.  Allowing HR or employees
to create accounts would permit privilege escalation (an employee creates a second
account with `role=finance`).  The new user's `org_id` is forced to the owner's
`org_id` from the JWT — the request body has no `org_id` field, so cross-tenant
account creation is structurally impossible.

---

### 6. Startup assertion on JWT_SECRET

**Chosen:** `_assert_strong_jwt_secret()` called at app startup; raises `RuntimeError`
if the secret is the placeholder or shorter than 32 bytes.

**Rationale:** A default or weak HS256 secret makes all token signatures forgeable.
A startup crash is the only safe behaviour — a warning would be silently ignored in
production deployments.  Generate a strong secret with:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Consequences

- **Positive:** `org_id` and `role` are unforgeable; tenant isolation is structural
  rather than just a policy check.  The Phase 2 RBAC filter now receives proven identity.
- **Positive:** Single `get_current_identity()` dependency gives a clear audit trail
  for every auth decision.
- **Positive:** Adversarial tests #2 (token tampering) and #3 (cross-tenant) prove the
  invariant with automated assertions that block any future regression.
- **Trade-off:** No instant token revocation without a session store (deferred).
- **Trade-off:** Short-lived tokens require re-authentication; mitigated by refresh
  tokens in the UI slice.

---

## Security audit trail

Every call to `get_current_identity()` emits a `structlog` event:
- Success: `identity.verified` with `user_id`, `org_id`, `role`
- Failure: `identity.missing_token`, `identity.expired_token`, `identity.invalid_token`
  (with `reason`), `identity.unknown_role`

Failed login attempts: `auth.login_failed` with `email`.
Non-owner `/admin/users` attempts: `admin.create_user_forbidden` with `user_id` and
`role`.

These events form the security audit log.  In Phase 5, they wire into the
Prometheus/Grafana observability stack.
