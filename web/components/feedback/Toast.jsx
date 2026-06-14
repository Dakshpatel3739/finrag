import React from 'react';
import { IconButton } from '../core/IconButton.jsx';

const ICONS = {
  verified: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/></svg>,
  info: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>,
  danger: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/></svg>,
};
const Close = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>;

/** Transient notification. Render inside a fixed-position stack. */
export function Toast({ variant = 'info', title, onClose, className = '', children, ...rest }) {
  const cls = ['fr-toast', `fr-toast--${variant}`, className].filter(Boolean).join(' ');
  return (
    <div className={cls} role="status" {...rest}>
      <span className="fr-toast__icon" aria-hidden="true">{ICONS[variant]}</span>
      <div className="fr-toast__body">
        {title && <span className="fr-toast__title">{title}</span>}
        {children && <span className="fr-toast__desc">{children}</span>}
      </div>
      {onClose && (
        <span className="fr-toast__close">
          <IconButton size="sm" label="Dismiss" onClick={onClose}><Close/></IconButton>
        </span>
      )}
    </div>
  );
}
