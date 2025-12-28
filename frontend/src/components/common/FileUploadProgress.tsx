import React from 'react';
import { LoadingSpinner } from './LoadingSpinner';

export interface FileUploadProgressProps {
  fileName: string;
  progress: number; // 0-100
  status?: 'uploading' | 'processing' | 'completed' | 'error';
  errorMessage?: string;
  onCancel?: () => void;
}

export const FileUploadProgress: React.FC<FileUploadProgressProps> = ({
  fileName,
  progress,
  status = 'uploading',
  errorMessage,
  onCancel,
}) => {
  const getStatusText = () => {
    switch (status) {
      case 'uploading':
        return 'Uploading...';
      case 'processing':
        return 'Processing document...';
      case 'completed':
        return 'Completed';
      case 'error':
        return 'Error';
      default:
        return '';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return 'var(--ai-color-brand-primary)';
      case 'completed':
        return 'var(--ai-color-brand-success)';
      case 'error':
        return 'var(--ai-color-brand-error)';
      default:
        return 'var(--ai-color-border-default)';
    }
  };

  return (
    <div
      style={{
        padding: 'var(--ai-spacing-6)',
        border: '1.5px solid var(--ai-color-border-heavy)',
        borderRadius: 'var(--ai-radius-md)',
        backgroundColor: 'var(--ai-color-bg-primary)',
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex-1 min-w-0">
          <p
            style={{
              fontSize: 'var(--ai-font-size-body-small)',
              fontWeight: 'var(--ai-font-weight-medium)',
              color: 'var(--ai-color-text-primary)',
              marginBottom: 'var(--ai-spacing-2)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {fileName}
          </p>
          <p
            style={{
              fontSize: 'var(--ai-font-size-caption)',
              color: 'var(--ai-color-text-secondary)',
            }}
          >
            {getStatusText()}
          </p>
        </div>
        {status === 'uploading' && onCancel && (
          <button
            onClick={onCancel}
            style={{
              padding: 'var(--ai-spacing-2) var(--ai-spacing-4)',
              fontSize: 'var(--ai-font-size-body-small)',
              color: 'var(--ai-color-text-secondary)',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              borderRadius: 'var(--ai-radius-base)',
            }}
          >
            Cancel
          </button>
        )}
        {status === 'processing' && (
          <LoadingSpinner size="sm" />
        )}
      </div>

      {/* Progress Bar */}
      {status !== 'completed' && status !== 'error' && (
        <div
          style={{
            width: '100%',
            height: '4px',
            backgroundColor: 'var(--ai-color-bg-secondary)',
            borderRadius: 'var(--ai-radius-full)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${progress}%`,
              height: '100%',
              backgroundColor: getStatusColor(),
              borderRadius: 'var(--ai-radius-full)',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      )}

      {/* Error Message */}
      {status === 'error' && errorMessage && (
        <div
          style={{
            marginTop: 'var(--ai-spacing-4)',
            padding: 'var(--ai-spacing-4)',
            backgroundColor: 'var(--ai-color-bg-danger)',
            border: '1.5px solid var(--ai-color-brand-error)',
            borderRadius: 'var(--ai-radius-base)',
          }}
        >
          <p
            style={{
              fontSize: 'var(--ai-font-size-body-small)',
              color: 'var(--ai-color-brand-error)',
              margin: 0,
            }}
          >
            {errorMessage}
          </p>
        </div>
      )}

      {/* Success Indicator */}
      {status === 'completed' && (
        <div
          style={{
            marginTop: 'var(--ai-spacing-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ai-spacing-2)',
            color: 'var(--ai-color-brand-success)',
            fontSize: 'var(--ai-font-size-body-small)',
          }}
        >
          <span>✓</span>
          <span>File uploaded and processed successfully</span>
        </div>
      )}
    </div>
  );
};

