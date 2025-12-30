import { useCalendarStatus, useCalendarOAuth } from '@/lib/hooks';
import { useAppStore } from '@/lib/store';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { CheckCircle2, XCircle, Loader2, AlertCircle } from 'lucide-react';

export const CalendarStatus = () => {
  const { data: status, isLoading, error, refetch } = useCalendarStatus();
  const oauthMutation = useCalendarOAuth();
  const calendarConnected = useAppStore((state) => state.calendarConnected);

  const isConnected = status?.connected ?? calendarConnected ?? false;

  const handleConnect = () => {
    oauthMutation.mutate();
  };

  if (isLoading && status === undefined && !error) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Google Calendar (OAuth)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-yellow-600" />
            <p className="text-sm text-yellow-800">Unable to check calendar status</p>
            <Button onClick={() => refetch()} variant="ghost" size="sm" className="ml-auto">
              Retry
            </Button>
          </div>
        )}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <Badge variant="success">Connected</Badge>
              </>
            ) : (
              <>
                <XCircle className="w-5 h-5 text-red-600" />
                <Badge variant="error">Not Connected</Badge>
              </>
            )}
          </div>
          <Button
            onClick={handleConnect}
            disabled={oauthMutation.isPending}
            variant={isConnected ? 'outline' : 'primary'}
          >
            {oauthMutation.isPending
              ? 'Connecting...'
              : isConnected
              ? 'Reconnect Google'
              : 'Connect Google'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

