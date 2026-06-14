import * as React from 'react';

/** Indeterminate loading spinner. */
export interface SpinnerProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** @default "md" */
  size?: 'sm' | 'md' | 'lg';
  /** White spinner for use on accent/dark backgrounds. @default false */
  onAccent?: boolean;
}

export function Spinner(props: SpinnerProps): JSX.Element;
