# FinRAG Design System

> **FinRAG — "Grounded financial intelligence."**
> A production-grade, multi-tenant financial-document RAG platform. Finance teams
> upload their filings (10-Ks, annual reports, board decks) and ask natural-language
> questions, getting **cited, grounded answers**. Chunk-level role-based access keeps
> sensitive sections (e.g. salary tables) invisible to unauthorized roles.

This repository is the design system that lets agents and developers build on-brand
FinRAG interfaces and assets. It contains the visual foundations (tokens, type, color),
reusable React components, and a full UI-kit recreation of the product.

---

## Sources

This system was authored from a written product brief — **no external codebase, Figma
file, or brand kit was provided**. All visual decisions (palette, type, logo, motion)
are original and should be treated as the canonical FinRAG brand until real brand
assets exist. If/when a codebase or Figma is shared, reconcile against it and update
this file with the links.

> ⚠️ **Font substitution flag:** the brand uses the **IBM Plex** family (Sans / Mono /
> Serif), currently loaded from the Google Fonts CDN (`tokens/fonts.css`). For
> production or offline use, self-host the woff2 binaries and replace the `@import`
> with local `@font-face` rules. If IBM Plex is later replaced by a licensed face,
> swap it there.

---

## The product in one screen

FinRAG's hero is the **cited-answer view**: a generated answer whose every factual
claim is visibly tied to the source chunk that backs it. The design system treats this
"which source backed which claim" relationship as the single most important thing to
get right — hence a dedicated **grounding color** and a dedicated **citation component
group** (`Citation`, `SourceCard`, `AccessBadge`, `ConfidenceMeter`).

### Two product invariants (non-negotiable)

These two rules define the product's trust model and are enforced in the components
and screens — do not design around them:

1. **Grounded-only.** Every claim shown maps to a cited source. There is no
   model-only / "ungrounded" path — if something can't be cited, it isn't said. The
   promise is *"if it's not cited, we don't say it."* (No amber "unverified" chip.)
2. **Unauthorized chunks are invisible.** Restricted content for a given role never
   enters the answer context, and so never appears in the UI — **not even as a redacted
   placeholder**. A placeholder would itself reveal that restricted content exists,
   which is a leak. When nothing authorized answers a question, show the graceful
   *"no authorized sources"* state — never imply withheld content.

---

## Content fundamentals

How FinRAG writes. The voice is that of a **calm, precise financial professional** —
trustworthy, exact, never breezy. It earns confidence by being specific and by never
overclaiming.

- **Person & address.** Speak to the user as **"you"** ("Sign in to your workspace",
  "Sections outside your permissions are not used to answer"). The product refers to
  itself in the third person or not at all — never "I".
- **Casing.** **Sentence case** everywhere — buttons, headings, menu items
  ("Upload document", not "Upload Document"). The only uppercase is the
  **eyebrow / micro-label** treatment (letter-spaced, 11px): `QUESTION`, `SOURCES`,
  `GROUNDING`. Product name is always **FinRAG** (one word, capital F and RAG).
- **Tone.** Confident and plain. Short declarative sentences. Lead with the number or
  the fact. Avoid hype words ("powerful", "seamless", "revolutionary") and avoid hedging
  filler. Good: *"Every answer is grounded in cited sources."* Not: *"Get amazing
  AI-powered insights instantly!"*
- **Numbers & data.** Always concrete and formatted: `24.1%`, `$8.42 billion`,
  `482 chunks`, `p.42`. Render figures in the **mono** face with tabular figures.
- **Trust & compliance language.** Security and access are stated factually, never
  alarmingly: *"Protected workspace. Activity is logged for compliance."*,
  *"Sources reflect your access role."*
- **Access / restriction copy — handle with care.** When a role can't see something,
  never imply *what* is hidden or that sensitive content relevant to the query exists.
  Use neutral, role-framed language: *"No authorized sources answer this question"*,
  *"Sources reflect your access role."* Never name or hint at the restricted content
  (never: *"You don't have access to the salary data"*), and never show a "content
  withheld" placeholder — for an unauthorized role the content simply isn't there.
- **Errors.** Specific, blameless, actionable: *"Invalid email or password. Please try
  again."*, *"3 pages were unreadable (scanned images)."*
- **Grounding honesty.** Every shown claim is grounded in a cited source; uncited model
  inferences are suppressed entirely rather than marked. The UI never presents an
  unsourced statement as an answer.
