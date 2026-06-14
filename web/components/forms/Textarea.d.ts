import * as React from 'react';

/** Multi-line text input, vertically resizable. */
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Error styling + aria-invalid. @default false */
  invalid?: boolean;
}

export function Textarea(props: TextareaProps): JSX.Element;
