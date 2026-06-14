import React from 'react';

/**
 * Compact status / label chip. Verified variant carries the grounding signal.
 */
export function Badge({
  variant = 'neutral',
  dot = false,
  mono = false,
  className = '',
  children,
  ...rest
}) {
  const cls = [
    'fr-badge',
    `fr-badge--${variant}`,
    dot ? 'fr-badge--dot' : '',
    mono ? 'fr-badge--mono' : '',
    className,
  ].filter(Boolean).join(' ');

  return <span className={cls} {...rest}>{children}</span>;
}
