import React from 'react';

/** Controlled toggle switch with optional label. */
export function Switch({ checked = false, disabled = false, label, onChange, className = '', ...rest }) {
  const cls = ['fr-switch', checked ? 'fr-switch--on' : '', className].filter(Boolean).join(' ');
  return (
    <label className={cls} aria-disabled={disabled || undefined}>
      <input
        type="checkbox"
        role="switch"
        checked={checked}
        disabled={disabled}
        onChange={onChange}
        style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }}
        {...rest}
      />
      <span className="fr-switch__track" aria-hidden="true"><span className="fr-switch__thumb" /></span>
      {label && <span className="fr-switch__label">{label}</span>}
    </label>
  );
}
