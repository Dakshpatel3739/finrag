import * as React from 'react';

/**
 * Inline citation reference chip — anchors an answer claim to its source chunk.
 * The signature grounding affordance: clicking should activate the matching SourceCard.
 *
 * GROUNDED-ONLY: every Citation maps to a real source. There is intentionally no
 * "ungrounded" variant — uncited claims are suppressed upstream, never rendered.
 */
export interface CitationProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  /** Source number shown in the chip (also used as label). */
  index?: number | string;
  /** Highlighted (currently focused) state. @default false */
  active?: boolean;
  /** Overrides the displayed label (defaults to `index`). */
  children?: React.ReactNode;
}

export function Citation(props: CitationProps): JSX.Element;
