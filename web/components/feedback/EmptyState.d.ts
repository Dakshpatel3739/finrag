import * as React from 'react';

/** Centered zero / empty state for lists, search results and panels. */
export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Icon node (22px) shown in a tile. */
  icon?: React.ReactNode;
  title?: React.ReactNode;
  description?: React.ReactNode;
  /** Action buttons row. */
  actions?: React.ReactNode;
}

export function EmptyState(props: EmptyStateProps): JSX.Element;
