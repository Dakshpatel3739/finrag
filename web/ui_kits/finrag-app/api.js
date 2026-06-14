/* ============================================================
   FinRAG — API client
   Thin wrapper over the configurable backend. Every call targets
   FINRAG_CONFIG.apiBaseUrl + endpoint; on network failure (or when
   no backend is running) it falls back to bundled fixtures so the
   prototype stays interactive. Swap-in real backend by setting
   window.FINRAG_API_BASE — no call-site changes required.

   BACKEND WIRING (api/app.py, Phase 3 chain-server):
     POST /auth/login          {email, password} → {access_token, token_type}
     POST /query               {question}        → {answer, org_id, role, sources:[str]}
     POST /documents/upload    {doc_name, text}  → {doc_id, doc_name, org_id, chunks_ingested}
     POST /admin/users         {email,password,role} → {user_id, email, org_id, role} (owner+JWT)

   NORMALIZE LAYER:
     The backend response shape differs from the UI's internal shape.
     normalizeLoginResponse and normalizeQueryResponse bridge the gap
     without touching any component files.
   ============================================================ */
(function () {
  const cfg = window.FINRAG_CONFIG;
  const fx = window.FINRAG_FIXTURES;

  function baseUrl() {
    return cfg.apiBaseUrl.replace(/\/$/, '');
  }

  // ---- HTTP helpers -----------------------------------------------

  async function postJSON(path, body) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), cfg.timeoutMs);
    try {
      const res = await fetch(baseUrl() + path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: ctrl.signal,
      });
      clearTimeout(t);
      if (!res.ok) {
        const err = new Error('HTTP ' + res.status);
        err.status = res.status;
        throw err;
      }
      return await res.json();
    } catch (e) {
      clearTimeout(t);
      if (!e.status) e.isNetwork = true;
      throw e;
    }
  }

  // Authenticated POST — sends JWT in Authorization: Bearer header.
  // Required for /query, /documents/upload, /admin/users.
  async function authedPostJSON(path, body, token) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), cfg.timeoutMs);
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    try {
      const res = await fetch(baseUrl() + path, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: ctrl.signal,
      });
      clearTimeout(t);
      if (!res.ok) {
        const err = new Error('HTTP ' + res.status);
        err.status = res.status;
        throw err;
      }
      return await res.json();
    } catch (e) {
      clearTimeout(t);
      if (!e.status) e.isNetwork = true;
      throw e;
    }
  }

  // ---- JWT decode (display only — no signature verification) ------
  // Used to extract role/org_id from the access token so the session
  // object has the shape the app expects: {token, role, email}.
  function decodeJwtPayload(token) {
    try {
      // JWT is header.payload.signature; payload is base64url-encoded JSON.
      const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(b64));
    } catch {
      return {};
    }
  }

  // ---- Normalize: login ------------------------------------------
  // Backend → {access_token, token_type}
  // UI session expects → {token, role, email}
  //   role comes from the JWT payload (claim "role")
  //   email is the address the user typed — the backend does not echo it
  function normalizeLoginResponse(backendRes, email) {
    const payload = decodeJwtPayload(backendRes.access_token || '');
    return {
      token: backendRes.access_token,
      role: payload.role || 'employee',
      email: email,
    };
  }

  // ---- Normalize: query ------------------------------------------
  // Backend → {answer: str, org_id, role, sources: [str]}
  // UI expects → {question, grounding, segments: [{text, sourceRef?}], sources: [{ref, docName, page, score, excerpt, access}]}
  //
  // sources: The backend currently emits [] (Phase 3 stub). When Phase 4
  // wires answer_query, sources will be strings like "doc_name, page N
  // (chunk_id=...)". The normalizer handles both cases gracefully.
  function normalizeQueryResponse(backendRes, question) {
    const answer = backendRes.answer || '';

    // "I cannot answer" is the backend refusal phrase from generation/prompt.py.
    // Treat it as no-authorized-context so the UI shows the NoContext state.
    if (!answer || /^i cannot answer/i.test(answer.trim())) {
      return { noContext: true };
    }

    return {
      question,
      // Backend does not yet expose a grounding score; components render
      // ConfidenceMeter with null gracefully (it defaults to 0 / hidden).
      grounding: null,
      segments: parseAnswerSegments(answer),
      sources: normalizeSourcesList(backendRes.sources || []),
    };
  }

  // Parse "[N]" citation markers from the backend answer string into the
  // segment array format the UI renders.
  //
  // Input:  "Revenue was $26.97B [1]. Margin was 24.1% [2]."
  // Output: [{text:"Revenue was $26.97B", sourceRef:1},
  //          {text:". Margin was 24.1%",  sourceRef:2},
  //          {text:"."}]
  function parseAnswerSegments(answer) {
    const parts = answer.split(/(\[\d+\])/);
    const segments = [];
    let pending = '';
    for (const part of parts) {
      const m = part.match(/^\[(\d+)\]$/);
      if (m) {
        segments.push({ text: pending, sourceRef: parseInt(m[1], 10) });
        pending = '';
      } else {
        pending += part;
      }
    }
    if (pending) segments.push({ text: pending });
    return segments.filter((s) => s.text !== '' || s.sourceRef != null);
  }

  // Map backend sources (list of strings, currently []) to the source
  // object shape the SourceCard component expects.
  //
  // When Phase 4 wires answer_query the backend will emit citation strings
  // like "filename.pdf, page 42 (chunk_id=abc123)". We parse that format;
  // unknown strings fall back to displaying the raw string as the doc name.
  function normalizeSourcesList(sources) {
    return sources.map((s, i) => {
      const raw = typeof s === 'string' ? s : String(s);
      // Try to parse "doc_name, page N (chunk_id=...)"
      const m = raw.match(/^(.+?),\s*page\s*(\d+)/i);
      return {
        ref: i + 1,
        docName: m ? m[1].trim() : raw,
        page: m ? parseInt(m[2], 10) : null,
        score: null,
        excerpt: null,
        access: 'granted',
      };
    });
  }

  // ---- Auth -------------------------------------------------------

  async function login(email, password) {
    try {
      const backendRes = await postJSON(cfg.endpoints.login, { email, password });
      return normalizeLoginResponse(backendRes, email);
    } catch (e) {
      if (e.status === 401) throw new Error('INVALID_CREDENTIALS');
      if (e.isNetwork && cfg.allowMockFallback) return mockLogin(email, password);
      throw e;
    }
  }

  function roleFromEmail(email) {
    const local = (email.split('@')[0] || '').toLowerCase();
    if (/owner|admin/.test(local)) return 'owner';
    if (/finance|cfo/.test(local)) return 'finance';
    if (/^hr|people/.test(local)) return 'hr';
    if (/employee|staff/.test(local)) return 'employee';
    return 'finance'; // default demo role
  }

  function mockLogin(email, password) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const ok = /\S+@\S+\.\S+/.test(email) && password === fx.demoPassword;
        if (!ok) return reject(new Error('INVALID_CREDENTIALS'));
        const role = roleFromEmail(email);
        resolve({ token: 'demo.' + btoa(email), role, email });
      }, 650);
    });
  }

  // ---- Query ------------------------------------------------------

  async function query(question, { token, role } = {}) {
    try {
      const backendRes = await authedPostJSON(cfg.endpoints.query, { question }, token);
      return normalizeQueryResponse(backendRes, question);
    } catch (e) {
      if (e.isNetwork && cfg.allowMockFallback) return mockQuery(question, role);
      // 401 means token expired — propagate so the caller can sign out.
      throw e;
    }
  }

  function mockQuery(question, role) {
    return new Promise((resolve) => {
      const q = (question || '').toLowerCase();
      const canSeeRestricted = role === 'owner' || role === 'finance';
      let payload;
      if (/salary|salaries|compensation|comp\b|executive pay|bonus/.test(q)) {
        payload = canSeeRestricted ? fx.answers.compensation : fx.noContext;
      } else if (/revenue|segment|sales|top line/.test(q)) {
        payload = fx.answers.revenue;
      } else {
        payload = fx.answers.margin;
      }
      setTimeout(() => resolve(payload), 1400);
    });
  }

  // ---- Upload -----------------------------------------------------

  async function uploadDocument(docName, text, token) {
    return authedPostJSON(cfg.endpoints.upload, { doc_name: docName, text }, token);
  }

  // ---- Admin ------------------------------------------------------

  // Create a new user in the calling owner's org.
  // request: {email, password, role}
  // response: {user_id, email, org_id, role}
  async function adminCreateUser(email, password, role, token) {
    return authedPostJSON(cfg.endpoints.adminCreateUser, { email, password, role }, token);
  }

  window.FinRAGAPI = { login, query, uploadDocument, adminCreateUser };
})();
