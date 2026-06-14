import * as React from 'react';

/** Groundedness / confidence meter for an answer. Color tier derives from `value`. */
export interface ConfidenceMeterProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 0–1. ≥0.8 high (green), ≥0.5 medium (amber), else low (red). */
  value?: number;
  /** Caption above the bar. @default "Grounding" */
  label?: string;
}

export function ConfidenceMeter(props: ConfidenceMeterProps): JSX.Element;
