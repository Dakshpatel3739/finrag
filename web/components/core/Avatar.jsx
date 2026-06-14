import React from 'react';

function initials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * User / entity avatar. Shows an image when `src` is set, otherwise initials from `name`.
 */
export function Avatar({
  name = '',
  src,
  size = 'md',
  accent = false,
  square = false,
  className = '',
  ...rest
}) {
  const cls = [
    'fr-avatar',
    `fr-avatar--${size}`,
    accent ? 'fr-avatar--accent' : '',
    square ? 'fr-avatar--square' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <span className={cls} title={name || undefined} {...rest}>
      {src ? <img src={src} alt={name} /> : initials(name)}
    </span>
  );
}