- **Emoji:** never. Iconography is line-based SVG (see Iconography).

---

## Visual foundations

**Overall vibe:** a light, dense, legible enterprise application — institutional and
calm, closer to a Bloomberg terminal's seriousness than a consumer SaaS landing page.
Confidence through restraint: lots of hairline structure, generous tabular data, one
decisive accent.

### Color
- **Cool slate neutrals** form the base — a near-black navy-slate ink (`--slate-950`
  for dark chrome, `--slate-900` for text) down through a 12-step ramp to near-white
  surfaces. Page background is `--slate-100`; cards are pure white.
- **One brand accent: cobalt/azure blue** (`--accent`, `#2257D6`-ish). Used for primary
  actions, links, focus rings, selection, and brand chrome — and nothing else.
- **One semantic "verified" green** (`--verified`) is **reserved exclusively for the
  grounding system** — citations, source highlights, confidence, "authorized" badges.
  Seeing green anywhere in FinRAG means "this is grounded / you can trust this." Do not
  use green for generic success chrome outside that meaning.
- Semantic **amber** (warning / attention) and **red** (danger / failure) round out the
  set. All ramps are defined in `oklch` for perceptual harmony; prefer the **semantic
  aliases** (`--text-primary`, `--surface-card`, `--border-subtle`, `--accent`,
  `--verified`, `--locked`, …) over raw ramp steps in product code.
- **Imagery vibe:** cool, restrained, mostly UI — no photography in the core product.
  The one dark surface (login brand panel) uses a subtle cool radial wash, not a
  saturated gradient.

### Type
- **IBM Plex Sans** — all UI and body text and headings (`--font-sans`).
- **IBM Plex Mono** — all figures, document ids, page refs, citation numbers,
  percentages, metadata (`--font-mono`, tabular + lining numerals on by default).
- **IBM Plex Serif** — *quoted document excerpts only* (`--font-serif`). Source snippets
  render in serif so they read as lifted "from the document," distinct from product UI.
- Dense scale (11 → 52px); UI body is **14px**. Headings are semibold (600), snug
  letter-spacing, tight leading. Eyebrows are 11px uppercase, `0.06em` tracking.

### Spacing & layout
- **4px base grid** (`--space-*`). Dense enterprise rhythm.
- Fixed layout dims as tokens: 52px topbar, 248px sidebar, 420px source panel,
  760px readable answer column, 1320px container max.
- Layout leans on **CSS grid/flex with `gap`**, hairline `1px` dividers, and sticky
  headers — structure is expressed with borders, not heavy shadows.

### Elevation, borders, radii
- **Tight radii:** 3px (chips) → 5px (inputs) → 7px (buttons/cards) → 10px (panels) →
  14px (modals); pill for avatars/dots.
- **Hairline borders** (`--border-subtle` / `--border-default`) do most of the
  separation work. Cards = white surface + 1px subtle border + `--shadow-xs`.
- **Shadows** are cool, low-spread, and soft (`--shadow-xs … xl`), used sparingly —
  for raised menus, dialogs, toasts, hover lift. No glow, no colored shadows.

### Motion & states
- **Easing:** `--ease-out` (cubic-bezier(.16,1,.3,1)) for most enter/settle;
  `--ease-spring` only for tiny affordances (checkbox tick). Durations 120 / 180 / 280ms.
- **Hover:** surfaces shift one step darker (`--surface-hover`), borders strengthen,
  ghost buttons gain a tint. **Press:** a 0.5px nudge down + one more shade.
- **Focus:** always a 3px cobalt ring (`--ring-shadow`) + accent border. Never removed.
- Animations are functional (spinners, indeterminate bars, skeleton shimmer,
  citation/highlight activation) — **no decorative or looping motion** on content.
- Respects `prefers-reduced-motion`.

### Signature motifs
- **Citation chips** — small mono `[n]` pills with a leading dot, green (grounded);
  vertically raised like a footnote marker. Every chip maps to a real source.
- **Grounded-text highlight** — a low underline-style green wash (`linear-gradient`)
  behind any clause backed by a source; intensifies when its citation is active.
- **SourceCard** — white card with a **3px green left rule**, mono ref tag, serif
  excerpt with `<mark>` highlights, and an "Authorized" access badge. Only authorized
  chunks are ever rendered — there is no locked/redacted variant.
- **Access policy (owner admin)** — the `restricted` / `confidential` `AccessBadge`
  levels express *policy* (which roles a section is scoped to) in the access-control
  screen. They mark configuration, never withheld answer content.

