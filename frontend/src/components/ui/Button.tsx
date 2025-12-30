import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-semibold transition-all',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          {
            // Primary - Purple gradient with white text
            'bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-500 hover:to-indigo-500 focus:ring-purple-500 shadow-lg shadow-purple-500/25':
              variant === 'primary',
            // Secondary - Slate background with white text
            'bg-slate-700 text-white hover:bg-slate-600 focus:ring-slate-500 border border-slate-600':
              variant === 'secondary',
            // Outline - Transparent with visible border and text
            'border-2 border-slate-500 bg-transparent text-white hover:bg-slate-800 hover:border-slate-400 focus:ring-slate-500':
              variant === 'outline',
            // Ghost - Transparent with visible text on hover
            'text-slate-200 hover:bg-slate-800 hover:text-white focus:ring-slate-500':
              variant === 'ghost',
            // Danger - Red with white text
            'bg-red-600 text-white hover:bg-red-500 focus:ring-red-500 shadow-lg shadow-red-500/25':
              variant === 'danger',
            'px-3 py-1.5 text-sm': size === 'sm',
            'px-4 py-2 text-base': size === 'md',
            'px-6 py-3 text-lg': size === 'lg',
          },
          className
        )}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

