import { Link, useLocation } from 'react-router-dom';
import { Phone, Calendar, Settings, ListTodo, Users, Inbox, FolderKanban, Sparkles, DollarSign, CheckCircle2, Star, FileText, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTasks } from '@/lib/hooks';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  showBadge?: boolean;
  highlight?: boolean;
}

const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: Phone },
  { path: '/command-center', label: 'Command', icon: Zap, highlight: true },
  { path: '/projects', label: 'Projects', icon: FolderKanban },
  { path: '/daily-plan', label: 'Today', icon: Sparkles },
  { path: '/tasks', label: 'Tasks', icon: ListTodo },
  { path: '/calendar', label: 'Calendar', icon: Calendar },
  { path: '/messaging', label: 'Inbox', icon: Inbox },
  { path: '/contacts', label: 'Contacts', icon: Users },
  { path: '/trusted-list', label: 'Trusted', icon: Star },
  { path: '/cost', label: 'Costs', icon: DollarSign },
  { path: '/approvals', label: 'Approvals', icon: CheckCircle2, showBadge: true },
  { path: '/audit-log', label: 'Audit Log', icon: FileText },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Navbar = () => {
  const location = useLocation();
  const { data: tasks = [] } = useTasks();
  const pendingApprovals = tasks.filter(t => t.status === 'awaiting_confirmation').length;

  return (
    <nav className="bg-slate-900/95 backdrop-blur-sm border-b border-slate-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
                AI Caller
              </h1>
            </div>
            <div className="hidden lg:ml-6 lg:flex lg:space-x-2 overflow-x-auto">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                const showBadge = item.showBadge && pendingApprovals > 0;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'inline-flex items-center px-2 pt-1 border-b-2 text-sm font-medium transition-colors relative whitespace-nowrap',
                      isActive
                        ? 'border-purple-500 text-purple-400'
                        : item.highlight
                        ? 'border-transparent text-amber-400 hover:text-amber-300 hover:border-amber-500'
                        : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-500'
                    )}
                  >
                    <Icon className={cn("w-4 h-4 mr-1.5", item.highlight && !isActive && "text-amber-400")} />
                    {item.label}
                    {showBadge && (
                      <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                        {pendingApprovals > 9 ? '9+' : pendingApprovals}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};
