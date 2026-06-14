import * as React from 'react';

/** Icon-only button for toolbars and dense controls. Requires an accessible `label`. */
export interface IconButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'aria-label'> {
  /** Visual style. @default "ghost" */
  variant?: 'ghost' | 'solid';
  /** Square size. @default "md" */
  size?: 'sm' | 'md' | 'lg';
  /** Accessible label (also used as tooltip title). Required. */
  label: string;
  disabled?: boolean;
  /** The icon element (18px). */
  children: React.ReactNode;
}

export function IconButton(props: IconButtonProps): JSX.Element;
