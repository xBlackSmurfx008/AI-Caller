import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { useConfigStore } from '../../store/configStore';
import { callsAPI } from '../../api/calls';
import { configAPI } from '../../api/config';
import toast from 'react-hot-toast';

const initiateCallSchema = z.object({
  to_number: z.string().min(1, 'Phone number is required').regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number format'),
  from_number: z.string().optional(),
  business_id: z.string().min(1, 'Business configuration is required'),
  template_id: z.string().optional(),
  agent_personality: z.string().optional(),
});

type InitiateCallFormData = z.infer<typeof initiateCallSchema>;

interface InitiateCallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const InitiateCallModal: React.FC<InitiateCallModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { businessConfigs } = useConfigStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [personalities, setPersonalities] = useState<Array<{
    name: string;
    display_name: string;
    traits: string[];
    skills: string[];
    voice_config: Record<string, any>;
  }>>([]);
  const [loadingPersonalities, setLoadingPersonalities] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<InitiateCallFormData>({
    resolver: zodResolver(initiateCallSchema),
    defaultValues: {
      to_number: '',
      from_number: '',
      business_id: '',
      template_id: '',
      agent_personality: '',
    },
  });

  // Load personalities when modal opens
  useEffect(() => {
    if (isOpen && personalities.length === 0) {
      setLoadingPersonalities(true);
      configAPI.listPersonalities()
        .then(setPersonalities)
        .catch((error) => {
          console.error('Failed to load personalities:', error);
          toast.error('Failed to load agent personalities');
        })
        .finally(() => setLoadingPersonalities(false));
    }
  }, [isOpen, personalities.length]);

  const onSubmit = async (data: InitiateCallFormData) => {
    setIsSubmitting(true);
    try {
      await callsAPI.initiate({
        to_number: data.to_number,
        from_number: data.from_number || undefined,
        business_id: data.business_id,
        template_id: data.template_id || undefined,
        agent_personality: data.agent_personality || undefined,
      });
      toast.success('Call initiated successfully');
      reset();
      onClose();
      onSuccess?.();
    } catch (error: any) {
      toast.error(error?.response?.data?.error?.message || 'Failed to initiate call');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const activeConfigs = businessConfigs.filter((config) => config.is_active);

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Initiate Outbound Call"
      size="md"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <p
            style={{
              fontSize: 'var(--ai-font-size-body-small)',
              color: 'var(--ai-color-text-secondary)',
              marginBottom: 'var(--ai-spacing-6)',
            }}
          >
            Start a new outbound call to a customer. The call will use the selected business configuration.
          </p>
        </div>

        <Input
          label="To Phone Number"
          {...register('to_number')}
          error={errors.to_number?.message}
          placeholder="+1234567890"
          type="tel"
        />
        <div>
          <p
            style={{
              fontSize: 'var(--ai-font-size-caption)',
              color: 'var(--ai-color-text-tertiary)',
            }}
          >
            Format: +1234567890 (E.164 format)
          </p>
        </div>

        <Input
          label="From Phone Number (optional)"
          {...register('from_number')}
          error={errors.from_number?.message}
          placeholder="+1234567890"
          type="tel"
        />
        <div>
          <p
            style={{
              fontSize: 'var(--ai-font-size-caption)',
              color: 'var(--ai-color-text-tertiary)',
            }}
          >
            Leave empty to use default number
          </p>
        </div>

        <Select
          label="Business Configuration"
          options={[
            { value: '', label: 'Select a configuration...' },
            ...activeConfigs.map((config) => ({
              value: config.id,
              label: `${config.name} (${config.type})`,
            })),
          ]}
          {...register('business_id')}
          error={errors.business_id?.message}
        />

        <Select
          label="Agent Personality (Optional)"
          options={[
            { value: '', label: 'Use default personality...' },
            ...personalities.map((personality) => ({
              value: personality.name,
              label: personality.display_name,
            })),
          ]}
          {...register('agent_personality')}
          error={errors.agent_personality?.message}
        />
        {personalities.length > 0 && (
          <div>
            <p
              style={{
                fontSize: 'var(--ai-font-size-caption)',
                color: 'var(--ai-color-text-tertiary)',
              }}
            >
              Select an agent personality to customize the AI's communication style, voice, and skills.
            </p>
          </div>
        )}

        {activeConfigs.length === 0 && (
          <div
            style={{
              padding: 'var(--ai-spacing-4)',
              backgroundColor: 'var(--ai-color-bg-warning)',
              border: '1.5px solid var(--ai-color-brand-warning)',
              borderRadius: 'var(--ai-radius-base)',
            }}
          >
            <p
              style={{
                fontSize: 'var(--ai-font-size-body-small)',
                color: 'var(--ai-color-brand-warning)',
                margin: 0,
              }}
            >
              ⚠️ No active business configurations found. Please create one in Settings first.
            </p>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button
            type="button"
            variant="ghost"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
            disabled={activeConfigs.length === 0}
          >
            Initiate Call
          </Button>
        </div>
      </form>
    </Modal>
  );
};

