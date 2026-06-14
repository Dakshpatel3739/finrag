import * as React from 'react';

/** User / entity avatar. Renders `src` image or initials derived from `name`. */
export interface AvatarProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Full name — used for initials fallback and title. */
  name?: string;
  /** Image URL. Falls back to initials when absent. */
  src?: string;
  /** @default "md" */
  size?: 'xs' | 'sm' | 'md' | 'lg';
  /** Cobalt-tinted fallback instead of slate. @default false */
  accent?: boolean;
  /** Rounded-square shape instead of circle. @default false */
  square?: boolean;
}

export function Avatar(props: AvatarProps): JSX.Element;
