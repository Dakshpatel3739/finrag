import * as React from 'react';

/** Single-line text input with optional leading icon and invalid state. */
export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** @default "md" */
  size?: 'sm' | 'md' | 'lg';
  /** Error styling + aria-invalid. @default false */
  invalid?: boolean;
  /** Monospace + tabular figures, for ids and numbers. @default false */
  mono?: boolean;
  /** Leading icon node (16px). */
  icon?: React.ReactNode;
}

export function Input(props: InputProps): JSX.Element;
