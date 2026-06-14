import React from 'react';

/** Controlled checkbox with label. */
export function Checkbox({ checked = false, disabled = false, label, onChange, className = '', ...rest }) {
  const cls = ['fr-check', checked ? 'fr-check--checked' : '', className].filter(Boolean).join(' ');
  return (
    <label className={cls} aria-disabled={disabled || undefined}>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={onChange}
        style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }}
        {...rest}
      />
      <span className="fr-check__box" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7"/></svg>
      </span>
      {label && <span className="fr-check__label">{label}</span>}
    </label>
  );
}
