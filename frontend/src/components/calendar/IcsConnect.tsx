import { useState } from 'react';
import { useIcsPreview } from '@/lib/hooks';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Calendar as CalendarIcon, Loader2, Link as LinkIcon, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';

export const IcsConnect = () => {
  const [icsUrl, setIcsUrl] = useState('');
  const [lastUrl, setLastUrl] = useState('');
  const icsPreview = useIcsPreview();
  const events = icsPreview.data?.events || [];

  const handlePreview = () => {
    if (!icsUrl.trim()) return;
    setLastUrl(icsUrl.trim());
    icsPreview.mutate({ ics_url: icsUrl.trim(), limit: 10 });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarIcon className="w-5 h-5" />
          Any Calendar via ICS
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">ICS / iCal URL</label>
          <Input
            value={icsUrl}
            onChange={(e) => setIcsUrl(e.target.value)}
            placeholder="https://calendar.example.com/calendar.ics"
            disabled={icsPreview.isPending}
          />
          <p className="text-xs text-gray-500">
            Works with Google, Outlook, Apple, Fastmail, etc. Use the “secret ICS”/“subscribe” link from your calendar.
          </p>
        </div>
        <Button
          onClick={handlePreview}
          disabled={!icsUrl.trim() || icsPreview.isPending}
          variant="primary"
          className="w-full"
        >
          {icsPreview.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Connecting...
            </>
          ) : (
            'Connect & Preview'
          )}
        </Button>

        {icsPreview.isError && (
          <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded p-3 text-sm text-red-800">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <div>
              <p className="font-medium">Failed to load ICS feed</p>
              <p>{(icsPreview.error as any)?.response?.data?.detail || (icsPreview.error as Error).message}</p>
            </div>
          </div>
        )}

        {events.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <LinkIcon className="w-4 h-4" />
              <span className="truncate">{lastUrl}</span>
            </div>
            <div className="space-y-3">
              {events.map((event) => {
                const start = event.start?.dateTime ? new Date(event.start.dateTime) : undefined;
                const end = event.end?.dateTime ? new Date(event.end.dateTime) : undefined;
                return (
                  <div
                    key={event.id}
                    className="border-l-4 border-purple-500 pl-4 py-2 hover:bg-gray-50 rounded-r transition-colors"
                  >
                    <h4 className="font-semibold text-gray-900">{event.summary}</h4>
                    {start && (
                      <p className="text-sm text-gray-600 mt-1">
                        {format(start, 'MMM d, yyyy h:mm a')}
                        {end && ` - ${format(end, 'h:mm a')}`}
                      </p>
                    )}
                    {event.location && (
                      <p className="text-sm text-gray-500 mt-1">📍 {event.location}</p>
                    )}
                    {event.htmlLink && (
                      <a
                        href={event.htmlLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-purple-600 hover:underline mt-1 inline-block"
                      >
                        Open calendar
                      </a>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

