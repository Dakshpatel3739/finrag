import * as React from 'react';

/** Native `<select>` with FinRAG styling. Pass `<option>` children. */
export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  /** Error styling + aria-invalid. @default false */
  invalid?: boolean;
  children?: React.ReactNode;
}

export function Select(props: SelectProps): JSX.Element;
