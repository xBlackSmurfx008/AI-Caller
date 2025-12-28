import React from 'react';
import { cn } from '../../utils/helpers';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  actions?: React.ReactNode;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  title,
  actions,
  onClick,
}) => {
  return (
    <div
      className={cn(
        'chatkit-card',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
      style={onClick ? { cursor: 'pointer' } : undefined}
    >
      {(title || actions) && (
        <div 
          className="flex items-center justify-between"
          style={{
            padding: 'var(--ai-spacing-6) var(--ai-spacing-12)',
            borderBottom: '0.5px solid var(--ai-color-border-heavy)',
            background: 'var(--ai-color-bg-tertiary)',
            borderRadius: 'var(--ai-radius-xl) var(--ai-radius-xl) 0 0',
          }}
        >
          {title && (
            <h3 
              style={{
                fontSize: 'var(--ai-font-size-body-emph)',
                fontWeight: 'var(--ai-font-weight-body-emph)',
                lineHeight: 'var(--ai-line-height-body-emph)',
                letterSpacing: 'var(--ai-letter-spacing-body-emph)',
                color: 'var(--ai-color-text-primary)',
                margin: 0,
              }}
            >
              {title}
            </h3>
          )}
          {actions && <div className="flex items-center" style={{ gap: 'var(--ai-spacing-4)' }}>{actions}</div>}
        </div>
      )}
      <div 
        className={cn(!title && !actions && 'rounded-lg')}
        style={{ padding: 'var(--ai-spacing-12)' }}
      >
        {children}
      </div>
    </div>
  );
};
