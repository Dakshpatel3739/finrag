import * as React from 'react';

/** Labeled wrapper around a form control: label, hint, required marker, error message. */
export interface FieldProps {
  /** Field label text. */
  label?: React.ReactNode;
  /** Helper text shown below when there is no error. */
  hint?: React.ReactNode;
  /** Error message — replaces hint and styles red when present. */
  error?: React.ReactNode;
  /** Show required asterisk. @default false */
  required?: boolean;
  /** Associates label with the control. */
  htmlFor?: string;
  className?: string;
  /** The form control. */
  children: React.ReactNode;
}

export function Field(props: FieldProps): JSX.Element;
