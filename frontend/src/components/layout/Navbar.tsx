import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Sun, MessageSquare, Users, FolderKanban, CheckCircle2, Settings, LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTasks } from '@/lib/hooks';
import { useAuth } from '@/lib/AuthContext';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  showBadge?: boolean;
}

// Streamlined desktop nav - mirrors mobile for consistency
const navItems: NavItem[] = [
  { path: '/', label: 'Today', icon: Sun },
  { path: '/messaging', label: 'Messages', icon: MessageSquare },
  { path: '/contacts', label: 'People', icon: Users },
  { path: '/projects', label: 'Projects', icon: FolderKanban },
  { path: '/approvals', label: 'Approvals', icon: CheckCircle2, showBadge: true },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { signOut, userEmail } = useAuth();
  const { data: tasks = [] } = useTasks();
  const pendingApprovals = tasks.filter(t => t.status === 'awaiting_confirmation').length;

  const handleLogout = () => {
    signOut();
    navigate('/login');
  };

  return (
    <nav className="bg-slate-900/98 backdrop-blur-md border-b border-slate-700/50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-14">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center mr-8">
              <h1 className="text-lg font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent">
                AI Caller
              </h1>
            </Link>
            <div className="hidden lg:flex lg:space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path ||
                  (item.path === '/' && ['/', '/dashboard', '/daily-plan', '/command-center'].includes(location.pathname));
                const showBadge = item.showBadge && pendingApprovals > 0;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 relative',
                      isActive
                        ? 'bg-purple-500/20 text-purple-400'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                    )}
                  >
                    <Icon className="w-4 h-4 mr-1.5" />
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
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500 hidden md:block truncate max-w-[150px]">
              {userEmail || ''}
            </span>
            <button
              onClick={handleLogout}
              className="inline-flex items-center px-2.5 py-1.5 text-sm font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all duration-200"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline ml-1.5">Sign out</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};
