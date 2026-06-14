import React from 'react';

/** Native select with FinRAG styling and a custom chevron. */
export function Select({ invalid = false, className = '', children, ...rest }) {
  const cls = ['fr-select', invalid ? 'fr-input--invalid' : '', className].filter(Boolean).join(' ');
  return (
    <span className="fr-select-wrap">
      <select className={cls} aria-invalid={invalid || undefined} {...rest}>{children}</select>
      <span className="fr-select-wrap__chevron" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><path d="M6 9l6 6 6-6"/></svg>
      </span>
    </span>
  );
}
