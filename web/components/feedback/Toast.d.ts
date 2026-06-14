import * as React from 'react';

/** Transient notification toast. Place inside a fixed bottom/top stack. */
export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  /** @default "info" */
  variant?: 'info' | 'verified' | 'danger';
  title?: React.ReactNode;
  onClose?: () => void;
  /** Description line. */
  children?: React.ReactNode;
}

export function Toast(props: ToastProps): JSX.Element;
