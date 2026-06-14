/* FinRAG UI kit — Screen 4: Owner-only access control.
   Configures which ROLES may retrieve each document section. This is
   POLICY configuration — it shows who is permitted, never the withheld
   content itself. Sections below a role's threshold are never retrieved
   for that role (and never revealed to exist in an answer). */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const { Button, IconButton, Badge, Avatar, Select, Banner, AccessBadge, Tooltip } = DS;
  const I = window.Icons;
  const FX = window.FINRAG_FIXTURES;

  const TIER = {
    public:     { access: 'granted',    label: 'Public' },
    internal:   { access: 'role',       label: 'Internal' },
    restricted: { access: 'restricted', label: 'Restricted' },
  };

  const ROLE_LABEL = { owner: 'Owner', finance: 'Finance', hr: 'HR', employee: 'Employee' };

  function rolesForTier(tier) { return FX.sensitivityAccess[tier] || FX.sensitivityAccess.public; }

  /* ---- Members table -------------------------------------------- */
  function MembersCard({ session }) {
    const [members, setMembers] = React.useState(FX.members);
    function changeRole(id, role) {
      setMembers((m) => m.map((u) => (u.id === id ? { ...u, role } : u)));
    }
    return (
      <section style={ad.card}>
        <div style={ad.cardHead}>
          <div>
            <h2 style={ad.cardTitle}>Members</h2>
            <p style={ad.cardSub}>A member’s role determines which document sections they can retrieve. Only <strong>owner</strong> and <strong>finance</strong> can retrieve restricted sections.</p>
          </div>
          <Button variant="secondary" size="sm" leftIcon={<I.Plus />}>Invite member</Button>
        </div>
        <div style={ad.memberTable}>
          {members.map((u) => {
            const isSelf = u.email === session.email;
            return (
              <div key={u.id} style={ad.memberRow}>
                <div style={ad.memberId}>
                  <Avatar name={u.name} size="md" accent={u.role === 'owner'} />
                  <div style={{ minWidth: 0 }}>
                    <div style={ad.memberName}>{u.name}{isSelf && <span style={ad.youTag}>You</span>}</div>
                    <div style={ad.memberEmail}>{u.email}</div>
                  </div>
                </div>
                <div style={ad.memberLast}>Active {new Date(u.lastActive + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                <div style={{ width: 150 }}>
                  <Select value={u.role} disabled={isSelf} onChange={(e) => changeRole(u.id, e.target.value)}>
                    {FX.roles.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
                  </Select>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <IconButton variant="ghost" label="Member options" disabled={isSelf}><I.Dots /></IconButton>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    );
  }

  /* ---- Section access matrix ------------------------------------ */
  function MatrixCard() {
    const [sections, setSections] = React.useState(FX.sections);
    function setTier(id, sensitivity) {
      setSections((s) => s.map((sec) => (sec.id === id ? { ...sec, sensitivity } : sec)));
    }
    return (
      <section style={ad.card}>
        <div style={ad.cardHead}>
          <div>
            <h2 style={ad.cardTitle}>Section access policy</h2>
            <p style={ad.cardSub}>Set the sensitivity of each document section. Public and internal sections are retrievable by all roles; restricted sections are retrievable by owner and finance only — hr and employee can never see, or learn of, restricted content.</p>
          </div>
        </div>

        {/* Matrix header */}
        <div style={ad.matrixHead}>
          <span style={ad.colSection}>Document section</span>
          {FX.roles.map((r) => (
            <span key={r} style={ad.colRole}>{ROLE_LABEL[r]}</span>
          ))}
          <span style={ad.colMin}>Sensitivity</span>
        </div>

        {sections.map((sec) => {
          const allowed = rolesForTier(sec.sensitivity);
          const tier = TIER[sec.sensitivity] || TIER.public;
          return (
            <div key={sec.id} style={ad.matrixRow}>
              <div style={ad.colSection}>
                <div style={ad.secLabelRow}>
                  <span style={ad.secLabel}>{sec.label}</span>
                  {sec.sensitivity === 'public'
                    ? <Badge variant="neutral">{tier.label}</Badge>
                    : <AccessBadge level={tier.access} role={tier.label}>{tier.label}</AccessBadge>}
                </div>
                <div style={ad.secDetail}>{sec.detail}</div>
              </div>

              {FX.roles.map((r) => {
                const ok = allowed.includes(r);
                return (
                  <span key={r} style={ad.colRole}>
                    {ok
                      ? <span style={ad.cellOk} title={`${ROLE_LABEL[r]} can retrieve this section`}><I.Check /></span>
                      : <span style={ad.cellNo} title={`${ROLE_LABEL[r]} cannot retrieve this section`}><I.Lock /></span>}
                  </span>
                );
              })}

              <div style={ad.colMin}>
                <Select value={sec.sensitivity} onChange={(e) => setTier(sec.id, e.target.value)}>
                  {FX.sensitivityTiers.map((t) => <option key={t} value={t}>{TIER[t].label}</option>)}
                </Select>
              </div>
            </div>
          );
        })}

        <div style={ad.matrixFoot}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span style={ad.cellOk}><I.Check /></span> Can retrieve</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span style={ad.cellNo}><I.Lock /></span> Never retrieved or revealed</span>
        </div>
      </section>
    );
  }

  function AdminScreen({ session }) {
    if (session.role !== 'owner') {
      return (
        <div style={ad.screen}>
          <div style={{ ...ad.inner, maxWidth: 520 }}>
            <Banner variant="info" title="Owner access required">
              Access control is managed by workspace owners. Ask an owner if you need a section opened up for your role.
            </Banner>
          </div>
        </div>
      );
    }
    return (
      <div style={ad.screen}>
        <div style={ad.inner}>
          <div style={ad.head}>
            <div>
              <h1 style={ad.title}>Access control</h1>
              <p style={ad.subtitle}>Govern which roles can retrieve each document section across the workspace.</p>
            </div>
            <Button variant="primary" leftIcon={<I.ShieldCheck />}>Save policy</Button>
          </div>

          <Banner variant="verified" title="How access shapes answers" className="" >
            Retrieval respects these rules at the chunk level. Sections above a member’s role are never added to a query’s context — and are never hinted at in an answer. There is no “restricted” placeholder: for an unauthorized role, the content simply isn’t there.
          </Banner>

          <div style={{ height: 20 }} />
          <MembersCard session={session} />
          <div style={{ height: 16 }} />
          <MatrixCard />
        </div>
      </div>
    );
  }

  const ad = {
    screen: { flex: 1, overflowY: 'auto', background: 'var(--surface-page)' },
    inner: { maxWidth: 'var(--container-max)', margin: '0 auto', padding: '28px 32px 48px' },
    head: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 24, marginBottom: 20 },
    title: { fontSize: 'var(--text-2xl)', fontWeight: 600, letterSpacing: 'var(--tracking-snug)' },
    subtitle: { fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginTop: 5 },

    card: { background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' },
    cardHead: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 20, padding: '18px 20px', borderBottom: '1px solid var(--border-subtle)' },
    cardTitle: { fontSize: 'var(--text-lg)', fontWeight: 600, letterSpacing: 'var(--tracking-snug)' },
    cardSub: { fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginTop: 4, maxWidth: 560, lineHeight: 1.5 },

    /* members */
    memberTable: { display: 'flex', flexDirection: 'column' },
    memberRow: { display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 140px 150px 44px', gap: 16, alignItems: 'center', padding: '12px 20px', borderBottom: '1px solid var(--border-subtle)' },
    memberId: { display: 'flex', alignItems: 'center', gap: 11, minWidth: 0 },
    memberName: { fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 },
    youTag: { fontSize: 'var(--text-2xs)', fontWeight: 600, color: 'var(--accent-text)', background: 'var(--accent-soft)', border: '1px solid var(--accent-soft-bd)', borderRadius: 'var(--radius-xs)', padding: '0 5px', letterSpacing: 'var(--tracking-wide)' },
    memberEmail: { fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' },
    memberLast: { fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' },

    /* matrix */
    matrixHead: {
      display: 'grid', gridTemplateColumns: 'minmax(0,1fr) repeat(4, 64px) 150px', gap: 12, alignItems: 'center',
      padding: '10px 20px', background: 'var(--surface-sunken)', borderBottom: '1px solid var(--border-subtle)',
      fontSize: 'var(--text-2xs)', fontWeight: 600, letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', color: 'var(--text-tertiary)',
    },
    matrixRow: { display: 'grid', gridTemplateColumns: 'minmax(0,1fr) repeat(4, 64px) 150px', gap: 12, alignItems: 'center', padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)' },
    colSection: { minWidth: 0 },
    colRole: { display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' },
    colMin: { display: 'flex', justifyContent: 'flex-end' },
    secLabelRow: { display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
    secLabel: { fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' },
    secDetail: { fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', marginTop: 3 },
    cellOk: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 22, height: 22, borderRadius: 'var(--radius-xs)', background: 'var(--verified-soft)', color: 'var(--verified)', fontSize: 14, border: '1px solid var(--verified-soft-bd)' },
    cellNo: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 22, height: 22, borderRadius: 'var(--radius-xs)', background: 'var(--surface-sunken)', color: 'var(--text-disabled)', fontSize: 12, border: '1px solid var(--border-subtle)' },
    matrixFoot: { display: 'flex', gap: 20, padding: '12px 20px', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' },
  };

  window.AdminScreen = AdminScreen;
})();
