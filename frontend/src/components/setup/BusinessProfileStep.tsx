import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Button } from '../common/Button';

const businessProfileSchema = z.object({
  name: z.string().min(1, 'Business name is required'),
  type: z.enum(['customer_support', 'sales', 'appointments', 'custom']),
  ai_model: z.string().default('gpt-4o'),
  temperature: z.number().min(0).max(1).default(0.7),
  system_prompt: z.string().min(1, 'System prompt is required'),
  voice: z.string().default('alloy'),
  language: z.string().default('en-US'),
});

type BusinessProfileData = z.infer<typeof businessProfileSchema>;

interface BusinessProfileStepProps {
  formData: any;
  onNext: (data: any) => void;
  onBack: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export const BusinessProfileStep: React.FC<BusinessProfileStepProps> = ({
  formData,
  onNext,
  onBack,
  isFirstStep,
}) => {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<BusinessProfileData>({
    resolver: zodResolver(businessProfileSchema),
    defaultValues: {
      ...businessProfileSchema.parse({}),
      ...formData.businessProfile,
    },
  });

  const temperature = watch('temperature');

  const onSubmit = (data: BusinessProfileData) => {
    onNext({ businessProfile: data });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Business Profile</h2>
        <p className="text-gray-600">
          Set up your business profile and AI configuration
        </p>
      </div>

      <div className="space-y-4">
        <Input
          label="Business Name"
          {...register('name')}
          error={errors.name?.message}
          placeholder="Acme Corporation"
        />

        <Select
          label="Business Type"
          options={[
            { value: 'customer_support', label: 'Customer Support' },
            { value: 'sales', label: 'Sales' },
            { value: 'appointments', label: 'Appointments' },
            { value: 'custom', label: 'Custom' },
          ]}
          {...register('type')}
          error={errors.type?.message}
        />

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="AI Model"
            options={[
              { value: 'gpt-4o', label: 'GPT-4o' },
              { value: 'gpt-4', label: 'GPT-4' },
              { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
            ]}
            {...register('ai_model')}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Temperature: {temperature}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              {...register('temperature', { valueAsNumber: true })}
              className="w-full"
            />
          </div>
        </div>

        <Input
          label="System Prompt"
          multiline
          rows={6}
          {...register('system_prompt')}
          error={errors.system_prompt?.message}
          placeholder="You are a helpful and professional customer service representative..."
        />

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Voice"
            options={[
              { value: 'alloy', label: 'Alloy' },
              { value: 'echo', label: 'Echo' },
              { value: 'fable', label: 'Fable' },
              { value: 'onyx', label: 'Onyx' },
              { value: 'nova', label: 'Nova' },
              { value: 'shimmer', label: 'Shimmer' },
            ]}
            {...register('voice')}
          />
          <Select
            label="Language"
            options={[
              { value: 'en-US', label: 'English (US)' },
              { value: 'en-GB', label: 'English (UK)' },
              { value: 'es-ES', label: 'Spanish' },
              { value: 'fr-FR', label: 'French' },
              { value: 'de-DE', label: 'German' },
            ]}
            {...register('language')}
          />
        </div>
      </div>

      <div className="flex justify-between pt-4">
        <div>
          {!isFirstStep && (
            <Button type="button" variant="ghost" onClick={onBack}>
              Back
            </Button>
          )}
        </div>
        <Button type="submit" variant="primary">
          Next
        </Button>
      </div>
    </form>
  );
};

