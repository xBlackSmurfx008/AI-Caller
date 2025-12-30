import { Link } from 'react-router-dom';
import { TaskInput } from '@/components/tasks/TaskInput';
import { TaskList } from '@/components/tasks/TaskList';
import { CalendarStatus } from '@/components/calendar/CalendarStatus';
import { CalendarEvents } from '@/components/calendar/CalendarEvents';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useDailyPlan, useCostSummary, useTasks } from '@/lib/hooks';
import { Loader2, Calendar, DollarSign, CheckCircle2, ArrowRight, Sparkles } from 'lucide-react';

export const Dashboard = () => {
  const { data: dailyPlan } = useDailyPlan();
  const { data: costSummary } = useCostSummary('day');
  const { data: tasks = [] } = useTasks();
  const pendingApprovals = tasks.filter((t) => t.status === 'awaiting_confirmation');

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-white/80">
          Your command center for tasks, calendar, and AI assistant
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Link to="/daily-plan">
          <Card className="bg-slate-900/50 border-slate-700 hover:border-purple-500/50 transition-colors cursor-pointer">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-blue-400" />
                <div className="flex-1">
                  <p className="text-xs text-slate-400">Scheduled Today</p>
                  <p className="text-xl font-bold text-white">
                    {dailyPlan?.scheduled_tasks.length || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>

        {costSummary && (
          <Link to="/cost">
            <Card className="bg-slate-900/50 border-slate-700 hover:border-purple-500/50 transition-colors cursor-pointer">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <DollarSign className="w-5 h-5 text-emerald-400" />
                  <div className="flex-1">
                    <p className="text-xs text-slate-400">Today's Spend</p>
                    <p className="text-xl font-bold text-white">
                      {formatCurrency(costSummary.total_cost)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        )}

        {pendingApprovals.length > 0 && (
          <Link to="/approvals">
            <Card className="bg-slate-900/50 border-slate-700 border-amber-500/30 hover:border-amber-500/50 transition-colors cursor-pointer">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-amber-400" />
                  <div className="flex-1">
                    <p className="text-xs text-slate-400">Pending Approvals</p>
                    <p className="text-xl font-bold text-amber-400">
                      {pendingApprovals.length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        )}

        <Link to="/projects">
          <Card className="bg-slate-900/50 border-slate-700 hover:border-purple-500/50 transition-colors cursor-pointer">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <div className="flex-1">
                  <p className="text-xs text-slate-400">Active Projects</p>
                  <p className="text-xl font-bold text-white">—</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="mb-6 flex flex-wrap gap-2">
        <Link to="/daily-plan">
          <Button variant="secondary" size="sm">
            View Today's Plan
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </Link>
        <Link to="/projects">
          <Button variant="secondary" size="sm">
            Manage Projects
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </Link>
        {pendingApprovals.length > 0 && (
          <Link to="/approvals">
            <Button variant="primary" size="sm">
              Review {pendingApprovals.length} Approval{pendingApprovals.length !== 1 ? 's' : ''}
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2">
          <TaskInput />
        </div>
        <div>
          <CalendarStatus />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-white mb-4">Recent Tasks</h2>
            <TaskList />
          </div>
        </div>
        <div>
          <CalendarEvents />
        </div>
      </div>
    </div>
  );
};

