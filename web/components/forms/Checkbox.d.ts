import * as React from 'react';

/** Controlled checkbox with optional label. */
export interface CheckboxProps {
  /** @default false */
  checked?: boolean;
  disabled?: boolean;
  /** Label text or node rendered after the box. */
  label?: React.ReactNode;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  className?: string;
}

export function Checkbox(props: CheckboxProps): JSX.Element;
