import { Link, useLocation } from 'react-router-dom';
import { Phone, Calendar, Inbox, CheckCircle2, DollarSign, Settings, FolderKanban } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTasks } from '@/lib/hooks';

// Keep mobile nav focused on essential daily-use items
const navItems = [
  { path: '/', label: 'Home', icon: Phone },
  { path: '/daily-plan', label: 'Today', icon: Calendar },
  { path: '/messaging', label: 'Inbox', icon: Inbox },
  { path: '/projects', label: 'Projects', icon: FolderKanban },
  { path: '/approvals', label: 'Approve', icon: CheckCircle2, showBadge: true },
  { path: '/cost', label: 'Costs', icon: DollarSign },
  { path: '/settings', label: 'More', icon: Settings },
];

export const BottomNav = () => {
  const location = useLocation();
  const { data: tasks = [] } = useTasks();
  const pendingApprovals = tasks.filter(t => t.status === 'awaiting_confirmation').length;

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-sm border-t border-slate-700 shadow-lg z-50 lg:hidden safe-area-inset-bottom">
      <div className="max-w-7xl mx-auto px-1">
        <div className="flex justify-around items-center h-16">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            const showBadge = item.showBadge && pendingApprovals > 0;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'flex flex-col items-center justify-center flex-1 h-full transition-colors min-w-0 relative',
                  'hover:bg-slate-800/50 active:bg-slate-700/50',
                  isActive ? 'text-purple-400' : 'text-slate-400'
                )}
              >
                <Icon className={cn('w-5 h-5 mb-0.5 flex-shrink-0', isActive && 'text-purple-400')} />
                <span className={cn('text-[10px] font-medium truncate w-full text-center px-0.5', isActive && 'text-purple-400')}>
                  {item.label}
                </span>
                {showBadge && (
                  <span className="absolute top-1 right-1/4 w-4 h-4 bg-amber-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center animate-pulse">
                    {pendingApprovals > 9 ? '9+' : pendingApprovals}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

