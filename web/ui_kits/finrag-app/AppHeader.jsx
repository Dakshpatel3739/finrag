/* FinRAG UI kit — application header with workspace + role indicator. */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const { IconButton, Avatar, Tooltip } = DS;
  const I = window.Icons;

  function AppHeader({ role = 'finance', email = '', workspace = 'Acme Treasury', onSignOut }) {
    const ROLE_LABEL = { owner: 'Owner', finance: 'Finance', hr: 'HR', employee: 'Employee' };
    const roleLabel = ROLE_LABEL[role] || role;
    return (
      <header style={hdr.bar}>
        <div style={hdr.left}>
          <img src="../../assets/logo-wordmark.svg" alt="FinRAG" height="22" style={{ display: 'block' }} />
          <span style={hdr.divider} />
          <button type="button" style={hdr.workspace}>
            <span style={hdr.wsAvatar}>{workspace.slice(0, 1)}</span>
            <span style={hdr.wsName}>{workspace}</span>
            <span style={{ fontSize: 14, color: 'var(--text-tertiary)', display: 'inline-flex' }}><I.Chevron /></span>
          </button>
        </div>

        <div style={hdr.right}>
          <Tooltip label={`Your role determines which document sections you can see`}>
            <span style={hdr.role}>
              <span style={hdr.roleDot} />
              Signed in as <strong style={hdr.roleName}>{roleLabel}</strong>
            </span>
          </Tooltip>
          <Avatar name={email || role} size="sm" accent />
          <IconButton variant="ghost" label="Sign out" onClick={onSignOut}><I.Logout /></IconButton>
        </div>
      </header>
    );
  }

  const hdr = {
    bar: {
      height: 'var(--topbar-height)', display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', padding: '0 16px',
      background: 'var(--surface-card)', borderBottom: '1px solid var(--border-subtle)',
      position: 'sticky', top: 0, zIndex: 'var(--z-sticky)',
    },
    left: { display: 'flex', alignItems: 'center', gap: 12 },
    divider: { width: 1, height: 22, background: 'var(--border-default)' },
    workspace: {
      display: 'inline-flex', alignItems: 'center', gap: 8, background: 'none',
      border: '1px solid transparent', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
      padding: '5px 8px', font: 'inherit',
    },
    wsAvatar: {
      width: 20, height: 20, borderRadius: 'var(--radius-xs)', background: 'var(--slate-900)',
      color: '#fff', fontSize: 11, fontWeight: 600, display: 'inline-flex',
      alignItems: 'center', justifyContent: 'center',
    },
    wsName: { fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' },
    right: { display: 'flex', alignItems: 'center', gap: 10 },
    role: {
      display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 'var(--text-sm)',
      color: 'var(--text-secondary)', padding: '5px 10px', borderRadius: 'var(--radius-pill)',
      background: 'var(--surface-sunken)', border: '1px solid var(--border-subtle)', cursor: 'default',
      whiteSpace: 'nowrap',
    },
    roleDot: { width: 7, height: 7, borderRadius: '50%', background: 'var(--verified)' },
    roleName: { color: 'var(--text-primary)', fontWeight: 600 },
  };

  window.AppHeader = AppHeader;
})();
