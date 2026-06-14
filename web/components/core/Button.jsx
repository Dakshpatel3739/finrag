import React from 'react';
import { Spinner } from './Spinner.jsx';

/**
 * FinRAG primary action button. Token-driven, five variants, three sizes.
 */
export function Button({
  variant = 'primary',
  size = 'md',
  leftIcon,
  rightIcon,
  loading = false,
  block = false,
  disabled = false,
  type = 'button',
  className = '',
  children,
  ...rest
}) {
  const cls = [
    'fr-btn',
    `fr-btn--${variant}`,
    `fr-btn--${size}`,
    block ? 'fr-btn--block' : '',
    className,
  ].filter(Boolean).join(' ');

  const isDisabled = disabled || loading;

  return (
    <button type={type} className={cls} disabled={isDisabled} aria-busy={loading || undefined} {...rest}>
      {loading
        ? <Spinner size="sm" onAccent={variant === 'primary' || variant === 'danger'} />
        : leftIcon && <span className="fr-btn__icon" aria-hidden="true">{leftIcon}</span>}
      {children && <span>{children}</span>}
      {!loading && rightIcon && <span className="fr-btn__icon" aria-hidden="true">{rightIcon}</span>}
    </button>
  );
}
