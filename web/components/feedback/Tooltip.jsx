import React from 'react';

/** Hover/focus tooltip. Wraps its trigger child; label appears above. */
export function Tooltip({ label, className = '', children, ...rest }) {
  const cls = ['fr-tooltip-wrap', className].filter(Boolean).join(' ');
  return (
    <span className={cls} {...rest}>
      {children}
      <span className="fr-tooltip" role="tooltip">{label}</span>
    </span>
  );
}
