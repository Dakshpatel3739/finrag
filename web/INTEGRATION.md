# FinRAG Web UI — Integration Guide

Static frontend for the FinRAG chain-server. Built with React 18 (UMD/CDN, no build step), the FinRAG Design System components, and a thin API client that talks to the FastAPI backend.

See `readme.md` for the full Design System guide (tokens, components, brand, etc.).

## Quick start

Serve `ui_kits/finrag-app/index.html` from any static file server (run from `web/`):

```bash
# Python
python -m http.server 3000 --directory ui_kits/finrag-app

# Node (npx)
npx serve ui_kits/finrag-app -l 3000
```

Then open `http://localhost:3000`. No `npm install` or build step needed — React + Babel load from CDN (pinned in `index.html`).

## Pointing at the real backend

The API client defaults to `http://localhost:8000`. Override by injecting the global before `config.js` loads — add a `<script>` at the top of `index.html`:

```html
<script>window.FINRAG_API_BASE = "http://your-server:8000";</script>
```

## Running the chain-server

```bash
cd ..   # repo root (finrag/)
pip install -e ".[dev]"
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
export DEPLOY_MODE=hosted
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

## Backend endpoints consumed

| Screen | Method | Endpoint | Auth |
|--------|--------|----------|------|
| Login | POST | `/auth/login` | — |
| Query | POST | `/query` | Bearer JWT |
| Upload | POST | `/documents/upload` | Bearer JWT |
| Admin — invite member | POST | `/admin/users` | Bearer JWT (owner only) |

The **Documents list** and **Admin members list** have no backend endpoints yet — those screens fall back to `mockData.js` fixtures automatically (`allowMockFallback: true`).

## Normalize layer

`ui_kits/finrag-app/api.js` bridges field-name mismatches without touching any component:

| Flow | Backend field | UI field | Bridge |
|------|--------------|----------|--------|
| Login | `access_token` | `token` | rename |
| Login | *(absent)* | `role` | decode JWT payload client-side (display only) |
| Login | *(absent)* | `email` | pass through form input |
| Query | `answer: str` | `segments: [{text, sourceRef?}]` | parse `[N]` markers |
| Query | `sources: [str]` | `sources: [{ref, docName, page, ...}]` | normalize strings |
| Query | *(absent)* | `grounding` | default to `null` |

## Mock fallback

`FINRAG_CONFIG.allowMockFallback = true` (default). When the backend is unreachable the app renders with fixture data from `mockData.js`. Set to `false` to require a live API.

## IBM Plex fonts — CDN dependency

Fonts load from Google Fonts CDN (`tokens/fonts.css`). The app requires an internet connection to display the IBM Plex typeface. For offline/production use, self-host the woff2 binaries and replace the `@import` in `tokens/fonts.css` with local `@font-face` rules (see `readme.md`).

## CI note

`web/` is not part of the Python CI job (`ruff + mypy + pytest`). To add a JS lint or build step, add it to `.github/workflows/ci.yml` when the tooling and `package.json` exist — do not add it speculatively (CI hygiene rule 5 in `CLAUDE.md`).
