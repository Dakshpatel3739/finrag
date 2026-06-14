The grounding system — FinRAG's signature. `Citation` chips sit inline in answer text; clicking one activates the matching `SourceCard` in the evidence panel. `AccessBadge` marks chunk-level role policy. `ConfidenceMeter` shows answer groundedness.

```jsx
<p>
  Operating margin reached 24.1% in FY2024<Citation index={1} onClick={() => focus(1)} />,
  up from 21.8% the prior year<Citation index={2} active />.
</p>

<SourceCard refIndex={1} docName="FY2024_10-K.pdf" page={42} score={0.93}
  access="granted" active
  excerpt="Operating margin was <mark>24.1%</mark> for fiscal 2024…" />

<ConfidenceMeter value={0.92} label="Grounding" />
```

Two non-negotiable product invariants this system enforces:

- **Grounded-only.** Every `Citation` maps to a real source. There is no ungrounded / model-only chip — if a claim can't be cited, it is suppressed upstream and never rendered. Don't reintroduce an amber "unverified" variant.
- **Unauthorized chunks are invisible.** Only authorized chunks reach `SourceCard`; there is no `locked` state. Restricted content never appears — not even as a redacted placeholder, which would itself reveal that it exists. When a question has no authorized sources, show the graceful "no authorized context" empty state — never imply withheld content.

`verified` green is reserved for this system — don't use it elsewhere. `AccessBadge` `restricted`/`confidential` levels are for expressing POLICY in the owner admin panel (which roles a section is scoped to), not for marking answer sources.
