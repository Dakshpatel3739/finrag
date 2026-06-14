import React from 'react';

/** Multi-line text input. Vertically resizable. */
export function Textarea({ invalid = false, className = '', rows = 3, ...rest }) {
  const cls = ['fr-input', invalid ? 'fr-input--invalid' : '', className].filter(Boolean).join(' ');
  return <textarea className={cls} rows={rows} aria-invalid={invalid || undefined} {...rest} />;
}
