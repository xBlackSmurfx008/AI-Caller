import { useState } from 'react';
import { useDailyPlan, useCalendarEvents } from '@/lib/hooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Loader2, ChevronLeft, ChevronRight, Calendar as CalendarIcon, Clock, Sparkles, Lock, Unlock } from 'lucide-react';
import { format, startOfWeek, addDays, addWeeks, subWeeks, isSameDay, isToday, getHours, getMinutes } from 'date-fns';
import { Link } from 'react-router-dom';

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

interface TimeBlock {
  id: string;
  title: string;
  start: Date;
  end: Date;
  type: 'task' | 'event';
  executionMode?: string;
  locked?: boolean;
  color?: string;
}

export const VisualCalendar = () => {
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 0 });
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  const { data: dailyPlan, isLoading: planLoading } = useDailyPlan();
  const { data: calendarData, isLoading: eventsLoading } = useCalendarEvents(50);

  const isLoading = planLoading || eventsLoading;

  // Convert scheduled tasks to time blocks
  const taskBlocks: TimeBlock[] = [];
  if (dailyPlan) {
    dailyPlan.scheduled_tasks.forEach((task) => {
      const start = new Date(task.start);
      const end = new Date(task.end);
      taskBlocks.push({
        id: task.task_id,
        title: task.title,
        start,
        end,
        type: 'task',
        executionMode: task.execution_mode,
        locked: false,
        color: task.execution_mode === 'AI' ? 'purple' : task.execution_mode === 'HYBRID' ? 'indigo' : 'blue',
      });
    });
  }

  // Convert calendar events to time blocks
  const eventBlocks: TimeBlock[] = [];
  if (calendarData?.events) {
    calendarData.events.forEach((event) => {
      const start = event.start?.dateTime ? new Date(event.start.dateTime) : event.start?.date ? new Date(event.start.date) : null;
      const end = event.end?.dateTime ? new Date(event.end.dateTime) : event.end?.date ? new Date(event.end.date) : null;
      if (start && end) {
        eventBlocks.push({
          id: event.id,
          title: event.summary || 'Untitled',
          start,
          end,
          type: 'event',
          color: 'gray',
        });
      }
    });
  }

  const allBlocks = [...taskBlocks, ...eventBlocks];

  const getBlocksForDay = (day: Date) => {
    return allBlocks.filter((block) => isSameDay(block.start, day));
  };

  const getBlockPosition = (block: TimeBlock) => {
    const startMinutes = getHours(block.start) * 60 + getMinutes(block.start);
    const endMinutes = getHours(block.end) * 60 + getMinutes(block.end);
    const duration = endMinutes - startMinutes;
    const topPercent = (startMinutes / (24 * 60)) * 100;
    const heightPercent = (duration / (24 * 60)) * 100;
    return { top: `${topPercent}%`, height: `${heightPercent}%` };
  };

  const getBlockColor = (block: TimeBlock) => {
    if (block.type === 'event') {
      return 'bg-slate-600 border-slate-500';
    }
    switch (block.color) {
      case 'purple':
        return 'bg-purple-500/80 border-purple-400';
      case 'indigo':
        return 'bg-indigo-500/80 border-indigo-400';
      case 'blue':
        return 'bg-blue-500/80 border-blue-400';
      default:
        return 'bg-slate-500/80 border-slate-400';
    }
  };

  const handlePreviousWeek = () => {
    setCurrentWeek(subWeeks(currentWeek, 1));
  };

  const handleNextWeek = () => {
    setCurrentWeek(addWeeks(currentWeek, 1));
  };

  const handleToday = () => {
    setCurrentWeek(new Date());
  };

  return (
    <Card className="bg-slate-900/50 border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <CalendarIcon className="w-5 h-5" />
            Weekly Schedule
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handlePreviousWeek}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleToday}>
              Today
            </Button>
            <Button variant="ghost" size="sm" onClick={handleNextWeek}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
        <div className="text-sm text-slate-400 mt-2">
          {format(weekStart, 'MMM d')} - {format(addDays(weekStart, 6), 'MMM d, yyyy')}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <div className="min-w-[800px]">
              {/* Day Headers */}
              <div className="grid grid-cols-8 gap-1 mb-2">
                <div className="p-2"></div>
                {weekDays.map((day, idx) => (
                  <div
                    key={idx}
                    className={`p-2 text-center rounded ${
                      isToday(day) ? 'bg-purple-500/20 border border-purple-500/50' : 'bg-slate-800/50'
                    }`}
                  >
                    <div className="text-xs text-slate-400">{DAYS[idx]}</div>
                    <div className={`text-sm font-semibold ${isToday(day) ? 'text-purple-400' : 'text-white'}`}>
                      {format(day, 'd')}
                    </div>
                  </div>
                ))}
              </div>

              {/* Time Grid */}
              <div className="grid grid-cols-8 gap-1 relative">
                {/* Time Labels */}
                <div className="space-y-0">
                  {HOURS.map((hour) => (
                    <div key={hour} className="h-16 flex items-start justify-end pr-2 border-t border-slate-700">
                      <span className="text-xs text-slate-500">{hour}:00</span>
                    </div>
                  ))}
                </div>

                {/* Day Columns */}
                {weekDays.map((day, dayIdx) => {
                  const dayBlocks = getBlocksForDay(day);
                  return (
                    <div key={dayIdx} className="relative border-l border-slate-700">
                      {/* Hour Lines */}
                      {HOURS.map((hour) => (
                        <div key={hour} className="h-16 border-t border-slate-700/50"></div>
                      ))}

                      {/* Time Blocks */}
                      {dayBlocks.map((block) => {
                        const position = getBlockPosition(block);
                        return (
                          <div
                            key={block.id}
                            className={`absolute left-0 right-0 rounded border-l-2 ${getBlockColor(block)} text-white p-1 text-xs overflow-hidden cursor-pointer hover:opacity-90 transition-opacity z-10`}
                            style={{
                              top: position.top,
                              height: position.height,
                              minHeight: '20px',
                            }}
                            title={`${block.title} - ${format(block.start, 'h:mm a')} - ${format(block.end, 'h:mm a')}`}
                          >
                            <div className="flex items-start gap-1">
                              {block.type === 'task' && block.executionMode === 'AI' && (
                                <Sparkles className="w-3 h-3 flex-shrink-0 mt-0.5" />
                              )}
                              {block.locked && <Lock className="w-3 h-3 flex-shrink-0 mt-0.5" />}
                            </div>
                            <div className="font-medium truncate">{block.title}</div>
                            <div className="text-[10px] opacity-75">
                              {format(block.start, 'h:mm')} - {format(block.end, 'h:mm')}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="mt-6 pt-4 border-t border-slate-700">
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-500/80 rounded border border-purple-400"></div>
              <span className="text-slate-300">AI Tasks</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-indigo-500/80 rounded border border-indigo-400"></div>
              <span className="text-slate-300">Hybrid Tasks</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-500/80 rounded border border-blue-400"></div>
              <span className="text-slate-300">Human Tasks</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-slate-600 rounded border border-slate-500"></div>
              <span className="text-slate-300">Calendar Events</span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-4 flex gap-2">
          <Link to="/daily-plan">
            <Button variant="secondary" size="sm">
              View Daily Plan
            </Button>
          </Link>
          <Link to="/projects">
            <Button variant="secondary" size="sm">
              Schedule Tasks
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
};

