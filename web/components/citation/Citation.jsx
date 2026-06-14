import React from 'react';

/**
 * Inline citation reference chip. Anchors a claim in an answer to its source chunk.
 * Render inside answer text, immediately after the clause it grounds.
 *
 * GROUNDED-ONLY: every Citation must map to a real source. There is no
 * ungrounded / model-only variant — if a claim can't be cited, it isn't shown.
 */
export function Citation({ index, active = false, className = '', children, ...rest }) {
  const cls = [
    'fr-cite',
    active ? 'fr-cite--active' : '',
    className,
  ].filter(Boolean).join(' ');
  return (
    <button type="button" className={cls} aria-label={`Source ${index ?? children}`} {...rest}>
      {children ?? index}
    </button>
  );
}
