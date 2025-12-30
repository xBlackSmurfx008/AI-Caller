import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Loader2, Sparkles, Shield, Zap, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

type AutonomyLevel = 'cautious' | 'balanced' | 'autopilot';

interface AutonomyPreset {
  level: AutonomyLevel;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  settings: {
    requireApprovalForMessages: boolean;
    requireApprovalForTasks: boolean;
    requireApprovalForScheduling: boolean;
    allowAutoReschedule: boolean;
    maxCostWithoutApproval: number;
  };
}

const PRESETS: AutonomyPreset[] = [
  {
    level: 'cautious',
    label: 'Cautious Mode',
    description: 'Require approval for most AI actions',
    icon: Shield,
    settings: {
      requireApprovalForMessages: true,
      requireApprovalForTasks: true,
      requireApprovalForScheduling: true,
      allowAutoReschedule: false,
      maxCostWithoutApproval: 0.10,
    },
  },
  {
    level: 'balanced',
    label: 'Balanced Mode',
    description: 'Approve important actions, auto-approve routine tasks',
    icon: Zap,
    settings: {
      requireApprovalForMessages: true,
      requireApprovalForTasks: false,
      requireApprovalForScheduling: false,
      allowAutoReschedule: true,
      maxCostWithoutApproval: 1.00,
    },
  },
  {
    level: 'autopilot',
    label: 'Autopilot Mode',
    description: 'Maximum AI autonomy with minimal approvals',
    icon: Sparkles,
    settings: {
      requireApprovalForMessages: false,
      requireApprovalForTasks: false,
      requireApprovalForScheduling: false,
      allowAutoReschedule: true,
      maxCostWithoutApproval: 10.00,
    },
  },
];

export const AIAutonomySettings = () => {
  const [selectedLevel, setSelectedLevel] = useState<AutonomyLevel>('balanced');
  const [saving, setSaving] = useState(false);
  const [customSettings, setCustomSettings] = useState(PRESETS[1].settings);

  const handleSelectPreset = (level: AutonomyLevel) => {
    setSelectedLevel(level);
    const preset = PRESETS.find((p) => p.level === level);
    if (preset) {
      setCustomSettings(preset.settings);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // This would save to API endpoint
      // For now, store in localStorage as a fallback
      localStorage.setItem('ai_autonomy_level', selectedLevel);
      localStorage.setItem('ai_autonomy_settings', JSON.stringify(customSettings));
      toast.success('AI autonomy settings saved');
    } catch (error: any) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const currentPreset = PRESETS.find((p) => p.level === selectedLevel);

  return (
    <Card className="bg-slate-900/50 border-slate-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          AI Autonomy Level
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Preset Selection */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-3">
            Choose Autonomy Level
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {PRESETS.map((preset) => {
              const Icon = preset.icon;
              const isSelected = selectedLevel === preset.level;
              return (
                <button
                  key={preset.level}
                  type="button"
                  onClick={() => handleSelectPreset(preset.level)}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${
                    isSelected
                      ? 'bg-purple-500/20 border-purple-500'
                      : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon
                      className={`w-5 h-5 ${
                        isSelected ? 'text-purple-400' : 'text-slate-400'
                      }`}
                    />
                    <span
                      className={`font-semibold ${
                        isSelected ? 'text-purple-400' : 'text-white'
                      }`}
                    >
                      {preset.label}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400">{preset.description}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Settings Details */}
        {currentPreset && (
          <div className="bg-slate-800/50 rounded-lg p-4 space-y-3">
            <h4 className="font-semibold text-white mb-3">Current Settings</h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Require approval for messages</span>
                <span
                  className={`font-medium ${
                    customSettings.requireApprovalForMessages
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}
                >
                  {customSettings.requireApprovalForMessages ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Require approval for tasks</span>
                <span
                  className={`font-medium ${
                    customSettings.requireApprovalForTasks
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}
                >
                  {customSettings.requireApprovalForTasks ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Require approval for scheduling</span>
                <span
                  className={`font-medium ${
                    customSettings.requireApprovalForScheduling
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}
                >
                  {customSettings.requireApprovalForScheduling ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Allow auto-reschedule</span>
                <span
                  className={`font-medium ${
                    customSettings.allowAutoReschedule
                      ? 'text-emerald-400'
                      : 'text-amber-400'
                  }`}
                >
                  {customSettings.allowAutoReschedule ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Max cost without approval</span>
                <span className="font-medium text-white">
                  ${customSettings.maxCostWithoutApproval.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Warning */}
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-400 mb-1">
                Autopilot Mode Warning
              </p>
              <p className="text-xs text-amber-300">
                Autopilot mode gives AI maximum autonomy. Ensure you have budget limits and
                monitoring in place. Review the audit log regularly.
              </p>
            </div>
          </div>
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
            'Save Autonomy Settings'
          )}
        </Button>
      </CardContent>
    </Card>
  );
};

