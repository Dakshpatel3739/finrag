import * as React from 'react';

/**
 * Primary action button for FinRAG. Five variants, three sizes, loading + icon support.
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual style. @default "primary" */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'accent-soft';
  /** Control height. @default "md" */
  size?: 'sm' | 'md' | 'lg';
  /** Icon node rendered before the label (16px). */
  leftIcon?: React.ReactNode;
  /** Icon node rendered after the label (16px). */
  rightIcon?: React.ReactNode;
  /** Show spinner and disable interaction. @default false */
  loading?: boolean;
  /** Stretch to full container width. @default false */
  block?: boolean;
  disabled?: boolean;
  children?: React.ReactNode;
}

export function Button(props: ButtonProps): JSX.Element;
