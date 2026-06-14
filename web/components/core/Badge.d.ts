import * as React from 'react';

/** Compact status / label chip. Use `verified` only for grounding/citation states. */
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Color role. @default "neutral" */
  variant?: 'neutral' | 'accent' | 'verified' | 'success' | 'warning' | 'danger' | 'solid';
  /** Show a leading status dot. @default false */
  dot?: boolean;
  /** Use monospace (for ids, counts, percentages). @default false */
  mono?: boolean;
  children?: React.ReactNode;
}

export function Badge(props: BadgeProps): JSX.Element;
