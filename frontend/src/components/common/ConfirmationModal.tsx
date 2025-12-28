import React from 'react';
import { Modal } from './Modal';
import { Button } from './Button';

export interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  isLoading?: boolean;
  confirmButtonVariant?: 'primary' | 'danger' | 'secondary';
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'info',
  isLoading = false,
  confirmButtonVariant,
}) => {
  const handleConfirm = async () => {
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      // Error handling is done by the caller via toast
      console.error('Confirmation action failed:', error);
    }
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return {
          iconBg: 'var(--ai-color-brand-error)',
          iconColor: '#ffffff',
          messageBg: 'var(--ai-color-bg-danger)',
          messageBorder: 'var(--ai-color-brand-error)',
        };
      case 'warning':
        return {
          iconBg: 'var(--ai-color-brand-warning)',
          iconColor: '#ffffff',
          messageBg: 'var(--ai-color-bg-warning)',
          messageBorder: 'var(--ai-color-brand-warning)',
        };
      default:
        return {
          iconBg: 'var(--ai-color-brand-primary)',
          iconColor: '#ffffff',
          messageBg: 'var(--ai-color-bg-tertiary)',
          messageBorder: 'var(--ai-color-border-heavy)',
        };
    }
  };

  const styles = getVariantStyles();
  const buttonVariant = confirmButtonVariant || (variant === 'danger' ? 'danger' : 'primary');

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <div className="space-y-4">
        {/* Icon and Message */}
        <div
          style={{
            padding: 'var(--ai-spacing-6)',
            backgroundColor: styles.messageBg,
            border: `1.5px solid ${styles.messageBorder}`,
            borderRadius: 'var(--ai-radius-md)',
          }}
        >
          <div className="flex items-start gap-3">
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--ai-radius-full)',
                backgroundColor: styles.iconBg,
                color: styles.iconColor,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                fontSize: '18px',
              }}
            >
              {variant === 'danger' ? '⚠️' : variant === 'warning' ? '⚠️' : 'ℹ️'}
            </div>
            <p
              style={{
                fontSize: 'var(--ai-font-size-body-small)',
                lineHeight: 'var(--ai-line-height-body-small)',
                color: 'var(--ai-color-text-primary)',
                margin: 0,
                flex: 1,
              }}
            >
              {message}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-2 pt-2">
          <Button
            variant="ghost"
            onClick={onClose}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={buttonVariant}
            onClick={handleConfirm}
            isLoading={isLoading}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

