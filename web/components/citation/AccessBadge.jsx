import React from 'react';

const LockIcon = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>;
const CheckIcon = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7"/></svg>;
const ShieldIcon = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l7 3v6c0 4-3 6.5-7 9-4-2.5-7-5-7-9V6z"/></svg>;

const PRESET = {
  granted:      { icon: <CheckIcon/>, label: 'Authorized' },
  restricted:   { icon: <LockIcon/>,  label: 'Restricted' },
  confidential: { icon: <ShieldIcon/>,label: 'Confidential' },
};

/**
 * Chunk-level role-based access indicator. Use `level="role"` with a `role`
 * prop to show which role a chunk is scoped to.
 */
export function AccessBadge({ level = 'granted', role, className = '', children, ...rest }) {
  const cls = ['fr-access', `fr-access--${level}`, className].filter(Boolean).join(' ');
  if (level === 'role') {
    return <span className={cls} {...rest}>{children ?? role}</span>;
  }
  const preset = PRESET[level] || PRESET.granted;
  return (
    <span className={cls} {...rest}>
      {preset.icon}
      {children ?? preset.label}
    </span>
  );
}
