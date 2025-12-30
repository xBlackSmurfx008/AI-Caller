import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Loader2, Clock, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';

interface WorkPreferences {
  working_hours_start: string;
  working_hours_end: string;
  working_days: number[];
  buffer_minutes: number;
  max_blocks_per_day: number;
  timezone: string;
}

const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
];

export const WorkPreferencesSettings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preferences, setPreferences] = useState<WorkPreferences>({
    working_hours_start: '09:00',
    working_hours_end: '17:00',
    working_days: [1, 2, 3, 4, 5], // Mon-Fri
    buffer_minutes: 15,
    max_blocks_per_day: 8,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });

  useEffect(() => {
    // Fetch work preferences from API
    const fetchPreferences = async () => {
      try {
        const response = await api.get('/api/settings/work-preferences');
        if (response.data) {
          setPreferences({
            working_hours_start: response.data.working_hours_start || '09:00',
            working_hours_end: response.data.working_hours_end || '17:00',
            working_days: response.data.working_days || [1, 2, 3, 4, 5],
            buffer_minutes: response.data.buffer_minutes || 15,
            max_blocks_per_day: response.data.max_blocks_per_day || 8,
            timezone: response.data.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
          });
        }
      } catch (error: any) {
        // If endpoint doesn't exist yet, use defaults
        console.log('Work preferences endpoint not available, using defaults');
      } finally {
        setLoading(false);
      }
    };

    fetchPreferences();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.post('/api/settings/work-preferences', preferences);
      toast.success('Work preferences saved');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save work preferences');
    } finally {
      setSaving(false);
    }
  };

  const toggleDay = (day: number) => {
    setPreferences((prev) => ({
      ...prev,
      working_days: prev.working_days.includes(day)
        ? prev.working_days.filter((d) => d !== day)
        : [...prev.working_days, day].sort(),
    }));
  };

  if (loading) {
    return (
      <Card className="bg-slate-900/50 border-slate-700">
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-900/50 border-slate-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Work Hours & Scheduling
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Working Hours */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Working Hours
          </label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Start Time</label>
              <Input
                type="time"
                value={preferences.working_hours_start}
                onChange={(e) =>
                  setPreferences({ ...preferences, working_hours_start: e.target.value })
                }
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">End Time</label>
              <Input
                type="time"
                value={preferences.working_hours_end}
                onChange={(e) =>
                  setPreferences({ ...preferences, working_hours_end: e.target.value })
                }
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>
        </div>

        {/* Working Days */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Working Days
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {DAYS_OF_WEEK.map((day) => (
              <button
                key={day.value}
                type="button"
                onClick={() => toggleDay(day.value)}
                className={`p-3 rounded-lg border-2 transition-colors ${
                  preferences.working_days.includes(day.value)
                    ? 'bg-purple-500/20 border-purple-500 text-purple-400'
                    : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600'
                }`}
              >
                <div className="text-xs font-medium">{day.label.slice(0, 3)}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Buffer Time */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Buffer Time Between Tasks (minutes)
          </label>
          <Input
            type="number"
            min="0"
            max="60"
            value={preferences.buffer_minutes}
            onChange={(e) =>
              setPreferences({ ...preferences, buffer_minutes: parseInt(e.target.value) || 15 })
            }
            className="bg-slate-800 border-slate-700 text-white"
          />
          <p className="text-xs text-slate-400 mt-1">
            Time to add between scheduled tasks for transitions
          </p>
        </div>

        {/* Max Blocks Per Day */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Maximum Task Blocks Per Day
          </label>
          <Input
            type="number"
            min="1"
            max="20"
            value={preferences.max_blocks_per_day}
            onChange={(e) =>
              setPreferences({ ...preferences, max_blocks_per_day: parseInt(e.target.value) || 8 })
            }
            className="bg-slate-800 border-slate-700 text-white"
          />
          <p className="text-xs text-slate-400 mt-1">
            Maximum number of scheduled task blocks per day
          </p>
        </div>

        {/* Timezone */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Timezone
          </label>
          <select
            value={preferences.timezone}
            onChange={(e) => setPreferences({ ...preferences, timezone: e.target.value })}
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
          >
            {Intl.supportedValuesOf('timeZone').map((tz) => (
              <option key={tz} value={tz}>
                {tz}
              </option>
            ))}
          </select>
        </div>

        <Button
          onClick={handleSave}
          disabled={saving}
          variant="primary"
          className="w-full sm:w-auto"
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            'Save Preferences'
          )}
        </Button>
      </CardContent>
    </Card>
  );
};

