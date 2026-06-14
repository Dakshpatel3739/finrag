import * as React from 'react';

/** Chunk-level role-based access indicator for retrieved sources. */
export interface AccessBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Access state. @default "granted" */
  level?: 'granted' | 'restricted' | 'confidential' | 'role';
  /** Role label (used when `level="role"`). */
  role?: string;
  /** Override the default label text. */
  children?: React.ReactNode;
}

export function AccessBadge(props: AccessBadgeProps): JSX.Element;
