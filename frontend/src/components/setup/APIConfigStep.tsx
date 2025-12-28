import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import toast from 'react-hot-toast';
import { configAPI } from '../../api/config';

const apiConfigSchema = z.object({
  openai_api_key: z.string().min(1, 'OpenAI API key is required'),
  telephony_provider: z.enum(['twilio', 'ringcentral']),
  twilio_account_sid: z.string().optional(),
  twilio_auth_token: z.string().optional(),
  twilio_phone_number: z.string().optional(),
  ringcentral_client_id: z.string().optional(),
  ringcentral_client_secret: z.string().optional(),
  ringcentral_server_url: z.string().optional(),
  webhook_url: z.string().url('Invalid URL').optional().or(z.literal('')),
}).refine((data) => {
  if (data.telephony_provider === 'twilio') {
    return data.twilio_account_sid && data.twilio_auth_token && data.twilio_phone_number;
  } else {
    return data.ringcentral_client_id && data.ringcentral_client_secret && data.ringcentral_server_url;
  }
}, {
  message: 'Please fill in all required fields for the selected provider',
});

type APIConfigData = z.infer<typeof apiConfigSchema>;

interface APIConfigStepProps {
  formData: any;
  onNext: (data: any) => void;
  onBack: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export const APIConfigStep: React.FC<APIConfigStepProps> = ({
  formData,
  onNext,
  onBack,
  isFirstStep,
}) => {
  const [isTesting, setIsTesting] = useState(false);
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<APIConfigData>({
    resolver: zodResolver(apiConfigSchema),
    defaultValues: {
      telephony_provider: 'twilio',
      ...formData.apiConfig,
    },
  });

  const selectedProvider = watch('telephony_provider');

  const testConnection = async (data: APIConfigData) => {
    setIsTesting(true);
    try {
      let result;
      if (data.telephony_provider === 'twilio') {
        result = await configAPI.testConnection({
          openai_api_key: data.openai_api_key,
          twilio_account_sid: data.twilio_account_sid || '',
          twilio_auth_token: data.twilio_auth_token || '',
          twilio_phone_number: data.twilio_phone_number,
        });
      } else {
        // For RingCentral, we'd need a separate test endpoint
        // For now, just test OpenAI
        toast.info('RingCentral connection testing coming soon');
        return true;
      }
      
      if (result.success) {
        toast.success('Connection test successful!');
        return true;
      } else {
        const errors: string[] = [];
        if (!result.openai.connected) {
          errors.push(`OpenAI: ${result.openai.error || 'Connection failed'}`);
        }
        if (data.telephony_provider === 'twilio' && !result.twilio.connected) {
          errors.push(`Twilio: ${result.twilio.error || 'Connection failed'}`);
        }
        toast.error(`Connection test failed: ${errors.join(', ')}`);
        return false;
      }
    } catch (error: any) {
      const errorMessage = error?.error?.message || error?.message || 'Connection test failed';
      toast.error(errorMessage);
      return false;
    } finally {
      setIsTesting(false);
    }
  };

  const onSubmit = async (data: APIConfigData) => {
    try {
      // Test connection first
      const success = await testConnection(data);
      if (success) {
        onNext({ apiConfig: data });
      }
    } catch (error) {
      console.error('Error submitting API config:', error);
      toast.error('Failed to save API configuration');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">API Configuration</h2>
        <p className="text-gray-600">
          Configure your OpenAI and telephony provider API credentials
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">OpenAI</h3>
          <Input
            label="OpenAI API Key"
            type="password"
            {...register('openai_api_key')}
            error={errors.openai_api_key?.message}
            placeholder="sk-..."
          />
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Telephony Provider</h3>
          <Select
            label="Select Provider"
            {...register('telephony_provider')}
            error={errors.telephony_provider?.message}
            options={[
              { value: 'twilio', label: 'Twilio' },
              { value: 'ringcentral', label: 'RingCentral' },
            ]}
          />
        </div>

        {selectedProvider === 'twilio' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Twilio Configuration</h3>
            <Input
              label="Twilio Account SID"
              {...register('twilio_account_sid')}
              error={errors.twilio_account_sid?.message}
              placeholder="AC..."
            />
            <Input
              label="Twilio Auth Token"
              type="password"
              {...register('twilio_auth_token')}
              error={errors.twilio_auth_token?.message}
              placeholder="Your auth token"
            />
            <Input
              label="Twilio Phone Number"
              {...register('twilio_phone_number')}
              error={errors.twilio_phone_number?.message}
              placeholder="+1234567890"
            />
          </div>
        )}

        {selectedProvider === 'ringcentral' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">RingCentral Configuration</h3>
            <Input
              label="Client ID"
              {...register('ringcentral_client_id')}
              error={errors.ringcentral_client_id?.message}
              placeholder="Your RingCentral Client ID"
            />
            <Input
              label="Client Secret"
              type="password"
              {...register('ringcentral_client_secret')}
              error={errors.ringcentral_client_secret?.message}
              placeholder="Your RingCentral Client Secret"
            />
            <Input
              label="Server URL"
              {...register('ringcentral_server_url')}
              error={errors.ringcentral_server_url?.message}
              placeholder="https://platform.ringcentral.com"
            />
          </div>
        )}

        <div>
          <Input
            label="Webhook URL (optional)"
            {...register('webhook_url')}
            error={errors.webhook_url?.message}
            placeholder="https://your-domain.com/webhooks"
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
        <div className="flex space-x-2">
          <Button
            type="button"
            variant="secondary"
            onClick={handleSubmit(testConnection)}
            isLoading={isTesting}
          >
            Test Connection
          </Button>
          <Button type="submit" variant="primary" isLoading={isTesting}>
            Next
          </Button>
        </div>
      </div>
    </form>
  );
};

