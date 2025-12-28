import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { createPortal } from 'react-dom';
import { cn } from '../../utils/helpers';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'large';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}) => {
  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    large: 'max-w-5xl',
  };

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <Transition show={isOpen} as={Fragment}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div 
            className="fixed inset-0 bg-black/20" 
            aria-hidden="true"
            onClick={onClose}
            style={{ zIndex: 9998 }}
          />
        </Transition.Child>

        <div className="fixed inset-0 flex items-center justify-center p-4" style={{ zIndex: 9999, pointerEvents: 'none' }}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-200"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-150"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <Dialog.Panel 
              className={cn('w-full chatkit-surface', sizes[size])}
              style={{ 
                boxShadow: 'var(--ai-elevation-3-shadow)',
                pointerEvents: 'auto',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {title && (
                <div 
                  className="px-5 py-3.5"
                  style={{ 
                    borderBottom: '0.5px solid var(--ai-color-border-heavy)',
                  }}
                >
                  <Dialog.Title 
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
                  </Dialog.Title>
                </div>
              )}
              <div 
                style={{ 
                  padding: 'var(--ai-spacing-8) var(--ai-spacing-12)',
                  maxHeight: 'calc(100vh - 200px)',
                  overflowY: 'auto',
                }}
              >
                {children}
              </div>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Transition>
    </Dialog>
  );
};

