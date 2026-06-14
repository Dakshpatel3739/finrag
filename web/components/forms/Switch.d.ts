import * as React from 'react';

/** Controlled toggle switch with optional trailing label. */
export interface SwitchProps {
  /** @default false */
  checked?: boolean;
  disabled?: boolean;
  label?: React.ReactNode;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  className?: string;
}

export function Switch(props: SwitchProps): JSX.Element;
