/* FinRAG UI kit — left navigation rail (app shell).
   Owner-only items are gated by `role`. */
(function () {
  const I = window.Icons;

  function NavItem({ icon, label, active, onClick }) {
    const Ico = icon;
    return (
      <button type="button" onClick={onClick}
              style={{ ...nv.item, ...(active ? nv.itemActive : null) }}>
        <span style={{ ...nv.itemIcon, color: active ? 'var(--accent)' : 'var(--text-tertiary)' }}><Ico /></span>
        {label}
      </button>
    );
  }

  function NavSidebar({ view, onNavigate, role }) {
    const isOwner = role === 'owner';
    return (
      <nav style={nv.bar}>
        <div style={nv.group}>
          <span style={nv.groupLabel}>Workspace</span>
          <NavItem icon={I.Ask}   label="Ask"       active={view === 'ask'}  onClick={() => onNavigate('ask')} />
          <NavItem icon={I.Doc}   label="Documents" active={view === 'docs'} onClick={() => onNavigate('docs')} />
        </div>

        {isOwner && (
          <div style={nv.group}>
            <span style={nv.groupLabel}>Administration</span>
            <NavItem icon={I.Shield} label="Access control" active={view === 'admin'} onClick={() => onNavigate('admin')} />
            <NavItem icon={I.Users}  label="Members"        active={view === 'members'} onClick={() => onNavigate('admin')} />
          </div>
        )}

        <div style={nv.spacer} />

        <div style={nv.helpCard}>
          <span style={nv.helpIcon}><I.ShieldCheck /></span>
          <div>
            <div style={nv.helpTitle}>Grounded-only</div>
            <p style={nv.helpText}>Every answer is backed by a cited source you’re authorized to see.</p>
          </div>
        </div>
      </nav>
    );
  }

  const nv = {
    bar: {
      width: 'var(--sidebar-width)', flex: 'none', background: 'var(--surface-card)',
      borderRight: '1px solid var(--border-subtle)', padding: '16px 12px',
      display: 'flex', flexDirection: 'column', gap: 18, height: '100%', overflowY: 'auto',
    },
    group: { display: 'flex', flexDirection: 'column', gap: 2 },
    groupLabel: {
      fontSize: 'var(--text-2xs)', fontWeight: 600, letterSpacing: 'var(--tracking-caps)',
      textTransform: 'uppercase', color: 'var(--text-tertiary)', padding: '4px 10px 6px',
    },
    item: {
      display: 'flex', alignItems: 'center', gap: 10, width: '100%', textAlign: 'left',
      padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid transparent',
      background: 'none', cursor: 'pointer', font: 'inherit', fontSize: 'var(--text-sm)',
      fontWeight: 500, color: 'var(--text-secondary)', transition: 'background .12s, color .12s',
    },
    itemActive: { background: 'var(--accent-soft)', color: 'var(--accent-text)', borderColor: 'var(--accent-soft-bd)' },
    itemIcon: { fontSize: 17, display: 'inline-flex', flex: 'none' },
    spacer: { flex: 1 },
    helpCard: {
      display: 'flex', gap: 9, padding: '12px', borderRadius: 'var(--radius-md)',
      background: 'var(--verified-soft)', border: '1px solid var(--verified-soft-bd)',
    },
    helpIcon: { fontSize: 16, color: 'var(--verified)', display: 'inline-flex', flex: 'none', marginTop: 1 },
    helpTitle: { fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--verified-text)', marginBottom: 2 },
    helpText: { fontSize: 'var(--text-xs)', color: 'var(--verified-text)', opacity: 0.85, lineHeight: 1.45, margin: 0 },
  };

  window.NavSidebar = NavSidebar;
})();