---

## Iconography

- **System:** line icons on a 24px grid, **~1.9px stroke**, round caps & joins —
  visually consistent with **Lucide**. Icons are authored as inline SVG (see
  `ui_kits/finrag-app/Icons.jsx` for the product set; components inline their own small
  glyphs). This keeps stroke weight and corner treatment uniform across the brand.
- **Substitution flag:** there is no bespoke FinRAG icon font. The inline set is
  hand-matched to the **Lucide** style; if you need a glyph that isn't in
  `Icons.jsx`, pull it from **Lucide** (`https://lucide.dev`, same 24/1.9px grid) to
  stay consistent, and add it to `Icons.jsx`.
- **Emoji:** never used as iconography or decoration.
- **Unicode:** used only for tiny inline arrows in data deltas (`▴`/`▾`). Everything
  else is SVG.
- **Logo / brand mark:** in `assets/` — `logo-mark.svg` (the tile), `logo-wordmark.svg`
  (light bg), `logo-wordmark-inverse.svg` (dark bg). The mark depicts a claim line and a
  shorter source line bound by a citation node — the product's core idea. Cobalt tile;
  "Fin" in ink, "RAG" in cobalt.

---

## Index / manifest

**Root**
- `styles.css` — the single entry point consumers link. `@import`s only.
- `readme.md` — this guide.
- `SKILL.md` — Agent-Skill front matter for using this system in Claude Code.

**`tokens/`** (all `@import`ed by `styles.css`)
- `fonts.css` — IBM Plex `@import` (Sans / Mono / Serif).
- `colors.css` — neutral/accent/verified/semantic ramps + semantic aliases.
- `typography.css` — families, scale, weights, leading, tracking, numeric features.
- `spacing.css` — 4px spacing scale, layout dims, z-index.
- `elevation.css` — radii, border widths, shadows, motion (easing/durations).
- `base.css` — element resets and defaults (`.eyebrow`, `.excerpt`, `.num`, scrollbars).

**`components/`** — reusable React primitives (`<Name>.jsx` + `.d.ts`, grouped CSS in
`components/_css/`, one `@dsCard` HTML per group).
- `core/` — **Button, IconButton, Badge, Avatar, Spinner**
- `forms/` — **Field, Input, Textarea, Select, Checkbox, Switch**
- `feedback/` — **Banner, Tooltip, EmptyState, Toast**
- `data/` — **Card, Tabs, StatTile, ProgressBar**
- `citation/` — **Citation, SourceCard, AccessBadge, ConfidenceMeter** *(the hero group)*

**`ui_kits/finrag-app/`** — high-fidelity product recreation (click-through).
- `index.html` — app shell: Login → (Ask · Documents · Access control), role-gated.
- `config.js` — configurable `apiBaseUrl` + endpoints (point at your FastAPI backend).
- `api.js` — API client with graceful fixture fallback.
- `mockData.js` — prototype fixtures (mirror the backend response shape).
- `Icons.jsx` — shared Lucide-style icon set.
- `AppHeader.jsx` — top bar with workspace + "Signed in as <role>" indicator.
- `NavSidebar.jsx` — left rail; the **Access control** group is owner-only.
- `LoginScreen.jsx` — split brand-panel sign-in with error state.
- `QueryScreen.jsx` — **the hero**: grounded cited-answer view (idle · generating ·
  answer-with-citations · no-authorized-context).
- `DocumentsScreen.jsx` — document library: status, metadata, search, filter, empty.
- `AdminScreen.jsx` — **owner-only** access control: members + section→role policy matrix.

**`assets/`** — `logo-mark.svg`, `logo-wordmark.svg`, `logo-wordmark-inverse.svg`.

**Usage in a card / app:** link `styles.css`, load `_ds_bundle.js` (generated), then
`const { Button, Citation, SourceCard } = window.FinRAGDesignSystem_2f3924;`

---

## Roadmap (in progress)

- [x] Tokens, fonts, base, logo
- [x] Core / forms / feedback / data / citation components + cards
- [x] FinRAG app UI kit — **Login** + **Cited-answer query** (hero) screens
- [x] UI kit — **document dashboard** + **owner-only access control**
- [ ] Foundation specimen cards (Type / Colors / Spacing / Brand) for the Design System tab
- [ ] Self-hosted fonts to replace the CDN `@import`
