/* FinRAG UI kit — Screen 3: Document library / dashboard.
   List of indexed filings with status, metadata, search, filter,
   upload, and empty states. Composes DS primitives. */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const { Button, IconButton, Badge, Avatar, StatTile, Input, EmptyState, ProgressBar, Tooltip } = DS;
  const I = window.Icons;
  const FX = window.FINRAG_FIXTURES;

  const STATUS = {
    indexed:    { variant: 'verified', label: 'Indexed', dot: true },
    processing: { variant: 'accent',   label: 'Processing', dot: true },
    failed:     { variant: 'danger',   label: 'Failed', dot: true },
  };

  const TABS = [
    { id: 'all', label: 'All' },
    { id: 'indexed', label: 'Indexed' },
    { id: 'processing', label: 'Processing' },
    { id: 'failed', label: 'Needs attention' },
  ];

  function fmtDate(s) {
    const d = new Date(s + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  function DocRow({ doc }) {
    const st = STATUS[doc.status] || STATUS.indexed;
    return (
      <div style={ds.row}>
        <div style={ds.cellName}>
          <span style={{ ...ds.fileIcon, ...(doc.status === 'failed' ? ds.fileIconFail : null) }}>
            <I.Doc />
          </span>
          <div style={{ minWidth: 0 }}>
            <div style={ds.fileName} title={doc.name}>{doc.name}</div>
            <div style={ds.fileMeta}>
              <span className="num">{doc.id}</span>
              <span style={ds.metaDot} />
              <span>{doc.kind}</span>
              <span style={ds.metaDot} />
              <span>{doc.fiscalYear}</span>
            </div>
            {doc.status === 'failed' && doc.error && (
              <div style={ds.errLine}><span style={{ fontSize: 12, display: 'inline-flex' }}><I.Alert /></span>{doc.error}</div>
            )}
          </div>
        </div>

        <div style={ds.cellStatus}>
          {doc.status === 'processing' ? (
            <div style={{ width: 132 }}>
              <ProgressBar value={doc.progress} indeterminate={false} />
              <span style={ds.procLabel}>Indexing · {Math.round((doc.progress || 0) * 100)}%</span>
            </div>
          ) : (
            <Badge variant={st.variant} dot={st.dot}>{st.label}</Badge>
          )}
        </div>

        <div style={ds.cellNum}>
          <span className="num" style={ds.numVal}>{doc.chunks ? doc.chunks.toLocaleString() : '—'}</span>
          <span style={ds.numLabel}>chunks · {doc.pages} pp</span>
        </div>

        <div style={ds.cellDate}>
          <span style={ds.dateVal}>{fmtDate(doc.uploaded)}</span>
          <span style={ds.ownerRow}><Avatar name={doc.owner} size="xs" /> {doc.owner.split(' ')[0]}</span>
        </div>

        <div style={ds.cellActions}>
          {doc.status === 'failed'
            ? <Button variant="secondary" size="sm" leftIcon={<I.Upload />}>Re-upload</Button>
            : <Tooltip label="Ask about this document"><IconButton variant="ghost" label="Ask"><I.Ask /></IconButton></Tooltip>}
          <IconButton variant="ghost" label="More"><I.Dots /></IconButton>
        </div>
      </div>
    );
  }

  function DocumentsScreen() {
    const [tab, setTab] = React.useState('all');
    const [q, setQ] = React.useState('');
    const stats = FX.documentStats;

    const filtered = FX.documents.filter((d) => {
      const matchTab = tab === 'all' ? true
        : tab === 'failed' ? d.status === 'failed'
        : d.status === tab;
      const matchQ = !q.trim() || (d.name + ' ' + d.kind + ' ' + d.fiscalYear + ' ' + d.id).toLowerCase().includes(q.toLowerCase());
      return matchTab && matchQ;
    });

    const counts = {
      all: FX.documents.length,
      indexed: FX.documents.filter((d) => d.status === 'indexed').length,
      processing: FX.documents.filter((d) => d.status === 'processing').length,
      failed: FX.documents.filter((d) => d.status === 'failed').length,
    };

    return (
      <div style={ds.screen}>
        <div style={ds.inner}>
          {/* Header */}
          <div style={ds.head}>
            <div>
              <h1 style={ds.title}>Documents</h1>
              <p style={ds.subtitle}>Filings and reports indexed for grounded retrieval.</p>
            </div>
            <div style={ds.headActions}>
              <Button variant="secondary" leftIcon={<I.Filter />}>Filter</Button>
              <Button variant="primary" leftIcon={<I.Upload />}>Upload document</Button>
            </div>
          </div>

          {/* Stats */}
          <div style={ds.stats}>
            <StatTile label="Documents" value={String(stats.total)} />
            <StatTile label="Indexed" value={String(stats.indexed)} meta={<span style={{ color: 'var(--verified-text)' }}>Ready to query</span>} />
            <StatTile label="Total chunks" value={stats.chunks.toLocaleString()} />
            <StatTile label="Processing" value={String(stats.processing)} meta="≈ 2 min remaining" />
          </div>

          {/* Toolbar */}
          <div style={ds.toolbar}>
            <div className="fr-tabs" style={{ border: 'none' }}>
              {TABS.map((t) => (
                <button key={t.id} className={'fr-tab' + (tab === t.id ? ' fr-tab--active' : '')} onClick={() => setTab(t.id)}>
                  {t.label}<span className="fr-tab__count">{counts[t.id]}</span>
                </button>
              ))}
            </div>
            <div style={{ width: 260 }}>
              <Input icon={<I.Search />} placeholder="Search documents…" value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
          </div>

          {/* Table */}
          <div style={ds.tableWrap}>
            <div style={ds.table}>
              <div style={ds.theadRow}>
                <span style={ds.cellName}>Document</span>
                <span style={ds.cellStatus}>Status</span>
                <span style={ds.cellNum}>Indexed</span>
                <span style={ds.cellDate}>Uploaded</span>
                <span style={ds.cellActions} />
              </div>
              {filtered.length === 0 ? (
                <EmptyState
                  icon={<I.DocSearch />}
                  title={q ? 'No documents match your search' : 'Nothing here yet'}
                  description={q ? 'Try a different filename, year or document type.' : 'Upload a filing to start asking grounded questions.'}
                  actions={q ? <Button variant="secondary" size="sm" onClick={() => setQ('')}>Clear search</Button>
                              : <Button variant="primary" size="sm" leftIcon={<I.Upload />}>Upload document</Button>}
                />
              ) : (
                filtered.map((d) => <DocRow key={d.id} doc={d} />)
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const ds = {
    screen: { flex: 1, overflowY: 'auto', background: 'var(--surface-page)' },
    inner: { maxWidth: 'var(--container-max)', margin: '0 auto', padding: '28px 32px 48px' },
    head: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 24, marginBottom: 22 },
    title: { fontSize: 'var(--text-2xl)', fontWeight: 600, letterSpacing: 'var(--tracking-snug)' },
    subtitle: { fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginTop: 5 },
    headActions: { display: 'flex', gap: 8, flex: 'none' },

    stats: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, marginBottom: 24 },

    toolbar: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, marginBottom: 14, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 12 },

    table: { background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', minWidth: 720 },
    tableWrap: { overflowX: 'auto', borderRadius: 'var(--radius-lg)' },
    theadRow: {
      display: 'grid', gridTemplateColumns: 'minmax(200px,1fr) 132px 116px 140px 96px', gap: 14,
      padding: '10px 18px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-sunken)',
      fontSize: 'var(--text-2xs)', fontWeight: 600, letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', color: 'var(--text-tertiary)',
    },
    row: {
      display: 'grid', gridTemplateColumns: 'minmax(200px,1fr) 132px 116px 140px 96px', gap: 14,
      padding: '14px 18px', borderBottom: '1px solid var(--border-subtle)', alignItems: 'center',
      transition: 'background .12s',
    },
    cellName: { display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 },
    fileIcon: {
      width: 36, height: 36, flex: 'none', borderRadius: 'var(--radius-sm)', display: 'inline-flex',
      alignItems: 'center', justifyContent: 'center', fontSize: 18,
      background: 'var(--accent-soft)', color: 'var(--accent)', border: '1px solid var(--accent-soft-bd)',
    },
    fileIconFail: { background: 'var(--danger-soft)', color: 'var(--danger)', borderColor: 'var(--danger-soft-bd)' },
    fileName: { fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
    fileMeta: { display: 'flex', alignItems: 'center', gap: 7, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', marginTop: 2 },
    metaDot: { width: 3, height: 3, borderRadius: '50%', background: 'var(--border-strong)' },
    errLine: { display: 'flex', alignItems: 'center', gap: 5, marginTop: 5, fontSize: 'var(--text-xs)', color: 'var(--danger-text)' },

    cellStatus: { display: 'flex', alignItems: 'center' },
    procLabel: { display: 'block', marginTop: 5, fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' },

    cellNum: { display: 'flex', flexDirection: 'column', gap: 1 },
    numVal: { fontSize: 'var(--text-sm)', color: 'var(--text-primary)', fontWeight: 500 },
    numLabel: { fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)' },

    cellDate: { display: 'flex', flexDirection: 'column', gap: 4 },
    dateVal: { fontSize: 'var(--text-sm)', color: 'var(--text-primary)' },
    ownerRow: { display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' },

    cellActions: { display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 },
  };

  window.DocumentsScreen = DocumentsScreen;
})();
