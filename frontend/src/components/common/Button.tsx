import React from 'react';
import { cn } from '../../utils/helpers';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'success';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className,
  disabled,
  leftIcon,
  rightIcon,
  ...props
}) => {
  const getVariantStyles = () => {
    const base = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 'var(--ai-spacing-4)',
      minWidth: size === 'sm' ? '72px' : size === 'lg' ? '100px' : '88px',
      height: size === 'sm' ? '36px' : size === 'lg' ? '52px' : '44px',
      padding: `0 ${size === 'sm' ? 'var(--ai-spacing-8)' : size === 'lg' ? 'var(--ai-spacing-16)' : 'var(--ai-spacing-12)'}`,
      fontFamily: 'var(--ai-font-family)',
      fontSize: 'var(--ai-font-size-button)',
      lineHeight: 'var(--ai-line-height-button)',
      fontWeight: 'var(--ai-font-weight-button)',
      letterSpacing: 'var(--ai-letter-spacing-button)',
      borderRadius: 'var(--ai-radius-full)',
      border: 'none',
      cursor: 'pointer',
      userSelect: 'none',
      whiteSpace: 'nowrap',
      transition: 'background-color 0.15s ease, border-color 0.15s ease, transform 0.1s ease, opacity 0.15s ease',
    };

    if (variant === 'primary') {
      return {
        ...base,
        backgroundColor: 'var(--ai-color-brand-primary)',
        color: 'var(--ai-color-brand-on-primary)',
      };
    } else if (variant === 'secondary') {
      return {
        ...base,
        backgroundColor: 'transparent',
        color: 'var(--ai-color-text-primary)',
        border: '1.5px solid var(--ai-color-border-heavy)',
      };
    } else if (variant === 'danger') {
      return {
        ...base,
        backgroundColor: 'var(--ai-color-brand-error)',
        color: '#ffffff',
      };
    } else if (variant === 'success') {
      return {
        ...base,
        backgroundColor: 'var(--ai-color-brand-success)',
        color: '#ffffff',
      };
    } else {
      return {
        ...base,
        backgroundColor: 'transparent',
        color: 'var(--ai-color-text-primary)',
        border: 'none',
      };
    }
  };

  const isDisabled = disabled || isLoading;
  const baseStyles = getVariantStyles();
  // Remove 'as' prop if present (not supported)
  const { onClick, onMouseEnter: propsOnMouseEnter, onMouseLeave: propsOnMouseLeave, as, ...restProps } = props;

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    // Prevent clicks on disabled buttons
    if (isDisabled) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    
    // Call the provided onClick handler
    if (onClick) {
      try {
        onClick(e);
      } catch (error) {
        console.error('Error in button onClick handler:', error);
        // Re-throw to ensure errors are visible
        throw error;
      }
    } else {
      console.warn('Button clicked but no onClick handler provided');
    }
  };

  const handleMouseEnter = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!isDisabled) {
      if (variant === 'primary') {
        e.currentTarget.style.opacity = '0.9';
      } else if (variant === 'secondary') {
        e.currentTarget.style.borderColor = 'var(--ai-color-text-secondary)';
        e.currentTarget.style.backgroundColor = 'var(--ai-color-bg-secondary)';
      } else if (variant === 'ghost') {
        e.currentTarget.style.backgroundColor = 'var(--ai-color-bg-tertiary)';
      } else if (variant === 'danger') {
        e.currentTarget.style.opacity = '0.9';
      } else if (variant === 'success') {
        e.currentTarget.style.opacity = '0.9';
      }
      if (propsOnMouseEnter) {
        propsOnMouseEnter(e);
      }
    }
  };

  const handleMouseLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!isDisabled) {
      const styles = getVariantStyles();
      Object.assign(e.currentTarget.style, {
        ...styles,
        cursor: 'pointer',
        opacity: '1',
      });
      if (propsOnMouseLeave) {
        propsOnMouseLeave(e);
      }
    }
  };

  return (
    <button
      type="button"
      className={cn('chatkit-button', className)}
      style={{
        ...baseStyles,
        cursor: isDisabled ? 'not-allowed' : 'pointer',
        opacity: isDisabled ? 'var(--ai-opacity-disabled)' : baseStyles.opacity || '1',
        pointerEvents: isDisabled ? 'none' : 'auto',
        position: 'relative',
        zIndex: 1,
      }}
      disabled={isDisabled}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      {...restProps}
    >
      {isLoading ? (
        <>
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Loading...
        </>
      ) : (
        <>
          {leftIcon && <span>{leftIcon}</span>}
          {children}
          {rightIcon && <span>{rightIcon}</span>}
        </>
      )}
    </button>
  );
};
