import { useState, useRef, useEffect } from 'react';
import { useGodfatherSettings, useUpdateGodfatherSettings } from '@/lib/hooks';
import { useAppStore } from '@/lib/store';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { toast } from 'react-hot-toast';
import { Loader2, AlertCircle } from 'lucide-react';

export const GodfatherSettings = () => {
  const { data, isLoading, error } = useGodfatherSettings();
  const updateSettings = useUpdateGodfatherSettings();
  const { godfatherSettings, setGodfatherSettings } = useAppStore();

  // Use ref to track if we've already synced from initial data load
  const hasSyncedFromData = useRef(false);

  // Get initial values from store
  const [phoneNumbers, setPhoneNumbers] = useState(godfatherSettings.phone_numbers_csv || '');
  const [email, setEmail] = useState(godfatherSettings.email || '');

  // Sync from API data on initial load only - this is intentional one-time sync
  useEffect(() => {
    if (data && !hasSyncedFromData.current) {
      setPhoneNumbers(data.phone_numbers_csv || '');
      setEmail(data.email || '');
      hasSyncedFromData.current = true;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
  }, [data]);

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync({
        phone_numbers_csv: phoneNumbers,
        email: email,
      });
      setGodfatherSettings({ phone_numbers_csv: phoneNumbers, email });
      toast.success('Settings saved successfully');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save settings');
    }
  };

  if (isLoading && !data) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Godfather Settings</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && isLoading === false && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-yellow-600" />
            <p className="text-sm text-yellow-800">Unable to load settings from server. Using local values.</p>
          </div>
        )}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone Numbers (CSV, E.164 format)
          </label>
          <Input
            value={phoneNumbers}
            onChange={(e) => setPhoneNumbers(e.target.value)}
            placeholder='E.g., "+15551234567,+15557654321"'
            disabled={updateSettings.isPending}
          />
          <p className="mt-1 text-xs text-gray-500">
            Comma-separated list of phone numbers in E.164 format
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Address
          </label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="godfather@example.com"
            disabled={updateSettings.isPending}
          />
          <p className="mt-1 text-xs text-gray-500">Optional email address for the Godfather</p>
        </div>

        <Button
          onClick={handleSave}
          disabled={updateSettings.isPending}
          className="w-full sm:w-auto"
        >
          {updateSettings.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            'Save Settings'
          )}
        </Button>
      </CardContent>
    </Card>
  );
};
