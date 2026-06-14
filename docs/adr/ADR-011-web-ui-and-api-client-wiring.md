# ADR-011 — Web UI integration and API client wiring

**Status:** Accepted
**Date:** 2026-06-14

## Context

The FinRAG backend (Phases 0–4) has a working FastAPI chain-server with JWT auth and chunk-level RBAC. The backend exposes four endpoints:

```
POST /auth/login          {email, password} → {access_token, token_type}
POST /query               {question}        → {answer, org_id, role, sources:[str]}
POST /documents/upload    {doc_name, text}  → {doc_id, doc_name, org_id, chunks_ingested}
POST /admin/users         {email,pass,role} → {user_id, email, org_id, role}  (owner+JWT)
```

A frontend (Login, Query, Documents, Admin screens) was designed in Claude Design and exported to `/FinRAG Design System/`. The exported kit includes:
- `config.js` — configurable `apiBaseUrl` + endpoint map
- `api.js` — API client with graceful mock fallback
- `mockData.js` — fixture data mirroring the expected backend response shape
- Four screen JSX files + shared components bundled in `_ds_bundle.js`

The frontend's assumed response shapes differ from the real backend:

| Flow | Backend (real) | Frontend (assumed) |
|------|---------------|-------------------|
| Login | `{access_token, token_type}` | `{token, role, email}` |
| Query answer | `answer: str` with `[N]` markers | `segments: [{text, sourceRef?}]` |
| Query sources | `sources: [str]` | `sources: [{ref, docName, page, score, excerpt, access}]` |
| Query grounding | *(absent)* | `grounding: float` |

The backend's JWT payload carries `sub`, `org_id`, `role` — no `email` claim.

The `sources: [str]` from the backend currently returns `[]` (Phase 3 stub); when Phase 4 wires `answer_query`, sources will be citation strings like `"doc_name, page N (chunk_id=...)"` from `generation/citations.py`.

## Decision

1. **Copy frontend into `web/`** at repo root so it is versioned alongside the backend.

2. **Keep components as-built.** All four screen JSX files, shared components, and the design system bundle (`_ds_bundle.js`) are unchanged. This preserves the visual and interaction design exactly.

3. **Bridge field-name mismatches in `api.js` only.** A thin normalize layer (`normalizeLoginResponse`, `normalizeQueryResponse`, `parseAnswerSegments`, `normalizeSourcesList`) sits in `api.js`. Components receive the shape they were designed to consume; the normalize functions absorb any backend/frontend schema gap.

4. **Login normalize:** extract `access_token` → `token`; decode JWT payload client-side (no signature verification — display only) to get `role`; echo the submitted `email` back (backend doesn't return it).

5. **Query normalize:** parse `[N]` markers in the flat `answer` string into `{segments, sources}` the UI expects. `grounding` defaults to `null` (the ConfidenceMeter renders gracefully). `sources: [str]` is parsed with a best-effort `"doc_name, page N (chunk_id=...)"` regex, consistent with `generation/citations.py`'s output format.

6. **No-context detection:** the backend's refusal phrase starts with `"I cannot answer"` (from `generation/prompt.py`'s `GROUNDING_SYSTEM_PROMPT`). The normalizer detects this and returns `{noContext: true}` so the UI shows the authorized-context-empty state rather than an empty answer.

7. **Authenticated calls:** `authedPostJSON` sends `Authorization: Bearer <token>` on all calls that need a JWT (`/query`, `/documents/upload`, `/admin/users`). The original `postJSON` is kept for the unauthenticated `/auth/login` call.

8. **Mock fallback preserved:** `allowMockFallback: true` keeps the fixture path active for dev/design review when the backend is unreachable. The mock path for login now mirrors the same `{token, role, email}` shape that the real path produces.

9. **No backend modifications.** `api/`, `retrieval/`, `rbac/`, `generation/` are untouched.

10. **No CI job for web/JS** (no `package.json` or JS toolchain exists yet; per CI hygiene rule 5, we do not add CI jobs that reference non-existent files).

## Two product invariants — enforced in UI

The design system readme defines two non-negotiable invariants. Both are maintained:

1. **Grounded-only:** every claim shown maps to a cited source. The `segments` normalize preserves the `[N]` → `sourceRef` mapping. If the answer has no citations, `segments` contains no `sourceRef` entries and the ConfidenceMeter gets `null` (no false grounding score shown).

2. **Unauthorized chunks are invisible:** the backend enforces RBAC at Milvus retrieval time (ADR-007). The UI enforces the UX side: the `noContext` detection triggers the "No authorized sources answer this question" state — it never shows a placeholder or mentions withheld content.

## Consequences

- `web/ui_kits/finrag-app/api.js` is the single integration seam. Any future backend schema change (e.g. adding `grounding` to `QueryResponse`) can be absorbed here without touching components.
- The frontend does not have a `GET /documents` or `GET /admin/users` endpoint. Documents and admin member lists render from `mockData.js`. These screens should be wired once the backend adds list endpoints.
- The JWT decode in `api.js` is for display only (extracting `role` for role-gated UI). The backend re-validates the JWT on every authenticated request. Client-side payload reads cannot be used to elevate privilege — the backend's `get_current_identity` is the sole authority (ADR-008).
