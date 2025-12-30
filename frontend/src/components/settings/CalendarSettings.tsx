import { useState } from 'react';
import { useCalendarStatus, useCalendarOAuth } from '@/lib/hooks';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { CheckCircle2, XCircle, Loader2, AlertCircle, Calendar, Link2, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';

export const CalendarSettings = () => {
  const { data: calendarStatus, isLoading, error, refetch } = useCalendarStatus();
  const calendarOAuth = useCalendarOAuth();
  const [icsUrl, setIcsUrl] = useState('');
  const [showIcsForm, setShowIcsForm] = useState(false);

  const connected = calendarStatus?.connected ?? false;

  const handleGoogleConnect = () => {
    calendarOAuth.mutate();
  };

  const handleSaveIcs = async () => {
    if (!icsUrl.trim()) {
      toast.error('Please enter an ICS URL');
      return;
    }
    
    // Validate URL format
    try {
      new URL(icsUrl);
    } catch {
      toast.error('Please enter a valid URL');
      return;
    }

    // Save ICS URL to localStorage for now
    // In a full implementation, this would be saved to the backend
    localStorage.setItem('ics_calendar_url', icsUrl);
    toast.success('ICS calendar URL saved');
    setShowIcsForm(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Calendar Integration</h2>
        <p className="text-slate-400">
          Connect your calendar to enable AI scheduling and event management
        </p>
      </div>

      {/* Google Calendar Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Google Calendar
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading && calendarStatus === undefined && !error && (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            </div>
          )}
          
          {error && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <p className="text-sm text-amber-300 flex-1">Unable to check calendar status</p>
              <Button onClick={() => refetch()} variant="ghost" size="sm" className="ml-auto">
                Retry
              </Button>
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {connected ? (
                <>
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <Badge variant="success">Connected</Badge>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-red-400" />
                  <Badge variant="error">Not Connected</Badge>
                </>
              )}
            </div>
            <Button
              onClick={handleGoogleConnect}
              disabled={calendarOAuth.isPending}
              variant={connected ? 'outline' : 'primary'}
            >
              {calendarOAuth.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Connecting...
                </>
              ) : connected ? (
                'Reconnect'
              ) : (
                'Connect Google Calendar'
              )}
            </Button>
          </div>
          
          {connected && (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
              <p className="text-sm text-emerald-300">
                Google Calendar is connected. The AI can create, update, and view your calendar events.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ICS Calendar Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link2 className="w-5 h-5" />
            ICS Calendar Feed
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-slate-400">
            Connect any calendar that provides an ICS feed URL (Apple Calendar, Outlook.com, etc.)
          </p>
          
          {!showIcsForm ? (
            <Button
              onClick={() => setShowIcsForm(true)}
              variant="secondary"
            >
              <Link2 className="w-4 h-4 mr-2" />
              Add ICS Calendar
            </Button>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  ICS Feed URL
                </label>
                <Input
                  value={icsUrl}
                  onChange={(e) => setIcsUrl(e.target.value)}
                  placeholder="https://calendar.example.com/feed.ics"
                />
                <p className="mt-1 text-xs text-slate-500">
                  Find this in your calendar app's sharing settings
                </p>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleSaveIcs} variant="primary" size="sm">
                  Save ICS URL
                </Button>
                <Button 
                  onClick={() => {
                    setShowIcsForm(false);
                    setIcsUrl('');
                  }} 
                  variant="ghost" 
                  size="sm"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
          
          {/* Help Section */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mt-4">
            <h4 className="text-sm font-semibold text-white mb-2">How to get your ICS URL</h4>
            <ul className="text-sm text-slate-400 space-y-2">
              <li className="flex items-start gap-2">
                <span className="font-medium text-slate-300">Apple Calendar:</span>
                Calendar app → Right-click calendar → Share Calendar → Public Calendar
              </li>
              <li className="flex items-start gap-2">
                <span className="font-medium text-slate-300">Outlook.com:</span>
                Settings → Calendar → Shared calendars → Publish a calendar
              </li>
              <li className="flex items-start gap-2">
                <span className="font-medium text-slate-300">Google Calendar:</span>
                Settings → Select calendar → Integrate calendar → Public URL
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-purple-300 mb-2">What you can do with calendar</h3>
            <ul className="text-sm text-purple-200 space-y-1 list-disc list-inside">
              <li>View upcoming events and availability</li>
              <li>Create new events via AI commands</li>
              <li>Auto-schedule tasks based on your calendar</li>
              <li>Get reminders before important meetings</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

