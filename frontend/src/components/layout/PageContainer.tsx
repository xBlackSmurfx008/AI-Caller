import React from 'react';
import { cn } from '../../utils/helpers';

interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  children,
  className,
}) => {
  return (
    <div 
      className={cn('min-h-screen', className)}
      style={{
        backgroundColor: 'var(--ai-color-bg-primary)',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {children}
    </div>
  );
};
