import * as React from 'react';

/** CSS-only hover/focus tooltip wrapping a trigger element. */
export interface TooltipProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Tooltip text shown on hover/focus. */
  label: React.ReactNode;
  /** The trigger element. */
  children: React.ReactNode;
}

export function Tooltip(props: TooltipProps): JSX.Element;
