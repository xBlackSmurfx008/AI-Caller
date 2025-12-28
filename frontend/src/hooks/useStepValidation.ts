import { useCallback } from 'react';
import { FieldErrors, UseFormReturn } from 'react-hook-form';

export interface StepValidationRule {
  fields: string[];
  validate: (values: any) => boolean | string;
}

export const useStepValidation = <T extends Record<string, any>>(
  form: UseFormReturn<T>
) => {
  const validateStep = useCallback(
    (stepFields: string[]): { isValid: boolean; errors: string[] } => {
      const errors: string[] = [];
      
      // Trigger validation for specific fields
      form.trigger(stepFields as any);
      
      // Get current form errors
      const formErrors = form.formState.errors;
      
      // Check each field in the step
      stepFields.forEach((field) => {
        const error = getNestedError(formErrors, field);
        if (error) {
          errors.push(error);
        }
      });
      
      return {
        isValid: errors.length === 0,
        errors,
      };
    },
    [form]
  );

  const scrollToFirstError = useCallback(() => {
    const firstErrorField = Object.keys(form.formState.errors)[0];
    if (firstErrorField) {
      const element = document.querySelector(
        `[name="${firstErrorField}"], [id="${firstErrorField}"]`
      );
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        (element as HTMLElement).focus();
      }
    }
  }, [form.formState.errors]);

  return {
    validateStep,
    scrollToFirstError,
  };
};

// Helper to get nested error from react-hook-form errors
function getNestedError(
  errors: FieldErrors<any>,
  fieldPath: string
): string | undefined {
  const parts = fieldPath.split('.');
  let current: any = errors;
  
  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = current[part];
    } else {
      return undefined;
    }
  }
  
  if (current && typeof current === 'object' && 'message' in current) {
    return current.message as string;
  }
  
  return undefined;
}

