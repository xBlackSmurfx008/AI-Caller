import { useState } from 'react';
import { Link } from 'react-router-dom';
import { GodfatherSettings } from '@/components/settings/GodfatherSettings';
import { ProfileSettings } from '@/components/settings/ProfileSettings';
import { EmailSettings } from '@/components/settings/EmailSettings';
import { CalendarSettings } from '@/components/settings/CalendarSettings';
import { TwilioSettings } from '@/components/settings/TwilioSettings';
import { WorkPreferencesSettings } from '@/components/settings/WorkPreferences';
import { BudgetSettings } from '@/components/settings/BudgetSettings';
import { AIAutonomySettings } from '@/components/settings/AIAutonomySettings';
import { Card, CardContent } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import { 
  Settings2, 
  Link2, 
  User,
  Calendar,
  Mail,
  Phone,
  DollarSign,
  FileText,
  Star,
  ListTodo,
  ChevronRight
} from 'lucide-react';

type SettingsTab = 'integrations' | 'preferences' | 'account';

const tabs = [
  { id: 'integrations' as const, label: 'Integrations', icon: Link2, description: 'Connect services' },
  { id: 'preferences' as const, label: 'Preferences', icon: Settings2, description: 'Work & AI settings' },
  { id: 'account' as const, label: 'Account', icon: User, description: 'Your profile' },
];

// Admin/utility pages accessible from Settings
const adminPages = [
  { path: '/settings/calendar', label: 'Calendar View', icon: Calendar, description: 'View full calendar', color: 'bg-blue-500/20 text-blue-400' },
  { path: '/settings/tasks', label: 'All Tasks', icon: ListTodo, description: 'Browse all tasks', color: 'bg-purple-500/20 text-purple-400' },
  { path: '/settings/trusted', label: 'Trusted List', icon: Star, description: 'Manage trusted contacts', color: 'bg-amber-500/20 text-amber-400' },
  { path: '/settings/costs', label: 'Cost Monitoring', icon: DollarSign, description: 'AI spend & budgets', color: 'bg-emerald-500/20 text-emerald-400' },
  { path: '/settings/audit', label: 'Audit Log', icon: FileText, description: 'Activity history', color: 'bg-slate-500/20 text-slate-400' },
];

export const Settings = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('integrations');

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">Settings</h1>
        <p className="text-sm text-slate-400">
          Configure your AI assistant, connect services, and manage preferences
        </p>
      </div>

      {/* Quick Access - Admin Pages */}
      <div className="mb-6">
        <h2 className="text-sm font-medium text-slate-400 mb-3">Quick Access</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {adminPages.map((page) => {
            const Icon = page.icon;
            return (
              <Link
                key={page.path}
                to={page.path}
                className="flex items-center gap-3 p-3 bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 hover:border-slate-600 rounded-lg transition-all group"
              >
                <div className={`p-2 rounded-lg ${page.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{page.label}</p>
                  <p className="text-xs text-slate-500 truncate hidden sm:block">{page.description}</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors flex-shrink-0" />
              </Link>
            );
          })}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-slate-700 pb-3 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all whitespace-nowrap',
                activeTab === tab.id
                  ? 'bg-purple-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
            >
              <Icon className="w-4 h-4" />
              <div className="text-left">
                <div className="text-sm font-semibold">{tab.label}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'integrations' && (
          <>
            {/* Quick Status Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                      <Calendar className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">Calendar</h3>
                      <p className="text-xs text-slate-400">Schedule & events</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-red-500/20 rounded-lg">
                      <Mail className="w-5 h-5 text-red-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">Email</h3>
                      <p className="text-xs text-slate-400">Gmail & Outlook</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-500/20 rounded-lg">
                      <Phone className="w-5 h-5 text-green-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">Messaging</h3>
                      <p className="text-xs text-slate-400">SMS & WhatsApp</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
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
            <ProfileSettings />
            <GodfatherSettings />
          </>
        )}
      </div>
    </div>
  );
};

