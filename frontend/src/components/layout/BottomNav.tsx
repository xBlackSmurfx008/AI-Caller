import { Link, useLocation } from 'react-router-dom';
import { Sun, MessageSquare, Users, FolderKanban, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

// Streamlined mobile nav - 5 core items for thumb reach
const navItems = [
  { path: '/', label: 'Today', icon: Sun },
  { path: '/messaging', label: 'Messages', icon: MessageSquare },
  { path: '/contacts', label: 'People', icon: Users },
  { path: '/projects', label: 'Projects', icon: FolderKanban },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const BottomNav = () => {
  const location = useLocation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-slate-900/98 backdrop-blur-md border-t border-slate-700/50 shadow-2xl z-50 lg:hidden safe-area-inset-bottom">
      <div className="max-w-md mx-auto px-2">
        <div className="flex justify-around items-center h-16">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || 
              (item.path === '/' && ['/', '/dashboard', '/daily-plan', '/command-center'].includes(location.pathname));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'flex flex-col items-center justify-center flex-1 h-full transition-all duration-200 min-w-0 relative',
                  isActive 
                    ? 'text-white' 
                    : 'text-slate-500 hover:text-slate-300 active:text-slate-200'
                )}
              >
                <div className={cn(
                  'p-1.5 rounded-xl transition-all duration-200',
                  isActive && 'bg-purple-500/20'
                )}>
                  <Icon className={cn(
                    'w-5 h-5 transition-all duration-200', 
                    isActive && 'text-purple-400 scale-110'
                  )} />
                </div>
                <span className={cn(
                  'text-[10px] font-medium mt-0.5 transition-all duration-200',
                  isActive ? 'text-purple-400' : 'text-slate-500'
                )}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

