/* FinRAG UI kit — Screen 2 (HERO): cited-answer query interface.
   States: idle · generating · answer-with-citations · no-authorized-context. */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const { Citation, SourceCard, ConfidenceMeter, Button, IconButton, Badge, EmptyState } = DS;
  const I = window.Icons;
  const FX = window.FINRAG_FIXTURES;

  /* ---- Ask bar -------------------------------------------------- */
  function AskBar({ value, onChange, onSubmit, busy }) {
    return (
      <form style={qs.askForm} onSubmit={(e) => { e.preventDefault(); onSubmit(); }}>
        <span style={qs.askIcon}><I.DocSearch /></span>
        <input
          style={qs.askInput}
          value={value}
          disabled={busy}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Ask a question about your financial documents…"
          aria-label="Ask a question"
        />
        <Button type="submit" variant="primary" loading={busy} disabled={!value.trim()}
                rightIcon={!busy && <I.ArrowUp />}>{busy ? 'Searching' : 'Ask'}</Button>
      </form>
    );
  }

  /* ---- Answer body with inline citations ------------------------ */
  function AnswerBody({ result, activeRef, onCite }) {
    return (
      <p style={qs.answerText}>
        {result.segments.map((seg, i) => {
          if (seg.sourceRef != null) {
            const active = activeRef === seg.sourceRef;
            return (
              <React.Fragment key={i}>
                <span className={active ? 'fr-grounded-text fr-grounded-text--active' : 'fr-grounded-text'}>{seg.text}</span>
                <Citation index={seg.sourceRef} active={active} onClick={() => onCite(seg.sourceRef)} />
              </React.Fragment>
            );
          }
          return <React.Fragment key={i}>{seg.text}</React.Fragment>;
        })}
      </p>
    );
  }

  /* ---- Main screen ---------------------------------------------- */
  function QueryScreen({ session }) {
    const [question, setQuestion] = React.useState('');
    const [status, setStatus] = React.useState('idle'); // idle|loading|answer|nocontext|error
    const [result, setResult] = React.useState(null);
    const [asked, setAsked] = React.useState('');
    const [activeRef, setActiveRef] = React.useState(null);
    const sourceRefs = React.useRef({});
    const panelRef = React.useRef(null);

    async function ask(q) {
      const text = (q ?? question).trim();
      if (!text) return;
      setAsked(text); setQuestion(text); setStatus('loading'); setResult(null); setActiveRef(null);
      try {
        const res = await window.FinRAGAPI.query(text, { token: session.token, role: session.role });
        if (res && res.noContext) { setStatus('nocontext'); return; }
        setResult(res);
        setStatus('answer');
        setActiveRef(res.sources?.[0]?.ref ?? null);
      } catch (e) {
        setStatus('error');
      }
    }

    function focusSource(ref) {
      setActiveRef(ref);
      const el = sourceRefs.current[ref];
      const panel = panelRef.current;
      if (el && panel) panel.scrollTo({ top: el.offsetTop - 12, behavior: 'smooth' });
    }

    const authorizedSources = result?.sources || [];

    return (
      <div style={qs.screen}>
        <div style={qs.askWrap}>
          <div style={qs.askInner}>
            <AskBar value={question} onChange={setQuestion} onSubmit={() => ask()} busy={status === 'loading'} />
          </div>
        </div>

        <div style={qs.body}>
          {status === 'idle' && <IdleState onPick={(q) => ask(q)} />}
          {status === 'loading' && <LoadingState question={asked} />}
          {status === 'error' && <ErrorState onRetry={() => ask(asked)} />}
          {status === 'nocontext' && <NoContextState question={asked} />}

          {status === 'answer' && result && (
            <div style={qs.answerGrid}>
              {/* Answer column */}
              <section style={qs.answerCol}>
                <div style={qs.qEcho}>
                  <span style={qs.qLabel}>Question</span>
                  <span style={qs.qText}>{asked}</span>
                </div>

                <div style={qs.answerHead}>
                  <span style={qs.answerEyebrow}><span style={{display:'inline-flex',fontSize:14,color:'var(--verified)'}}><I.ShieldCheck/></span> Grounded answer</span>
                  <ConfidenceMeter value={result.grounding} label="Grounding" />
                </div>

                <AnswerBody result={result} activeRef={activeRef} onCite={focusSource} />

                <div style={qs.legend}>
                  <span style={qs.legendItem}><span className="fr-grounded-text" style={{padding:'0 4px'}}>highlighted text</span> is backed by its cited source — every claim is grounded</span>
                </div>

                <div style={qs.actions}>
                  <Button variant="secondary" size="sm" leftIcon={<I.Copy />}>Copy with citations</Button>
                  <Button variant="ghost" size="sm" leftIcon={<I.Plus />}>Ask a follow-up</Button>
                </div>
              </section>

              {/* Sources panel */}
              <aside style={qs.sourcesCol} ref={panelRef}>
                <div style={qs.sourcesHead}>
                  <span style={qs.sourcesTitle}>Sources</span>
                  <Badge variant="neutral" mono>{authorizedSources.length}</Badge>
                </div>
                <div style={qs.sourcesList}>
                  {result.sources.map((s) => (
                    <div key={s.ref} ref={(el) => (sourceRefs.current[s.ref] = el)}>
                      <SourceCard
                        refIndex={s.ref}
                        docName={s.docName}
                        page={s.page}
                        score={s.score}
                        excerpt={s.excerpt}
                        access={s.access}
                        active={activeRef === s.ref}
                        onClick={() => focusSource(s.ref)}
                      />
                    </div>
                  ))}
                </div>
                <p style={qs.sourcesFoot}>
                  Sources reflect your access role. Sections outside your permissions are not used to answer.
                </p>
              </aside>
            </div>
          )}
        </div>
      </div>
    );
  }

  /* ---- State views ---------------------------------------------- */
  function IdleState({ onPick }) {
    return (
      <div style={qs.centerWrap}>
        <div style={qs.idleCard}>
          <span style={qs.idleIcon}><I.Sparkle /></span>
          <h2 style={qs.idleTitle}>Ask anything about your documents</h2>
          <p style={qs.idleSub}>Every answer is grounded in cited sources from your indexed filings — and respects your access role.</p>
          <div style={qs.suggest}>
            {FX.suggestedQuestions.map((q) => (
              <button key={q} type="button" style={qs.chip} onClick={() => onPick(q)}>
                <span style={{display:'inline-flex',fontSize:14,color:'var(--text-tertiary)'}}><I.Search/></span>{q}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  function LoadingState({ question }) {
    const steps = ['Retrieving authorized sources', 'Ranking relevant chunks', 'Grounding the answer'];
    const [step, setStep] = React.useState(0);
    React.useEffect(() => {
      const t = setInterval(() => setStep((s) => Math.min(s + 1, steps.length - 1)), 450);
      return () => clearInterval(t);
    }, []);
    return (
      <div style={qs.answerGrid}>
        <section style={qs.answerCol}>
          <div style={qs.qEcho}><span style={qs.qLabel}>Question</span><span style={qs.qText}>{question}</span></div>
          <div style={qs.loadSteps}>
            {steps.map((s, i) => (
              <div key={s} style={{ ...qs.loadStep, opacity: i <= step ? 1 : 0.4 }}>
                {i < step ? <span style={qs.loadDone}><I.Check /></span>
                  : i === step ? <span className="fr-spinner fr-spinner--sm" />
                  : <span style={qs.loadPending} />}
                {s}
              </div>
            ))}
          </div>
          <div style={qs.skeletonWrap}>
            {[100, 96, 88, 70].map((w, i) => <div key={i} style={{ ...qs.skel, width: w + '%' }} />)}
          </div>
        </section>
        <aside style={qs.sourcesCol}>
          <div style={qs.sourcesHead}><span style={qs.sourcesTitle}>Sources</span></div>
          <div style={qs.sourcesList}>
            {[0, 1, 2].map((i) => <div key={i} style={qs.skelCard} />)}
          </div>
        </aside>
      </div>
    );
  }

  function NoContextState({ question }) {
    return (
      <div style={qs.centerWrap}>
        <EmptyState
          icon={<I.DocSearch />}
          title="No authorized sources answer this question"
          description="We couldn’t find anything in the documents you’re authorized to view that answers this. Try rephrasing, or check with a workspace owner if you expect access to more sources."
          actions={<Button variant="secondary" size="sm" leftIcon={<I.Plus />}>Ask a different question</Button>}
        />
        <p style={qs.noCtxQuote}>“{question}”</p>
      </div>
    );
  }

  function ErrorState({ onRetry }) {
    return (
      <div style={qs.centerWrap}>
        <EmptyState
          icon={<I.Alert />}
          title="Something went wrong"
          description="We couldn’t complete that request. Please try again."
          actions={<Button variant="primary" size="sm" onClick={onRetry}>Retry</Button>}
        />
      </div>
    );
  }

  /* ---- Styles --------------------------------------------------- */
  const qs = {
    screen: { height: '100%', minHeight: 0, display: 'flex', flexDirection: 'column', background: 'var(--surface-page)' },
    askWrap: { borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-card)', padding: '14px 24px' },
    askInner: { maxWidth: 'var(--container-max)', margin: '0 auto', width: '100%' },
    askForm: { display: 'flex', alignItems: 'center', gap: 10, position: 'relative' },
    askIcon: { position: 'absolute', left: 13, fontSize: 18, color: 'var(--text-tertiary)', display: 'inline-flex', pointerEvents: 'none' },
    askInput: {
      flex: 1, height: 44, padding: '0 14px 0 40px', fontSize: 'var(--text-md)', fontFamily: 'var(--font-sans)',
      color: 'var(--text-primary)', background: 'var(--surface-card)', border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-md)', outline: 'none',
    },
    body: { flex: 1, overflow: 'hidden', display: 'flex' },

    answerGrid: {
      maxWidth: 'var(--container-max)', margin: '0 auto', width: '100%',
      display: 'grid', gridTemplateColumns: 'minmax(0,1fr) var(--source-panel-w)', gap: 0, height: '100%',
    },
    answerCol: { overflowY: 'auto', padding: '32px 40px', borderRight: '1px solid var(--border-subtle)' },
    qEcho: { display: 'flex', flexDirection: 'column', gap: 5, paddingBottom: 18, marginBottom: 22, borderBottom: '1px solid var(--border-subtle)' },
    qLabel: { fontSize: 'var(--text-2xs)', fontWeight: 600, letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', color: 'var(--text-tertiary)' },
    qText: { fontSize: 'var(--text-xl)', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: 'var(--tracking-snug)', lineHeight: 1.3 },
    answerHead: { display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 24, marginBottom: 16 },
    answerEyebrow: { display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 'var(--text-xs)', fontWeight: 600, letterSpacing: 'var(--tracking-wide)', textTransform: 'uppercase', color: 'var(--verified-text)' },
    answerText: { fontSize: 'var(--text-lg)', lineHeight: 1.75, color: 'var(--text-primary)', maxWidth: 'var(--content-max)' },
    legend: { display: 'flex', alignItems: 'center', gap: 14, marginTop: 24, padding: '10px 14px', background: 'var(--surface-sunken)', borderRadius: 'var(--radius-md)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', flexWrap: 'wrap' },
    legendItem: { display: 'inline-flex', alignItems: 'center', gap: 6 },
    actions: { display: 'flex', gap: 8, marginTop: 22 },

    sourcesCol: { overflowY: 'auto', padding: '24px 20px', background: 'var(--surface-card)', position: 'relative' },
    sourcesHead: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14, position: 'sticky', top: 0 },
    sourcesTitle: { fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: 'var(--tracking-snug)' },
    sourcesList: { display: 'flex', flexDirection: 'column', gap: 10 },
    sourcesFoot: { marginTop: 18, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', lineHeight: 1.5, paddingTop: 14, borderTop: '1px solid var(--border-subtle)' },

    centerWrap: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', overflowY: 'auto' },
    idleCard: { maxWidth: 620, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' },
    idleIcon: {
      width: 52, height: 52, borderRadius: 'var(--radius-lg)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      fontSize: 24, color: 'var(--accent)', background: 'var(--accent-soft)', border: '1px solid var(--accent-soft-bd)', marginBottom: 18,
    },
    idleTitle: { fontSize: 'var(--text-2xl)', fontWeight: 600, letterSpacing: 'var(--tracking-snug)' },
    idleSub: { fontSize: 'var(--text-md)', color: 'var(--text-secondary)', marginTop: 10, lineHeight: 1.6, maxWidth: 480 },
    suggest: { display: 'flex', flexDirection: 'column', gap: 8, marginTop: 26, width: '100%', maxWidth: 480 },
    chip: {
      display: 'flex', alignItems: 'center', gap: 10, textAlign: 'left', width: '100%', cursor: 'pointer',
      padding: '11px 14px', background: 'var(--surface-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)', fontSize: 'var(--text-sm)', color: 'var(--text-primary)', font: 'inherit',
      boxShadow: 'var(--shadow-xs)',
    },

    loadSteps: { display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 26 },
    loadStep: { display: 'flex', alignItems: 'center', gap: 10, fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', transition: 'opacity .2s' },
    loadDone: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 16, height: 16, borderRadius: '50%', background: 'var(--verified)', color: '#fff', fontSize: 11 },
    loadPending: { width: 14, height: 14, borderRadius: '50%', border: '2px solid var(--border-default)' },
    skeletonWrap: { display: 'flex', flexDirection: 'column', gap: 12 },
    skel: { height: 14, borderRadius: 5, background: 'linear-gradient(90deg, var(--slate-150) 25%, var(--slate-100) 37%, var(--slate-150) 63%)', backgroundSize: '400% 100%', animation: 'frShimmer 1.4s ease infinite' },
    skelCard: { height: 92, borderRadius: 'var(--radius-md)', background: 'linear-gradient(90deg, var(--slate-150) 25%, var(--slate-100) 37%, var(--slate-150) 63%)', backgroundSize: '400% 100%', animation: 'frShimmer 1.4s ease infinite' },

    noCtxQuote: { marginTop: 4, fontFamily: 'var(--font-serif)', fontStyle: 'italic', color: 'var(--text-tertiary)', fontSize: 'var(--text-sm)', maxWidth: 420, textAlign: 'center' },
  };

  window.QueryScreen = QueryScreen;
})();
