import * as React from 'react';

/**
 * A retrieved source chunk in the evidence panel beside a cited answer.
 *
 * INVARIANT: only authorized chunks reach this component. Unauthorized content never
 * enters the answer context, so it is never rendered — not even as a redacted
 * placeholder. There is intentionally no `locked` prop. In the answer view `access`
 * is `"granted"` or `"role"`; the policy-only `restricted`/`confidential` levels are
 * for the owner admin panel, not for marking withheld answer sources.
 */
export interface SourceCardProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'children'> {
  /** Citation number matching the inline marker. */
  refIndex: number | string;
  /** Source document name. */
  docName: string;
  /** Page number within the document. */
  page?: number | string;
  /** Supporting snippet — string (may contain `<mark>` highlights) or a node. */
  excerpt?: React.ReactNode;
  /** Retrieval relevance 0–1, rendered as a percentage. */
  score?: number;
  /** Access badge shown in the footer. */
  access?: 'granted' | 'restricted' | 'confidential' | 'role';
  /** Role label when `access="role"`. */
  role?: string;
  /** Highlighted (currently focused) state. @default false */
  active?: boolean;
  onClick?: React.MouseEventHandler<HTMLDivElement>;
}

export function SourceCard(props: SourceCardProps): JSX.Element;
