import React from 'react';
import { cn } from '../../utils/helpers';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement | HTMLTextAreaElement> {
  label?: string;
  error?: string;
  multiline?: boolean;
  rows?: number;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  className,
  id,
  multiline,
  rows = 3,
  onChange,
  value,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const inputStyles: React.CSSProperties = {
    width: '100%',
    padding: 'var(--ai-spacing-4) var(--ai-spacing-6)',
    fontFamily: 'var(--ai-font-family)',
    fontSize: 'var(--ai-font-size-body-small)',
    lineHeight: 'var(--ai-line-height-body-small)',
    fontWeight: 'var(--ai-font-weight-body-small)',
    letterSpacing: 'var(--ai-letter-spacing-body-small)',
    color: 'var(--ai-color-text-primary)',
    backgroundColor: 'var(--ai-color-bg-primary)',
    border: error ? '1.5px solid var(--ai-color-brand-error)' : '1.5px solid var(--ai-color-border-heavy)',
    borderRadius: 'var(--ai-radius-base)',
    transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
  };

  return (
    <div className="w-full">
      {label && (
        <label 
          htmlFor={inputId} 
          style={{
            display: 'block',
            fontSize: 'var(--ai-font-size-body-small-emph)',
            fontWeight: 'var(--ai-font-weight-body-small-emph)',
            lineHeight: 'var(--ai-line-height-body-small-emph)',
            letterSpacing: 'var(--ai-letter-spacing-body-small-emph)',
            color: 'var(--ai-color-text-primary)',
            marginBottom: 'var(--ai-spacing-4)',
          }}
        >
          {label}
        </label>
      )}
      {multiline ? (
        <textarea
          id={inputId}
          rows={rows}
          className={cn('chatkit-input', className)}
          style={inputStyles}
          value={value}
          onChange={onChange}
          {...(props as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
        />
      ) : (
        <input
          id={inputId}
          className={cn('chatkit-input', className)}
          style={inputStyles}
          value={value}
          onChange={onChange}
          {...(props as React.InputHTMLAttributes<HTMLInputElement>)}
        />
      )}
      {error && (
        <p 
          style={{
            marginTop: 'var(--ai-spacing-4)',
            fontSize: 'var(--ai-font-size-body-small)',
            color: 'var(--ai-color-brand-error)',
            fontWeight: 'var(--ai-font-weight-medium)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ai-spacing-2)',
          }}
        >
          <svg style={{ width: '16px', height: '16px' }} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
};

