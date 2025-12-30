import { useState } from 'react';
import { GodfatherSettings } from '@/components/settings/GodfatherSettings';
import { EmailSettings } from '@/components/settings/EmailSettings';
import { CalendarSettings } from '@/components/settings/CalendarSettings';
import { TwilioSettings } from '@/components/settings/TwilioSettings';
import { WorkPreferencesSettings } from '@/components/settings/WorkPreferences';
import { BudgetSettings } from '@/components/settings/BudgetSettings';
import { AIAutonomySettings } from '@/components/settings/AIAutonomySettings';
import { cn } from '@/lib/utils';
import { 
  Settings2, 
  Link2, 
  DollarSign, 
  Clock, 
  User,
  Calendar,
  Mail,
  Phone
} from 'lucide-react';

type SettingsTab = 'integrations' | 'preferences' | 'account';

const tabs = [
  { id: 'integrations' as const, label: 'Integrations', icon: Link2, description: 'Connect services' },
  { id: 'preferences' as const, label: 'Preferences', icon: Settings2, description: 'Work & AI settings' },
  { id: 'account' as const, label: 'Account', icon: User, description: 'Your profile' },
];

export const Settings = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('integrations');

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-slate-400">
          Configure your AI assistant, connect services, and manage preferences
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-8 border-b border-slate-700 pb-4 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-3 rounded-lg transition-all whitespace-nowrap',
                activeTab === tab.id
                  ? 'bg-purple-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
            >
              <Icon className="w-5 h-5" />
              <div className="text-left">
                <div className="font-semibold">{tab.label}</div>
                <div className="text-xs opacity-75">{tab.description}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="space-y-8">
        {activeTab === 'integrations' && (
          <>
            {/* Quick Status Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-500/20 rounded-lg">
                    <Calendar className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">Calendar</h3>
                    <p className="text-xs text-slate-400">Schedule & events</p>
                  </div>
                </div>
              </div>
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-500/20 rounded-lg">
                    <Mail className="w-5 h-5 text-red-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">Email</h3>
                    <p className="text-xs text-slate-400">Gmail & Outlook</p>
                  </div>
                </div>
              </div>
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-500/20 rounded-lg">
                    <Phone className="w-5 h-5 text-green-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">Messaging</h3>
                    <p className="text-xs text-slate-400">SMS & WhatsApp</p>
                  </div>
                </div>
              </div>
            </div>

            <CalendarSettings />
            <EmailSettings />
            <TwilioSettings />
          </>
        )}

        {activeTab === 'preferences' && (
          <>
            <AIAutonomySettings />
            <WorkPreferencesSettings />
            <BudgetSettings />
          </>
        )}

        {activeTab === 'account' && (
          <>
            <GodfatherSettings />
          </>
        )}
      </div>
    </div>
  );
};

