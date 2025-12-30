import { useState } from 'react';
import { CalendarStatus } from '@/components/calendar/CalendarStatus';
import { CalendarEvents } from '@/components/calendar/CalendarEvents';
import { VisualCalendar } from '@/components/calendar/VisualCalendar';
import { IcsConnect } from '@/components/calendar/IcsConnect';
import { Button } from '@/components/ui/Button';
import { Calendar as CalendarIcon, List } from 'lucide-react';

export const Calendar = () => {
  const [view, setView] = useState<'visual' | 'list'>('visual');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Calendar</h1>
          <p className="text-white/80">
            Visual schedule view with tasks and calendar events
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={view === 'visual' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setView('visual')}
          >
            <CalendarIcon className="w-4 h-4 mr-2" />
            Visual
          </Button>
          <Button
            variant={view === 'list' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setView('list')}
          >
            <List className="w-4 h-4 mr-2" />
            List
          </Button>
        </div>
      </div>

      {view === 'visual' ? (
        <>
          <div className="mb-6">
            <VisualCalendar />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CalendarStatus />
            <IcsConnect />
          </div>
        </>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <CalendarStatus />
            <IcsConnect />
          </div>
          <div>
            <CalendarEvents />
          </div>
        </>
      )}
    </div>
  );
};

