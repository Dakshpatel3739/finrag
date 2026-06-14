import React from 'react';

function levelFor(value) {
  if (value >= 0.8) return 'high';
  if (value >= 0.5) return 'medium';
  return 'low';
}

/**
 * Groundedness / confidence meter for an answer. `value` is 0–1.
 */
export function ConfidenceMeter({ value = 0, label = 'Grounding', className = '', ...rest }) {
  const v = Math.max(0, Math.min(1, value));
  const level = levelFor(v);
  const cls = ['fr-confidence', `fr-confidence--${level}`, className].filter(Boolean).join(' ');
  return (
    <div className={cls} {...rest}>
      <div className="fr-confidence__head">
        <span className="fr-confidence__label">{label}</span>
        <span className="fr-confidence__pct">{Math.round(v * 100)}%</span>
      </div>
      <div className="fr-confidence__bar">
        <div className="fr-confidence__fill" style={{ width: `${v * 100}%` }} />
      </div>
    </div>
  );
}
