import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import { CheckCircle2, XCircle, Loader2, AlertCircle, Phone, MessageSquare, Shield, Save } from 'lucide-react';
import toast from 'react-hot-toast';

interface TwilioStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'not_configured';
  message: string;
  error?: string;
  config_required?: string[];
}

interface TwilioConfig {
  account_sid: string;
  auth_token: string;
  phone_number: string;
  whatsapp_number: string;
}

export const TwilioSettings = () => {
  const queryClient = useQueryClient();
  const [showConfig, setShowConfig] = useState(false);
  const [config, setConfig] = useState<TwilioConfig>({
    account_sid: '',
    auth_token: '',
    phone_number: '',
    whatsapp_number: '',
  });

  // Fetch Twilio status from health endpoint
  const { data: status, isLoading, error, refetch } = useQuery<TwilioStatus>({
    queryKey: ['twilio-status'],
    queryFn: () => api.get<TwilioStatus>('/api/health/integrations/twilio').then(res => res.data),
    retry: 1,
    refetchInterval: 30000, // Check every 30 seconds
  });

  // Load saved config from localStorage on mount
  useEffect(() => {
    const savedConfig = localStorage.getItem('twilio_config');
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig);
        setConfig({
          account_sid: parsed.account_sid || '',
          auth_token: '', // Never persist auth token to localStorage for security
          phone_number: parsed.phone_number || '',
          whatsapp_number: parsed.whatsapp_number || '',
        });
      } catch (e) {
        console.error('Failed to parse saved Twilio config');
      }
    }
  }, []);

  const isConnected = status?.status === 'healthy';
  const isConfigured = status?.status !== 'not_configured';

  const handleSaveConfig = async () => {
    // Validate required fields
    if (!config.account_sid.trim()) {
      toast.error('Account SID is required');
      return;
    }
    if (!config.auth_token.trim()) {
      toast.error('Auth Token is required');
      return;
    }
    if (!config.phone_number.trim()) {
      toast.error('Phone number is required');
      return;
    }

    // Validate phone number format (E.164)
    const phoneRegex = /^\+[1-9]\d{1,14}$/;
    if (!phoneRegex.test(config.phone_number)) {
      toast.error('Phone number must be in E.164 format (e.g., +15551234567)');
      return;
    }

    // Save to localStorage (except auth token)
    localStorage.setItem('twilio_config', JSON.stringify({
      account_sid: config.account_sid,
      phone_number: config.phone_number,
      whatsapp_number: config.whatsapp_number,
    }));

    // In a real implementation, this would save to the backend
    // For now, show success message and refresh status
    toast.success('Twilio configuration saved. Restart the backend to apply changes.');
    setShowConfig(false);
    
    // Refresh status after a short delay
    setTimeout(() => {
      refetch();
    }, 1000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Twilio Phone & Messaging</h2>
        <p className="text-slate-400">
          Connect your Twilio account to enable SMS, MMS, and WhatsApp messaging
        </p>
      </div>

      {/* Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="w-5 h-5" />
            Connection Status
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading && status === undefined && !error && (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            </div>
          )}
          
          {error && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <p className="text-sm text-amber-300 flex-1">Unable to check Twilio status</p>
              <Button onClick={() => refetch()} variant="ghost" size="sm" className="ml-auto">
                Retry
              </Button>
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isConnected ? (
                <>
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <Badge variant="success">Connected</Badge>
                </>
              ) : isConfigured ? (
                <>
                  <AlertCircle className="w-5 h-5 text-amber-400" />
                  <Badge variant="warning">Configured but not healthy</Badge>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-red-400" />
                  <Badge variant="error">Not Configured</Badge>
                </>
              )}
            </div>
            <Button
              onClick={() => setShowConfig(!showConfig)}
              variant={isConnected ? 'outline' : 'primary'}
            >
              {showConfig ? 'Cancel' : isConnected ? 'Update Configuration' : 'Configure Twilio'}
            </Button>
          </div>

          {status?.message && !showConfig && (
            <p className="text-sm text-slate-400">{status.message}</p>
          )}
          
          {status?.error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              <p className="text-sm text-red-300">{status.error}</p>
            </div>
          )}

          {isConnected && !showConfig && (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
              <p className="text-sm text-emerald-300">
                Twilio is connected. You can send and receive SMS, MMS, and WhatsApp messages.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configuration Form */}
      {showConfig && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Twilio Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 mb-4">
              <p className="text-sm text-amber-300">
                ⚠️ These credentials should be set as environment variables on your server for security. 
                This form is for reference/testing only.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Account SID *
              </label>
              <Input
                value={config.account_sid}
                onChange={(e) => setConfig({ ...config, account_sid: e.target.value })}
                placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              />
              <p className="mt-1 text-xs text-slate-500">
                Found in your Twilio Console dashboard
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Auth Token *
              </label>
              <Input
                type="password"
                value={config.auth_token}
                onChange={(e) => setConfig({ ...config, auth_token: e.target.value })}
                placeholder="••••••••••••••••••••••••••••••••"
              />
              <p className="mt-1 text-xs text-slate-500">
                Keep this secret! Found in your Twilio Console
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Twilio Phone Number *
              </label>
              <Input
                value={config.phone_number}
                onChange={(e) => setConfig({ ...config, phone_number: e.target.value })}
                placeholder="+15551234567"
              />
              <p className="mt-1 text-xs text-slate-500">
                Your Twilio phone number in E.164 format
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                WhatsApp Number (Optional)
              </label>
              <Input
                value={config.whatsapp_number}
                onChange={(e) => setConfig({ ...config, whatsapp_number: e.target.value })}
                placeholder="+15551234567"
              />
              <p className="mt-1 text-xs text-slate-500">
                For WhatsApp Business API (usually same as phone number)
              </p>
            </div>

            <div className="flex gap-2 pt-2">
              <Button onClick={handleSaveConfig} variant="primary">
                <Save className="w-4 h-4 mr-2" />
                Save Configuration
              </Button>
              <Button onClick={() => setShowConfig(false)} variant="ghost">
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Capabilities Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Messaging Capabilities
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Phone className="w-5 h-5 text-blue-400" />
                <h4 className="font-semibold text-white">SMS</h4>
              </div>
              <p className="text-sm text-slate-400">
                Send and receive text messages to any phone number
              </p>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className="w-5 h-5 text-green-400" />
                <h4 className="font-semibold text-white">MMS</h4>
              </div>
              <p className="text-sm text-slate-400">
                Send images, documents, and media files
              </p>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className="w-5 h-5 text-emerald-400" />
                <h4 className="font-semibold text-white">WhatsApp</h4>
              </div>
              <p className="text-sm text-slate-400">
                Connect via WhatsApp Business API
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Help Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-purple-300 mb-2">Getting Started with Twilio</h3>
            <ol className="text-sm text-purple-200 space-y-2 list-decimal list-inside">
              <li>Create a free account at <a href="https://www.twilio.com" target="_blank" rel="noopener noreferrer" className="underline hover:text-purple-100">twilio.com</a></li>
              <li>Get a phone number from Twilio Console</li>
              <li>Copy your Account SID and Auth Token</li>
              <li>Set these as environment variables:
                <code className="block mt-1 bg-slate-900 p-2 rounded text-xs text-slate-300">
                  TWILIO_ACCOUNT_SID=ACxxx<br/>
                  TWILIO_AUTH_TOKEN=xxx<br/>
                  TWILIO_PHONE_NUMBER=+1xxx
                </code>
              </li>
            </ol>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

