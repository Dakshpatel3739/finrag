import React from 'react';

/**
 * Text input. Supports a leading icon, invalid state, sizes and mono (for ids/figures).
 */
export function Input({
  size = 'md',
  invalid = false,
  mono = false,
  icon,
  className = '',
  ...rest
}) {
  const cls = [
    'fr-input',
    size !== 'md' ? `fr-input--${size}` : '',
    invalid ? 'fr-input--invalid' : '',
    mono ? 'fr-input--mono' : '',
    className,
  ].filter(Boolean).join(' ');

  const input = <input className={cls} aria-invalid={invalid || undefined} {...rest} />;

  if (!icon) return input;
  return (
    <span className="fr-input-group">
      <span className="fr-input-group__icon" aria-hidden="true">{icon}</span>
      {input}
    </span>
  );
}
