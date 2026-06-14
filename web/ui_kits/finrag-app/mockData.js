/* ============================================================
   FinRAG — fixtures (prototype fallback data)
   Mirrors the shape returned by the FastAPI backend so screens
   render identically whether data is live or mocked.
   ============================================================ */
window.FINRAG_FIXTURES = {
  // Demo credential used by the mock login path.
  demoPassword: 'finance2024',

  // Sample questions surfaced on the idle query screen.
  suggestedQuestions: [
    'What was operating margin in FY2024 and how did it change?',
    'Summarize the key liquidity risks disclosed in the latest 10-K.',
    'What were total revenues for fiscal 2024 by segment?',
    'What are executive base salaries for FY2024?', // -> no authorized context for the finance role
  ],

  // Keyed canned responses. Any other question maps to `default`.
  answers: {
    margin: {
      question: 'What was operating margin in FY2024 and how did it change?',
      grounding: 0.94,
      segments: [
        { text: 'Operating margin reached ' },
        { text: '24.1% in fiscal 2024', sourceRef: 1 },
        { text: ', up from ' },
        { text: '21.8% in the prior fiscal year', sourceRef: 2 },
        { text: '. The improvement was driven primarily by ' },
        { text: 'operating leverage on higher revenue and disciplined operating expense growth', sourceRef: 1 },
        { text: '. Gross margin also expanded ' },
        { text: '60 basis points to 71.4%', sourceRef: 3 },
        { text: '.' },
      ],
      sources: [
        { ref: 1, docName: 'FY2024_10-K.pdf', page: 42, score: 0.94, access: 'granted',
          excerpt: 'Operating margin was <mark>24.1%</mark> for fiscal 2024, compared with 21.8% in the prior fiscal year, reflecting <mark>operating leverage on higher revenue</mark> and disciplined operating expense growth.' },
        { ref: 2, docName: 'FY2023_10-K.pdf', page: 39, score: 0.89, access: 'granted',
          excerpt: 'Operating margin of <mark>21.8%</mark> in fiscal 2023 reflected continued investment in research and development and go-to-market capacity.' },
        { ref: 3, docName: 'FY2024_10-K.pdf', page: 41, score: 0.86, access: 'granted',
          excerpt: 'Gross margin expanded <mark>60 basis points to 71.4%</mark>, driven by infrastructure efficiency and favorable revenue mix.' },
      ],
    },

    revenue: {
      question: 'What were total revenues for fiscal 2024 by segment?',
      grounding: 0.91,
      segments: [
        { text: 'Total revenue for fiscal 2024 was ' },
        { text: '$8.42 billion', sourceRef: 1 },
        { text: ', an increase of ' },
        { text: '14% year over year', sourceRef: 1 },
        { text: '. By segment, Platform contributed ' },
        { text: '$5.91 billion and Services $2.51 billion', sourceRef: 2 },
        { text: '.' },
      ],
      sources: [
        { ref: 1, docName: 'FY2024_10-K.pdf', page: 56, score: 0.93, access: 'granted',
          excerpt: 'Total revenue was <mark>$8,421 million</mark> for fiscal 2024, an increase of <mark>14%</mark> compared with the prior year.' },
        { ref: 2, docName: 'FY2024_10-K.pdf', page: 57, score: 0.9, access: 'granted',
          excerpt: 'Platform revenue was <mark>$5,908 million</mark> and Services revenue was <mark>$2,513 million</mark> for fiscal 2024.' },
      ],
    },

    // Authorized ONLY for owner + finance. hr / employee get `noContext`
    // for the same question — the restricted chunks never enter their context.
    compensation: {
      question: 'What are executive base salaries for FY2024?',
      grounding: 0.96,
      segments: [
        { text: 'For fiscal 2024, the CEO base salary was ' },
        { text: '$1.20 million', sourceRef: 1 },
        { text: ', and the named executive officers received base salaries totaling ' },
        { text: '$4.85 million', sourceRef: 1 },
        { text: '. Annual cash incentives are tied to ' },
        { text: 'operating margin and revenue growth targets', sourceRef: 2 },
        { text: '.' },
      ],
      sources: [
        { ref: 1, docName: 'FY2024_Proxy_Statement.pdf', page: 34, score: 0.95, access: 'restricted',
          excerpt: "The Chief Executive Officer's base salary was <mark>$1,200,000</mark> for fiscal 2024; aggregate base salary for named executive officers was <mark>$4,850,000</mark>." },
        { ref: 2, docName: 'FY2024_Proxy_Statement.pdf', page: 36, score: 0.9, access: 'restricted',
          excerpt: 'Annual incentive awards are determined by performance against <mark>operating margin and revenue growth</mark> targets approved by the committee.' },
      ],
    },
  },

  // Returned when a question only matches sources the role can't access.
  noContext: { noContext: true },

  // ---- Document library (dashboard) -----------------------------
  documents: [
    { id: 'DOC-10K-2024-0481', name: 'FY2024_10-K.pdf', kind: '10-K', fiscalYear: 'FY2024',
      status: 'indexed', pages: 184, chunks: 482, sizeMb: 4.8, uploaded: '2026-05-28', owner: 'Dana Whitfield' },
    { id: 'DOC-10K-2023-0377', name: 'FY2023_10-K.pdf', kind: '10-K', fiscalYear: 'FY2023',
      status: 'indexed', pages: 176, chunks: 451, sizeMb: 4.5, uploaded: '2026-05-28', owner: 'Dana Whitfield' },
    { id: 'DOC-AR-2024-0512', name: 'FY2024_Annual_Report.pdf', kind: 'Annual report', fiscalYear: 'FY2024',
      status: 'indexed', pages: 96, chunks: 268, sizeMb: 12.1, uploaded: '2026-06-02', owner: 'Marcus Cole' },
    { id: 'DOC-10Q-2025Q1-0588', name: 'FY2025_Q1_10-Q.pdf', kind: '10-Q', fiscalYear: 'FY2025',
      status: 'processing', progress: 0.62, pages: 58, chunks: 112, sizeMb: 2.2, uploaded: '2026-06-13', owner: 'Priya Nair' },
    { id: 'DOC-PROXY-2024-0490', name: 'FY2024_Proxy_Statement.pdf', kind: 'Proxy', fiscalYear: 'FY2024',
      status: 'indexed', pages: 72, chunks: 198, sizeMb: 3.4, uploaded: '2026-06-01', owner: 'Dana Whitfield' },
    { id: 'DOC-MDA-2024-0466', name: 'FY2024_MD&A_Supplement.pdf', kind: 'Supplement', fiscalYear: 'FY2024',
      status: 'failed', pages: 14, chunks: 0, sizeMb: 0.9, uploaded: '2026-06-10', owner: 'Marcus Cole',
      error: '3 pages were unreadable (scanned images). Re-upload a text-based PDF.' },
  ],

  documentStats: { total: 6, indexed: 4, chunks: 1511, processing: 1 },

  // ---- Workspace members (owner admin) --------------------------
  members: [
    { id: 'u1', name: 'Dana Whitfield', email: 'dana@acme.com', role: 'owner', lastActive: '2026-06-14' },
    { id: 'u2', name: 'Marcus Cole', email: 'marcus@acme.com', role: 'finance', lastActive: '2026-06-13' },
    { id: 'u3', name: 'Priya Nair', email: 'priya@acme.com', role: 'hr', lastActive: '2026-06-14' },
    { id: 'u4', name: 'Sam Okafor', email: 'sam@acme.com', role: 'employee', lastActive: '2026-06-11' },
    { id: 'u5', name: 'Lena Brandt', email: 'lena@acme.com', role: 'employee', lastActive: '2026-06-09' },
  ],

  // ---- Access policy (owner admin) ------------------------------
  // The four roles in the system, ordered most → least privileged.
  roles: ['owner', 'finance', 'hr', 'employee'],

  // Sensitivity tier -> roles permitted to retrieve. Mirrors the
  // backend exactly: public & internal are open to all four roles;
  // restricted is owner + finance ONLY (hr and employee cannot see it).
  // This is POLICY configuration — it states who is permitted, never
  // the withheld content itself.
  sensitivityAccess: {
    public:     ['owner', 'finance', 'hr', 'employee'],
    internal:   ['owner', 'finance', 'hr', 'employee'],
    restricted: ['owner', 'finance'],
  },
  sensitivityTiers: ['public', 'internal', 'restricted'],

  sections: [
    { id: 's1', label: 'Financial statements', detail: 'Income statement, balance sheet, cash flows', sensitivity: 'public' },
    { id: 's2', label: 'MD&A & risk factors', detail: 'Management discussion, liquidity & risk disclosures', sensitivity: 'public' },
    { id: 's3', label: 'Segment detail', detail: 'Revenue & margin by operating segment', sensitivity: 'internal' },
    { id: 's4', label: 'Notes & contingencies', detail: 'Legal contingencies, commitments, tax positions', sensitivity: 'internal' },
    { id: 's5', label: 'Executive compensation', detail: 'Salary tables, bonus & equity awards', sensitivity: 'restricted' },
    { id: 's6', label: 'Comp committee materials', detail: 'Board compensation committee deliberations', sensitivity: 'restricted' },
  ],
};
