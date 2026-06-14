import React from 'react';
import { IconButton } from '../core/IconButton.jsx';

const ICONS = {
  info: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>,
  verified: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l7 3v6c0 4-3 6.5-7 9-4-2.5-7-5-7-9V6z"/><path d="M9 12l2 2 4-4"/></svg>,
  warning: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.3 3.8 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>,
  danger: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/></svg>,
};
const Close = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>;

/**
 * Inline contextual alert. Use within content flow (not transient — that's Toast).
 */
export function Banner({ variant = 'info', title, icon, onClose, className = '', children, ...rest }) {
  const cls = ['fr-banner', `fr-banner--${variant}`, className].filter(Boolean).join(' ');
  return (
    <div className={cls} role="status" {...rest}>
      <span className="fr-banner__icon" aria-hidden="true">{icon || ICONS[variant]}</span>
      <div className="fr-banner__body">
        {title && <span className="fr-banner__title">{title}</span>}
        {children && <span>{children}</span>}
      </div>
      {onClose && (
        <span className="fr-banner__close">
          <IconButton size="sm" label="Dismiss" onClick={onClose}><Close/></IconButton>
        </span>
      )}
    </div>
  );
}
