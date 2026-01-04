import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Loader2, User, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';

type Profile = {
  full_name?: string | null;
  preferred_name?: string | null;
  pronouns?: string | null;
  location?: string | null;
  timezone?: string | null;
  company?: string | null;
  title?: string | null;
  bio?: string | null;
  assistant_notes?: string | null;
  preferences?: Record<string, any> | null;
};

export const ProfileSettings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState<Profile>({
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    preferences: { tone: 'direct', signoff: '' },
  });
  const [prefJson, setPrefJson] = useState<string>('{\n  "tone": "direct",\n  "signoff": ""\n}');
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await api.get('/api/settings/profile');
        if (cancelled) return;
        const data = res.data || {};
        setProfile({
          ...data,
          timezone: data.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
          preferences: data.preferences || {},
        });
        setPrefJson(JSON.stringify(data.preferences || {}, null, 2));
      } catch (e: any) {
        if (cancelled) return;
        setLoadError(e?.response?.data?.detail || 'Unable to load profile from server.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setLoadError(null);
    try {
      let prefs: Record<string, any> = {};
      if (prefJson.trim()) {
        prefs = JSON.parse(prefJson);
      }
      await api.post('/api/settings/profile', {
        ...profile,
        preferences: prefs,
      });
      toast.success('Profile saved');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || e?.message || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
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
        <CardTitle className="flex items-center gap-2">
          <User className="w-5 h-5" />
          Your Profile (Godfather)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {loadError && (
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <p className="text-sm text-amber-300">{loadError}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Full name</label>
            <Input
              value={profile.full_name || ''}
              onChange={(e) => setProfile((p) => ({ ...p, full_name: e.target.value }))}
              placeholder="e.g., Stephen Smith"
              disabled={saving}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Preferred name</label>
            <Input
              value={profile.preferred_name || ''}
              onChange={(e) => setProfile((p) => ({ ...p, preferred_name: e.target.value }))}
              placeholder="e.g., Stephen"
              disabled={saving}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Pronouns</label>
            <Input
              value={profile.pronouns || ''}
              onChange={(e) => setProfile((p) => ({ ...p, pronouns: e.target.value }))}
              placeholder="e.g., he/him"
              disabled={saving}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>
            <select
              value={profile.timezone || 'UTC'}
              onChange={(e) => setProfile((p) => ({ ...p, timezone: e.target.value }))}
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-600"
              disabled={saving}
            >
              {Intl.supportedValuesOf('timeZone').map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
            <Input
              value={profile.location || ''}
              onChange={(e) => setProfile((p) => ({ ...p, location: e.target.value }))}
              placeholder="e.g., Miami, FL"
              disabled={saving}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Company</label>
            <Input
              value={profile.company || ''}
              onChange={(e) => setProfile((p) => ({ ...p, company: e.target.value }))}
              placeholder="e.g., AI Caller Inc."
              disabled={saving}
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Title / role</label>
            <Input
              value={profile.title || ''}
              onChange={(e) => setProfile((p) => ({ ...p, title: e.target.value }))}
              placeholder="e.g., Founder"
              disabled={saving}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Bio (short)</label>
          <Textarea
            value={profile.bio || ''}
            onChange={(e) => setProfile((p) => ({ ...p, bio: e.target.value }))}
            placeholder="A short description the assistant can use for intros, tone, and context."
            rows={4}
            disabled={saving}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Assistant notes (how it should behave for you)</label>
          <Textarea
            value={profile.assistant_notes || ''}
            onChange={(e) => setProfile((p) => ({ ...p, assistant_notes: e.target.value }))}
            placeholder="e.g., Keep replies concise, be proactive, prefer email over SMS unless urgent..."
            rows={4}
            disabled={saving}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Preferences (JSON, optional)</label>
          <Textarea
            value={prefJson}
            onChange={(e) => setPrefJson(e.target.value)}
            rows={6}
            disabled={saving}
          />
          <p className="mt-1 text-xs text-gray-500">
            Use this for structured preferences like tone, signoff, writing style, etc.
          </p>
        </div>

        <Button onClick={handleSave} disabled={saving} className="w-full sm:w-auto">
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            'Save Profile'
          )}
        </Button>
      </CardContent>
    </Card>
  );
};


