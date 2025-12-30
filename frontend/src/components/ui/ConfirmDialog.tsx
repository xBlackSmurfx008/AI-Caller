import { Card, CardContent, CardHeader, CardTitle } from './Card';
import { Button } from './Button';
import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  isLoading?: boolean;
}

export const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  isLoading = false,
}: ConfirmDialogProps) => {
  if (!isOpen) return null;

  const variantClasses = {
    danger: 'text-red-400',
    warning: 'text-amber-400',
    info: 'text-blue-400',
  };

  const buttonVariants = {
    danger: 'bg-red-600 hover:bg-red-700',
    warning: 'bg-amber-600 hover:bg-amber-700',
    info: 'bg-blue-600 hover:bg-blue-700',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="bg-slate-900 border-slate-700 max-w-md w-full mx-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className={cn('w-5 h-5', variantClasses[variant])} />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-300 mb-6">{message}</p>
          <div className="flex gap-3 justify-end">
            <Button
              variant="secondary"
              onClick={onClose}
              disabled={isLoading}
            >
              {cancelText}
            </Button>
            <Button
              onClick={onConfirm}
              disabled={isLoading}
              className={cn(buttonVariants[variant], 'text-white')}
            >
              {confirmText}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

