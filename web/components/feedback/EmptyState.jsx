import React from 'react';

/** Centered empty / zero-state with icon, message and optional actions. */
export function EmptyState({ icon, title, description, actions, className = '', ...rest }) {
  const cls = ['fr-empty', className].filter(Boolean).join(' ');
  return (
    <div className={cls} {...rest}>
      {icon && <span className="fr-empty__icon" aria-hidden="true">{icon}</span>}
      {title && <div className="fr-empty__title">{title}</div>}
      {description && <p className="fr-empty__desc">{description}</p>}
      {actions && <div className="fr-empty__actions">{actions}</div>}
    </div>
  );
}
