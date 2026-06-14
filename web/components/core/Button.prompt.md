Primary action button — use for the main action in any view; pair one `primary` with `secondary`/`ghost` siblings.

```jsx
<Button variant="primary" leftIcon={<PlusIcon/>}>Upload document</Button>
<Button variant="secondary">Cancel</Button>
<Button variant="ghost" size="sm">Skip</Button>
<Button variant="primary" loading>Indexing…</Button>
```

Variants: `primary` (cobalt, one per view), `secondary` (outline), `ghost` (toolbar/low-emphasis), `danger` (destructive), `accent-soft` (tinted secondary). Sizes: `sm` 28px · `md` 34px · `lg` 42px. Set `loading` to show a spinner and block clicks; `block` for full width.
