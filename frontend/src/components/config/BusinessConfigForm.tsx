import React, { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { ConfirmationModal } from '../common/ConfirmationModal';
import { useUnsavedChanges } from '../../hooks/useUnsavedChanges';
import type { BusinessConfig, BusinessConfigData } from '../../types/config';
import { configAPI } from '../../api/config';
import toast from 'react-hot-toast';

// Validation schema
const businessConfigSchema = z.object({
  name: z.string().min(1, 'Business name is required').max(100, 'Name must be less than 100 characters'),
  type: z.enum(['customer_support', 'sales', 'appointments'], {
    errorMap: () => ({ message: 'Please select a business type' }),
  }),
  is_active: z.boolean().default(true),
  config_data: z.object({
    ai: z.object({
      model: z.string().min(1, 'AI model is required'),
      temperature: z.number().min(0).max(2).default(0.7),
      system_prompt: z.string().min(10, 'System prompt must be at least 10 characters'),
    }),
    voice: z.object({
      language: z.string().min(1, 'Language is required'),
      voice: z.string().min(1, 'Voice is required'),
      response_delay: z.number().min(0).max(5000).default(500),
    }),
    knowledge_base: z.object({
      enabled: z.boolean().default(false),
      retrieval_top_k: z.number().min(1).max(20).default(5),
      similarity_threshold: z.number().min(0).max(1).default(0.7),
    }),
    quality_assurance: z.object({
      enabled: z.boolean().default(true),
      sentiment_analysis: z.boolean().default(true),
      compliance_check: z.boolean().default(true),
      min_score_threshold: z.number().min(0).max(100).default(70),
    }),
    escalation: z.object({
      enabled: z.boolean().default(true),
      warm_transfer: z.boolean().default(true),
      triggers: z.array(
        z.object({
          type: z.enum(['sentiment', 'keyword', 'complexity']),
          threshold: z.number().optional(),
          keywords: z.array(z.string()).optional(),
        })
      ).default([]),
    }),
  }),
});

type BusinessConfigFormData = z.infer<typeof businessConfigSchema>;

interface BusinessConfigFormProps {
  isOpen: boolean;
  onClose: () => void;
  editingConfig?: BusinessConfig | null;
  onSuccess?: () => void;
}

const AI_MODELS = [
  { value: 'gpt-4o', label: 'GPT-4o (Recommended)' },
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
];

const VOICES = [
  { value: 'alloy', label: 'Alloy' },
  { value: 'echo', label: 'Echo' },
  { value: 'fable', label: 'Fable' },
  { value: 'onyx', label: 'Onyx' },
  { value: 'nova', label: 'Nova' },
  { value: 'shimmer', label: 'Shimmer' },
];

const LANGUAGES = [
  { value: 'en-US', label: 'English (US)' },
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'es-ES', label: 'Spanish (Spain)' },
  { value: 'es-MX', label: 'Spanish (Mexico)' },
  { value: 'fr-FR', label: 'French' },
  { value: 'de-DE', label: 'German' },
  { value: 'it-IT', label: 'Italian' },
  { value: 'pt-BR', label: 'Portuguese (Brazil)' },
  { value: 'ja-JP', label: 'Japanese' },
  { value: 'ko-KR', label: 'Korean' },
  { value: 'zh-CN', label: 'Chinese (Simplified)' },
];

