import React from 'react';

/**
 * Labeled field wrapper. Composes a label, optional hint, control, and error message.
 */
export function Field({ label, hint, error, required = false, htmlFor, className = '', children }) {
  const cls = ['fr-field', className].filter(Boolean).join(' ');
  return (
    <div className={cls}>
      {label && (
        <label className="fr-field__label" htmlFor={htmlFor}>
          {label}{required && <span className="fr-field__req" aria-hidden="true">*</span>}
        </label>
      )}
      {children}
      {error
        ? <span className="fr-field__error">{error}</span>
        : hint && <span className="fr-field__hint">{hint}</span>}
    </div>
  );
}
