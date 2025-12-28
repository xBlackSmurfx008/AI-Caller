import { useState, useCallback } from 'react';

export interface ConfirmationOptions {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  confirmButtonVariant?: 'primary' | 'danger' | 'secondary';
  onConfirm?: () => void | Promise<void>;
}

export interface ConfirmationState extends ConfirmationOptions {
  isOpen: boolean;
}

export const useConfirmation = () => {
  const [state, setState] = useState<ConfirmationState>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: undefined,
  });

  const confirm = useCallback(
    (options: ConfirmationOptions): Promise<boolean> => {
      return new Promise((resolve) => {
        setState({
          isOpen: true,
          title: options.title,
          message: options.message,
          confirmLabel: options.confirmLabel,
          cancelLabel: options.cancelLabel,
          variant: options.variant,
          confirmButtonVariant: options.confirmButtonVariant,
          onConfirm: async () => {
            try {
              if (options.onConfirm) {
                await options.onConfirm();
              }
              resolve(true);
            } catch (error) {
              resolve(false);
              throw error;
            } finally {
              setState((prev) => ({ ...prev, isOpen: false, onConfirm: undefined }));
            }
          },
        });
      });
    },
    []
  );

  const close = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: false, onConfirm: undefined }));
  }, []);

  const handleConfirm = useCallback(async () => {
    if (state.onConfirm) {
      await state.onConfirm();
    }
  }, [state.onConfirm]);

  return {
    confirm,
    close,
    handleConfirm,
    isOpen: state.isOpen,
    title: state.title,
    message: state.message,
    confirmLabel: state.confirmLabel,
    cancelLabel: state.cancelLabel,
    variant: state.variant,
    confirmButtonVariant: state.confirmButtonVariant,
  };
};

