import { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export interface UseUnsavedChangesOptions {
  hasUnsavedChanges: boolean;
  message?: string;
  onBeforeUnload?: (event: BeforeUnloadEvent) => void;
}

export const useUnsavedChanges = ({
  hasUnsavedChanges,
  message = 'You have unsaved changes. Are you sure you want to leave?',
  onBeforeUnload,
}: UseUnsavedChangesOptions) => {
  const navigate = useNavigate();
  const location = useLocation();
  const hasUnsavedChangesRef = useRef(hasUnsavedChanges);

  useEffect(() => {
    hasUnsavedChangesRef.current = hasUnsavedChanges;
  }, [hasUnsavedChanges]);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (hasUnsavedChangesRef.current) {
        if (onBeforeUnload) {
          onBeforeUnload(event);
        } else {
          event.preventDefault();
          event.returnValue = message;
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [message, onBeforeUnload]);

  const handleNavigation = (targetPath: string, onConfirm?: () => void) => {
    if (hasUnsavedChangesRef.current) {
      // This will be handled by the component using a confirmation modal
      return false;
    }
    if (onConfirm) {
      onConfirm();
    } else {
      navigate(targetPath);
    }
    return true;
  };

  return {
    hasUnsavedChanges,
    handleNavigation,
  };
};

