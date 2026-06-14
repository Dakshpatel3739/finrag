import React from 'react';
import { AccessBadge } from './AccessBadge.jsx';

/**
 * A retrieved source chunk shown in the evidence panel beside a cited answer.
 *
 * INVARIANT: only authorized chunks are ever passed to this component. Unauthorized
 * content never enters the answer context, so it is never rendered here — not even as
 * a redacted placeholder (a placeholder would itself reveal that restricted content
 * exists). There is no `locked` state by design.
 */
export function SourceCard({
  refIndex,
  docName,
  page,
  excerpt,
  score,
  access,
  role,
  active = false,
  onClick,
  className = '',
  ...rest
}) {
  const cls = [
    'fr-source',
    onClick ? 'fr-source--interactive' : '',
    active ? 'fr-source--active' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={cls} onClick={onClick} {...rest}>
      <div className="fr-source__head">
        <span className="fr-source__ref">{refIndex}</span>
        <span className="fr-source__doc" title={docName}>{docName}</span>
        <span className="fr-source__meta">
          {page != null && <span>p.{page}</span>}
          {score != null && <span>{Math.round(score * 100)}%</span>}
        </span>
      </div>

      <div
        className="fr-source__excerpt"
        dangerouslySetInnerHTML={typeof excerpt === 'string' ? { __html: excerpt } : undefined}
      >
        {typeof excerpt === 'string' ? undefined : excerpt}
      </div>

      <div className="fr-source__foot">
        {access && <AccessBadge level={access} role={role} />}
      </div>
    </div>
  );
}
