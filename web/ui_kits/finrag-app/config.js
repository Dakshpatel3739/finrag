/* ============================================================
   FinRAG — runtime config
   The API base URL is configurable (env / injected global), never
   hardcoded at call sites. A real FastAPI backend can be pointed
   to by setting window.FINRAG_API_BASE before this script loads,
   e.g. <script>window.FINRAG_API_BASE="https://api.acme.com"</script>
   ============================================================ */
window.FINRAG_CONFIG = {
  // Base URL of the FinRAG FastAPI backend.
  apiBaseUrl: (typeof window !== 'undefined' && window.FINRAG_API_BASE) || 'http://localhost:8000',

  // Endpoint paths (relative to apiBaseUrl) — must match api/app.py exactly.
  endpoints: {
    login:           '/auth/login',
    query:           '/query',
    upload:          '/documents/upload',
    adminCreateUser: '/admin/users',
  },

  // When the backend is unreachable, fall back to bundled fixtures so
  // the prototype stays interactive. Set false to require a live API.
  allowMockFallback: true,

  // Request timeout (ms) before falling back / erroring.
  timeoutMs: 8000,
};
