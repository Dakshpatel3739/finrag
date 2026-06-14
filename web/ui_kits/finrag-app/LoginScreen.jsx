/* FinRAG UI kit — Screen 1: Login (split brand panel + form). */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const { Field, Input, Button, Banner } = DS;
  const I = window.Icons;

  function LoginScreen({ onSuccess }) {
    const [email, setEmail] = React.useState('finance@acme.com');
    const [password, setPassword] = React.useState('');
    const [showPw, setShowPw] = React.useState(false);
    const [error, setError] = React.useState('');
    const [loading, setLoading] = React.useState(false);

    async function submit(e) {
      e.preventDefault();
      setError('');
      setLoading(true);
      try {
        const res = await window.FinRAGAPI.login(email.trim(), password);
        onSuccess(res);
      } catch (err) {
        setError(err.message === 'INVALID_CREDENTIALS'
          ? 'Invalid email or password. Please try again.'
          : 'Unable to sign in right now. Check your connection and retry.');
        setLoading(false);
      }
    }

    return (
      <div style={lg.page}>
        {/* Brand panel */}
        <aside style={lg.brand}>
          <img src="../../assets/logo-wordmark-inverse.svg" alt="FinRAG" height="26" />
          <div style={lg.brandBody}>
            <h1 style={lg.brandHead}>Answers your finance team can stand behind.</h1>
            <p style={lg.brandSub}>
              Ask questions across your filings and reports. Every answer is grounded
              in cited sources — with chunk-level access controls on sensitive sections.
            </p>
            <ul style={lg.points}>
              {[
                ['ShieldCheck', 'Cited, grounded answers — no unsourced claims'],
                ['Lock', 'Role-based access down to the document chunk'],
                ['Layers', 'Built for 10-Ks, annual reports & filings'],
              ].map(([icon, text]) => {
                const Ico = I[icon];
                return (
                  <li key={text} style={lg.point}>
                    <span style={lg.pointIcon}><Ico /></span>{text}
                  </li>
                );
              })}
            </ul>
          </div>
          <div style={lg.brandFoot}>SOC 2 Type II · Data encrypted in transit & at rest</div>
        </aside>

        {/* Form panel */}
        <main style={lg.formWrap}>
          <form style={lg.form} onSubmit={submit} noValidate>
            <div style={lg.formHead}>
              <h2 style={lg.title}>Sign in</h2>
              <p style={lg.subtitle}>Welcome back. Sign in to your workspace.</p>
            </div>

            {error && <Banner variant="danger" title="Sign-in failed">{error}</Banner>}

            <Field label="Work email" htmlFor="email">
              <Input id="email" type="email" autoComplete="username" icon={<I.Mail />}
                     value={email} invalid={!!error}
                     onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" />
            </Field>

            <Field label="Password" htmlFor="password">
              <div style={{ position: 'relative' }}>
                <Input id="password" type={showPw ? 'text' : 'password'} autoComplete="current-password"
                       value={password} invalid={!!error}
                       onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" />
                <button type="button" aria-label="Toggle password visibility"
                        onClick={() => setShowPw((v) => !v)} style={lg.eye}><I.Eye /></button>
              </div>
            </Field>

            <div style={lg.formRow}>
              <label style={lg.remember}>
                <input type="checkbox" style={{ accentColor: 'var(--accent)' }} defaultChecked /> Remember this device
              </label>
              <a href="#" style={lg.link} onClick={(e) => e.preventDefault()}>Forgot password?</a>
            </div>

            <Button type="submit" variant="primary" size="lg" block loading={loading}>
              {loading ? 'Signing in' : 'Sign in'}
            </Button>

            <p style={lg.demoHint}>
              Demo · password <code style={lg.code}>finance2024</code> · sign in as
              <code style={lg.code}>owner@</code>, <code style={lg.code}>finance@</code>,
              <code style={lg.code}>hr@</code> or <code style={lg.code}>employee@</code> to explore each role.
            </p>
          </form>
          <p style={lg.legal}>Protected workspace. Activity is logged for compliance.</p>
        </main>
      </div>
    );
  }

  const lg = {
    page: { minHeight: '100vh', display: 'grid', gridTemplateColumns: '1.05fr 1fr', background: 'var(--surface-card)' },
    brand: {
      background: 'var(--slate-950)', color: 'var(--slate-50)', padding: '40px 48px',
      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
      backgroundImage: 'radial-gradient(120% 90% at 0% 0%, oklch(0.30 0.05 262) 0%, transparent 55%)',
    },
    brandBody: { maxWidth: 420 },
    brandHead: { color: '#fff', fontSize: 'var(--text-3xl)', lineHeight: 1.18, letterSpacing: 'var(--tracking-tight)', marginBottom: 16, fontWeight: 600 },
    brandSub: { color: 'var(--slate-400)', fontSize: 'var(--text-md)', lineHeight: 1.6 },
    points: { listStyle: 'none', padding: 0, margin: '28px 0 0', display: 'flex', flexDirection: 'column', gap: 14 },
    point: { display: 'flex', alignItems: 'center', gap: 12, fontSize: 'var(--text-sm)', color: 'var(--slate-200)' },
    pointIcon: {
      width: 30, height: 30, flex: 'none', borderRadius: 'var(--radius-sm)', display: 'inline-flex',
      alignItems: 'center', justifyContent: 'center', fontSize: 16,
      background: 'oklch(0.585 0.172 257 / 0.18)', color: 'var(--blue-300)',
      border: '1px solid oklch(0.585 0.172 257 / 0.28)',
    },
    brandFoot: { fontSize: 'var(--text-xs)', color: 'var(--slate-500)', fontFamily: 'var(--font-mono)' },
    formWrap: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px', position: 'relative' },
    form: { width: '100%', maxWidth: 360, display: 'flex', flexDirection: 'column', gap: 18 },
    formHead: { marginBottom: 2 },
    title: { fontSize: 'var(--text-2xl)', fontWeight: 600, letterSpacing: 'var(--tracking-snug)' },
    subtitle: { fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginTop: 6 },
    formRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: -4 },
    remember: { display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', cursor: 'pointer' },
    link: { fontSize: 'var(--text-sm)', color: 'var(--text-link)' },
    eye: {
      position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none',
      border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 16, display: 'inline-flex',
      padding: 6, borderRadius: 'var(--radius-xs)',
    },
    demoHint: { fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', lineHeight: 1.6, textAlign: 'center', marginTop: 2 },
    code: { fontFamily: 'var(--font-mono)', background: 'var(--surface-sunken)', padding: '1px 5px', borderRadius: 4, margin: '0 3px', color: 'var(--text-secondary)', fontSize: '0.92em' },
    legal: { position: 'absolute', bottom: 24, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' },
  };

  window.LoginScreen = LoginScreen;
})();
