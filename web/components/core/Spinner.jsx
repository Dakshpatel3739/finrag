import React from 'react';

/** Indeterminate loading spinner. */
export function Spinner({ size = 'md', onAccent = false, className = '', ...rest }) {
  const cls = [
    'fr-spinner',
    `fr-spinner--${size}`,
    onAccent ? 'fr-spinner--onaccent' : '',
    className,
  ].filter(Boolean).join(' ');
  return <span className={cls} role="status" aria-label="Loading" {...rest} />;
}
