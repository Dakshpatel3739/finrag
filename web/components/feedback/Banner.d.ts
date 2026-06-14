import * as React from 'react';

/** Inline contextual alert placed within content flow. */
export interface BannerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Color + default icon. @default "info" */
  variant?: 'info' | 'verified' | 'warning' | 'danger';
  /** Bold title line. */
  title?: React.ReactNode;
  /** Override the default variant icon (18px). */
  icon?: React.ReactNode;
  /** When provided, shows a dismiss button. */
  onClose?: () => void;
  children?: React.ReactNode;
}

export function Banner(props: BannerProps): JSX.Element;
