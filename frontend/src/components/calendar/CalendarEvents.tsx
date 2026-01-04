import { useCalendarEvents } from '@/lib/hooks';
import { useAppStore } from '@/lib/store';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, Loader2, XCircle, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const CalendarEvents = () => {
  const calendarConnected = useAppStore((state) => state.calendarConnected);
  const { data, isLoading, error } = useCalendarEvents(10);
  const navigate = useNavigate();

  if (calendarConnected === false) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <CalendarIcon className="w-5 h-5" />
              Upcoming Events
            </CardTitle>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/messages')}
              className="flex items-center gap-2 shadow-sm hover:shadow-md"
            >
              <MessageSquare className="w-4 h-4" />
              Messages
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-gray-500 py-4">
            <XCircle className="w-4 h-4" />
            <p className="text-sm">Connect Google Calendar to view events</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <CalendarIcon className="w-5 h-5" />
              Upcoming Events
            </CardTitle>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/messages')}
              className="flex items-center gap-2 shadow-sm hover:shadow-md"
            >
              <MessageSquare className="w-4 h-4" />
              Messages
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <CalendarIcon className="w-5 h-5" />
              Upcoming Events
            </CardTitle>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/messages')}
              className="flex items-center gap-2 shadow-sm hover:shadow-md"
            >
              <MessageSquare className="w-4 h-4" />
              Messages
            </Button>
          </div>
        </CardHeader>
        <CardContent className="py-8 text-center">
          <p className="text-red-600 text-sm">Failed to load calendar events.</p>
        </CardContent>
      </Card>
    );
  }

  const events = data?.events || [];

  if (events.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <CalendarIcon className="w-5 h-5" />
              Upcoming Events
            </CardTitle>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/messages')}
              className="flex items-center gap-2 shadow-sm hover:shadow-md"
            >
              <MessageSquare className="w-4 h-4" />
              Messages
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-slate-400 text-center py-4">No upcoming events</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <CalendarIcon className="w-5 h-5" />
            Upcoming Events
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/messages')}
            className="flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            Messages
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {events.map((event) => {
            const startDate = event.start?.dateTime
              ? new Date(event.start.dateTime)
              : event.start?.date
              ? new Date(event.start.date)
              : null;
            const endDate = event.end?.dateTime
              ? new Date(event.end.dateTime)
              : event.end?.date
              ? new Date(event.end.date)
              : null;

            return (
              <div
                key={event.id}
                className="border-l-4 border-purple-500 pl-4 py-2 rounded-r transition-colors hover:bg-slate-800/60"
              >
                <h4 className="font-semibold text-white">{event.summary}</h4>
                {startDate && (
                  <p className="text-sm mt-1">
                    <span className="text-blue-400">
                      {format(startDate, 'MMM d, yyyy h:mm a')}
                      {endDate && ` - ${format(endDate, 'h:mm a')}`}
                    </span>
                  </p>
                )}
                {event.location && (
                  <p className="text-sm text-slate-300 mt-1">📍 {event.location}</p>
                )}
                {event.htmlLink && (
                  <a
                    href={event.htmlLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-400 hover:underline mt-1 inline-block"
                  >
                    View in Google Calendar
                  </a>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

