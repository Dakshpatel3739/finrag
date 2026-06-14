import React from 'react';

/**
 * Square icon-only button for toolbars and dense controls.
 * Always pass `label` for accessibility.
 */
export function IconButton({
  variant = 'ghost',
  size = 'md',
  label,
  disabled = false,
  className = '',
  children,
  ...rest
}) {
  const cls = [
    'fr-iconbtn',
    `fr-iconbtn--${variant}`,
    `fr-iconbtn--${size}`,
    className,
  ].filter(Boolean).join(' ');

  return (
    <button type="button" className={cls} disabled={disabled} aria-label={label} title={label} {...rest}>
      {children}
    </button>
  );
}