export const BusinessConfigForm: React.FC<BusinessConfigFormProps> = ({
  isOpen,
  onClose,
  editingConfig,
  onSuccess,
}) => {
  const [activeStep, setActiveStep] = useState(1);
  const [showCloseConfirm, setShowCloseConfirm] = useState(false);
  const totalSteps = 6;

  const form = useForm<BusinessConfigFormData>({
    resolver: zodResolver(businessConfigSchema),
    defaultValues: {
      name: '',
      type: 'customer_support',
      is_active: true,
      config_data: {
        ai: {
          model: 'gpt-4o',
          temperature: 0.7,
          system_prompt: 'You are a helpful AI assistant for customer service. Be professional, empathetic, and solution-oriented.',
        },
        voice: {
          language: 'en-US',
          voice: 'alloy',
          response_delay: 500,
        },
        knowledge_base: {
          enabled: false,
          retrieval_top_k: 5,
          similarity_threshold: 0.7,
        },
        quality_assurance: {
          enabled: true,
          sentiment_analysis: true,
          compliance_check: true,
          min_score_threshold: 70,
        },
        escalation: {
          enabled: true,
          warm_transfer: true,
          triggers: [],
        },
      },
    },
  });

  const {
    register,
    handleSubmit,
    control,
    watch,
    reset,
    setValue,
    trigger,
    formState: { errors, isSubmitting },
  } = form;

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'config_data.escalation.triggers',
  });

  const watchedValues = watch();

  // Step validation
  const stepFields = {
    1: ['name', 'type'],
    2: ['config_data.ai.model', 'config_data.ai.system_prompt'],
    3: ['config_data.voice.language', 'config_data.voice.voice'],
    4: ['config_data.knowledge_base.retrieval_top_k', 'config_data.knowledge_base.similarity_threshold'],
    5: ['config_data.quality_assurance.min_score_threshold'],
    6: ['config_data.escalation.triggers'],
  };

  // Step validation helper
  const validateStepFields = async (fields: string[]): Promise<boolean> => {
    const result = await trigger(fields as any);
    if (!result) {
      // Scroll to first error
      const firstErrorField = Object.keys(errors)[0];
      if (firstErrorField) {
        const element = document.querySelector(
          `[name="${firstErrorField}"], [id="${firstErrorField}"]`
        );
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          (element as HTMLElement).focus();
        }
      }
    }
    return result;
  };

  // Track unsaved changes
  const formValues = watch();
  const defaultValues = form.formState.defaultValues;
  const hasUnsavedChanges = JSON.stringify(formValues) !== JSON.stringify(defaultValues);
  useUnsavedChanges({
    hasUnsavedChanges: hasUnsavedChanges && isOpen,
    message: 'You have unsaved changes. Are you sure you want to leave?',
  });

  // Load editing config data
  useEffect(() => {
    if (editingConfig && isOpen) {
      reset({
        name: editingConfig.name,
        type: editingConfig.type as 'customer_support' | 'sales' | 'appointments',
        is_active: editingConfig.is_active,
        config_data: editingConfig.config_data,
      });
    } else if (!editingConfig && isOpen) {
      reset({
        name: '',
        type: 'customer_support',
        is_active: true,
        config_data: {
          ai: {
            model: 'gpt-4o',
            temperature: 0.7,
            system_prompt: 'You are a helpful AI assistant for customer service. Be professional, empathetic, and solution-oriented.',
          },
          voice: {
            language: 'en-US',
            voice: 'alloy',
            response_delay: 500,
          },
          knowledge_base: {
            enabled: false,
            retrieval_top_k: 5,
            similarity_threshold: 0.7,
          },
          quality_assurance: {
            enabled: true,
            sentiment_analysis: true,
            compliance_check: true,
            min_score_threshold: 70,
          },
          escalation: {
            enabled: true,
            warm_transfer: true,
            triggers: [],
          },
        },
      });
    }
  }, [editingConfig, isOpen, reset]);

  const onSubmit = async (data: BusinessConfigFormData) => {
    try {
      if (editingConfig) {
        await configAPI.updateBusinessConfig(editingConfig.id, data);
        toast.success('Configuration updated successfully');
      } else {
        await configAPI.createBusinessConfig(data);
        toast.success('Configuration created successfully');
      }
      onSuccess?.();
      onClose();
      reset();
      setActiveStep(1);
    } catch (error: any) {
      toast.error(error?.response?.data?.error?.message || 'Failed to save configuration');
    }
  };

  const handleClose = () => {
    if (hasUnsavedChanges) {
      setShowCloseConfirm(true);
      return;
    }
    reset();
    setActiveStep(1);
    onClose();
  };

  const handleCloseConfirm = () => {
    reset();
    setActiveStep(1);
    setShowCloseConfirm(false);
    onClose();
  };

  const handleNext = async () => {
    const currentStepFields = stepFields[activeStep as keyof typeof stepFields] || [];
    const isValid = await validateStepFields(currentStepFields);
    
    if (!isValid) {
      toast.error('Please fix the errors before proceeding');
      return;
    }
    
    setActiveStep(activeStep + 1);
  };

  const handlePrevious = () => {
    setActiveStep(activeStep - 1);
  };

  const addEscalationTrigger = () => {
    append({
      type: 'sentiment',
      threshold: 0.5,
      keywords: [],
    });
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 1: // Basic Information
        return (
          <div className="space-y-4">
            <div>
              <h3 style={{ fontSize: 'var(--ai-font-size-h3)', fontWeight: 'var(--ai-font-weight-semibold)', marginBottom: 'var(--ai-spacing-4)' }}>
                Basic Information
              </h3>
              <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)', marginBottom: 'var(--ai-spacing-6)' }}>
                Set up the basic details for your business configuration.
              </p>
            </div>
            <Input
              label="Business Name"
              {...register('name')}
              error={errors.name?.message}
              placeholder="e.g., Customer Support - Main Line"
            />
            <Select
              label="Business Type"
              options={[
                { value: 'customer_support', label: 'Customer Support' },
                { value: 'sales', label: 'Sales' },
                { value: 'appointments', label: 'Appointments' },
              ]}
              {...register('type')}
              error={errors.type?.message}
            />
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                {...register('is_active')}
                className="w-4 h-4"
              />
              <label htmlFor="is_active" style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-primary)' }}>
                Active (this configuration will be available for use)
              </label>
            </div>
          </div>
        );

      case 2: // AI Configuration
        return (
          <div className="space-y-4">
            <div>
              <h3 style={{ fontSize: 'var(--ai-font-size-h3)', fontWeight: 'var(--ai-font-weight-semibold)', marginBottom: 'var(--ai-spacing-4)' }}>
                AI Configuration
              </h3>
              <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)', marginBottom: 'var(--ai-spacing-6)' }}>
                Configure the AI model and behavior for your calls.
              </p>
            </div>
            <Select
              label="AI Model"
              options={AI_MODELS}
              {...register('config_data.ai.model')}
              error={errors.config_data?.ai?.model?.message}
            />
            <Input
              label="Temperature"
              type="number"
              step="0.1"
              min="0"
              max="2"
              {...register('config_data.ai.temperature', { valueAsNumber: true })}
              error={errors.config_data?.ai?.temperature?.message}
              placeholder="0.7"
            />
            <div>
              <p style={{ fontSize: 'var(--ai-font-size-body-small)', marginBottom: '4px' }}>
                Lower values = more focused, higher values = more creative
              </p>
            </div>
            <Input
              label="System Prompt"
              multiline
              rows={6}
              {...register('config_data.ai.system_prompt')}
              error={errors.config_data?.ai?.system_prompt?.message}
              placeholder="Define how the AI should behave during calls..."
            />
          </div>
        );

      case 3: // Voice Configuration
        return (
          <div className="space-y-4">
            <div>
              <h3 style={{ fontSize: 'var(--ai-font-size-h3)', fontWeight: 'var(--ai-font-weight-semibold)', marginBottom: 'var(--ai-spacing-4)' }}>
                Voice Configuration
              </h3>
              <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)', marginBottom: 'var(--ai-spacing-6)' }}>
                Configure the voice settings for AI responses.
              </p>
            </div>
            <Select
              label="Language"
              options={LANGUAGES}
              {...register('config_data.voice.language')}
              error={errors.config_data?.voice?.language?.message}
            />
            <Select
              label="Voice"
              options={VOICES}
              {...register('config_data.voice.voice')}
              error={errors.config_data?.voice?.voice?.message}
            />
            <Input
              label="Response Delay (ms)"
              type="number"
              min="0"
              max="5000"
              step="100"
              {...register('config_data.voice.response_delay', { valueAsNumber: true })}
              error={errors.config_data?.voice?.response_delay?.message}
              placeholder="500"
            />
            <div>
              <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)' }}>
                Delay before AI responds (in milliseconds). Lower values = faster responses.
              </p>
            </div>
          </div>
        );

      case 4: // Knowledge Base
        return (
          <div className="space-y-4">
            <div>
              <h3 style={{ fontSize: 'var(--ai-font-size-h3)', fontWeight: 'var(--ai-font-weight-semibold)', marginBottom: 'var(--ai-spacing-4)' }}>
                Knowledge Base Configuration
              </h3>
              <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)', marginBottom: 'var(--ai-spacing-6)' }}>
                Enable AI to access your knowledge base for more accurate responses.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="kb_enabled"
                {...register('config_data.knowledge_base.enabled')}
                className="w-4 h-4"
              />
              <label htmlFor="kb_enabled" style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-primary)' }}>
                Enable Knowledge Base
              </label>
            </div>
            {watchedValues.config_data?.knowledge_base?.enabled && (
              <>
                <Input
                  label="Retrieval Top K"
                  type="number"
                  min="1"
                  max="20"
                  {...register('config_data.knowledge_base.retrieval_top_k', { valueAsNumber: true })}
                  error={errors.config_data?.knowledge_base?.retrieval_top_k?.message}
                  placeholder="5"
                />
                <div>
                  <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)' }}>
                    Number of knowledge base entries to retrieve per query
                  </p>
                </div>
                <Input
                  label="Similarity Threshold"
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  {...register('config_data.knowledge_base.similarity_threshold', { valueAsNumber: true })}
                  error={errors.config_data?.knowledge_base?.similarity_threshold?.message}
                  placeholder="0.7"
                />
                <div>
                  <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)' }}>
                    Minimum similarity score (0-1) for knowledge base entries to be used
                  </p>
                </div>
              </>
            )}
          </div>
        );

      case 5: // Quality Assurance
        return (
          <div className="space-y-4">
            <div>
              <h3 style={{ fontSize: 'var(--ai-font-size-h3)', fontWeight: 'var(--ai-font-weight-semibold)', marginBottom: 'var(--ai-spacing-4)' }}>
                Quality Assurance Configuration
              </h3>
              <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)', marginBottom: 'var(--ai-spacing-6)' }}>
                Configure quality monitoring and compliance checks.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="qa_enabled"
                {...register('config_data.quality_assurance.enabled')}
                className="w-4 h-4"
              />
              <label htmlFor="qa_enabled" style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-primary)' }}>
                Enable Quality Assurance
              </label>
            </div>
            {watchedValues.config_data?.quality_assurance?.enabled && (
              <>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="sentiment_analysis"
                    {...register('config_data.quality_assurance.sentiment_analysis')}
                    className="w-4 h-4"
                  />
                  <label htmlFor="sentiment_analysis" style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-primary)' }}>
                    Enable Sentiment Analysis
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="compliance_check"
                    {...register('config_data.quality_assurance.compliance_check')}
                    className="w-4 h-4"
                  />
                  <label htmlFor="compliance_check" style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-primary)' }}>
                    Enable Compliance Check
                  </label>
                </div>
                <Input
                  label="Minimum QA Score Threshold"
                  type="number"
                  min="0"
                  max="100"
                  {...register('config_data.quality_assurance.min_score_threshold', { valueAsNumber: true })}
                  error={errors.config_data?.quality_assurance?.min_score_threshold?.message}
                  placeholder="70"
                />
                <div>
                  <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)' }}>
                    Minimum score (0-100) for calls to pass QA review
                  </p>
                </div>
              </>
            )}
          </div>
        );

      case 6: // Escalation
        return (
          <div className="space-y-4">
            <div>
              <h3 style={{ fontSize: 'var(--ai-font-size-h3)', fontWeight: 'var(--ai-font-weight-semibold)', marginBottom: 'var(--ai-spacing-4)' }}>
                Escalation Configuration
              </h3>
              <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)', marginBottom: 'var(--ai-spacing-6)' }}>
                Configure when and how calls should be escalated to human agents.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="escalation_enabled"
                {...register('config_data.escalation.enabled')}
                className="w-4 h-4"
              />
              <label htmlFor="escalation_enabled" style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-primary)' }}>
                Enable Escalation
              </label>
            </div>
            {watchedValues.config_data?.escalation?.enabled && (
              <>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="warm_transfer"
                    {...register('config_data.escalation.warm_transfer')}
                    className="w-4 h-4"
                  />
                  <label htmlFor="warm_transfer" style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-primary)' }}>
                    Warm Transfer (agent receives call context)
                  </label>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 style={{ fontSize: 'var(--ai-font-size-body-emph)', fontWeight: 'var(--ai-font-weight-semibold)' }}>
                      Escalation Triggers
                    </h4>
                    <Button variant="secondary" size="sm" type="button" onClick={addEscalationTrigger}>
                      + Add Trigger
                    </Button>
                  </div>
                  {fields.length === 0 && (
                    <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)', fontStyle: 'italic' }}>
                      No triggers configured. Add triggers to automatically escalate calls based on conditions.
                    </p>
                  )}
                  {fields.map((field, index) => (
                    <div key={field.id} style={{ padding: 'var(--ai-spacing-4)', border: '0.5px solid var(--ai-color-border-default)', borderRadius: 'var(--ai-radius-md)' }}>
                      <div className="flex items-start justify-between mb-3">
                        <h5 style={{ fontSize: 'var(--ai-font-size-body-small)', fontWeight: 'var(--ai-font-weight-medium)' }}>
                          Trigger {index + 1}
                        </h5>
                        <Button
                          variant="ghost"
                          size="sm"
                          type="button"
                          onClick={() => remove(index)}
                        >
                          Remove
                        </Button>
                      </div>
                      <div className="space-y-3">
                        <Select
                          label="Trigger Type"
                          options={[
                            { value: 'sentiment', label: 'Sentiment (negative sentiment threshold)' },
                            { value: 'keyword', label: 'Keyword (specific keywords detected)' },
                            { value: 'complexity', label: 'Complexity (call complexity score)' },
                          ]}
                          {...register(`config_data.escalation.triggers.${index}.type`)}
                        />
                        {watchedValues.config_data?.escalation?.triggers?.[index]?.type === 'sentiment' && (
                          <Input
                            label="Sentiment Threshold"
                            type="number"
                            step="0.1"
                            min="0"
                            max="1"
                            {...register(`config_data.escalation.triggers.${index}.threshold`, { valueAsNumber: true })}
                            placeholder="0.5"
                          />
                        )}
                        {watchedValues.config_data?.escalation?.triggers?.[index]?.type === 'keyword' && (
                          <Input
                            label="Keywords (comma-separated)"
                            defaultValue={watchedValues.config_data?.escalation?.triggers?.[index]?.keywords?.join(', ') || ''}
                            placeholder="urgent, complaint, cancel"
                            onChange={(e) => {
                              const keywords = e.target.value.split(',').map(k => k.trim()).filter(k => k);
                              setValue(`config_data.escalation.triggers.${index}.keywords` as any, keywords);
                            }}
                          />
                        )}
                        {watchedValues.config_data?.escalation?.triggers?.[index]?.type === 'complexity' && (
                          <Input
                            label="Complexity Threshold"
                            type="number"
                            min="0"
                            max="100"
                            {...register(`config_data.escalation.triggers.${index}.threshold`, { valueAsNumber: true })}
                            placeholder="75"
                          />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={editingConfig ? 'Edit Business Configuration' : 'Create Business Configuration'}
      size="lg"
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Step Indicator */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
              <React.Fragment key={step}>
                <div className="flex items-center">
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--ai-radius-full)',
                      backgroundColor: activeStep >= step ? 'var(--ai-color-brand-primary)' : 'var(--ai-color-bg-secondary)',
                      color: activeStep >= step ? 'var(--ai-color-brand-on-primary)' : 'var(--ai-color-text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 'var(--ai-font-size-body-small)',
                      fontWeight: 'var(--ai-font-weight-semibold)',
                    }}
                  >
                    {step}
                  </div>
                  {step < totalSteps && (
                    <div
                      style={{
                        width: '60px',
                        height: '2px',
                        backgroundColor: activeStep > step ? 'var(--ai-color-brand-primary)' : 'var(--ai-color-border-default)',
                        margin: '0 8px',
                      }}
                    />
                  )}
                </div>
              </React.Fragment>
            ))}
          </div>
          <div className="text-center">
            <p style={{ fontSize: 'var(--ai-font-size-body-small)', color: 'var(--ai-color-text-secondary)' }}>
              Step {activeStep} of {totalSteps}
            </p>
          </div>
        </div>

        {/* Step Content */}
        <div style={{ minHeight: '400px', marginBottom: 'var(--ai-spacing-8)' }}>
          {renderStepContent()}
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between pt-4" style={{ borderTop: '0.5px solid var(--ai-color-border-heavy)' }}>
          <div>
            {activeStep > 1 && (
              <Button
                type="button"
                variant="ghost"
                onClick={handlePrevious}
              >
                ← Previous
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={handleClose}
            >
              Cancel
            </Button>
            {activeStep < totalSteps ? (
              <Button
                type="button"
                variant="primary"
                onClick={handleNext}
              >
                Next →
              </Button>
            ) : (
              <Button
                type="submit"
                variant="primary"
                isLoading={isSubmitting}
              >
                {editingConfig ? 'Update Configuration' : 'Create Configuration'}
              </Button>
            )}
          </div>
        </div>
      </form>

      {/* Close Confirmation Modal */}
      <ConfirmationModal
        isOpen={showCloseConfirm}
        onClose={() => setShowCloseConfirm(false)}
        onConfirm={handleCloseConfirm}
        title="Unsaved Changes"
        message="You have unsaved changes. Are you sure you want to close? All changes will be lost."
        confirmLabel="Close"
        cancelLabel="Cancel"
        variant="warning"
      />
    </Modal>
  );
};

