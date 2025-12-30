import { useDailyPlan, useScheduleTask, useExecuteAITask, useScheduleAllTasks, useCostSummary, useTasks } from '@/lib/hooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Loader2, Calendar, Sparkles, AlertTriangle, Clock, RefreshCw, DollarSign, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { Link } from 'react-router-dom';

export const DailyPlan = () => {
  const { data: plan, isLoading, error, refetch } = useDailyPlan();
  const scheduleTask = useScheduleTask();
  const executeAI = useExecuteAITask();
  const scheduleAll = useScheduleAllTasks();
  const { data: costSummary } = useCostSummary('day');
  const { data: tasks = [] } = useTasks();
  const pendingApprovals = tasks.filter((t) => t.status === 'awaiting_confirmation');

  const handleSchedule = async (taskId: string) => {
    try {
      const result = await scheduleTask.mutateAsync(taskId);
      if (result.success) {
        toast.success('Task scheduled successfully');
      } else {
        toast.error(result.error || 'Failed to schedule task');
      }
    } catch (error: unknown) {
      const axiosErr = error as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr.response?.data?.detail || 'Failed to schedule task');
    }
  };

  const handleExecuteAI = async (taskId: string) => {
    try {
      const result = await executeAI.mutateAsync(taskId);
      if (result.success) {
        toast.success('AI task execution started');
      } else {
        toast.error(result.error || 'Failed to execute task');
      }
    } catch (error: unknown) {
      const axiosErr = error as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr.response?.data?.detail || 'Failed to execute task');
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-red-600 font-semibold mb-2">Failed to load daily plan</p>
            <Button onClick={() => refetch()} variant="primary" size="sm">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleRescheduleDay = async () => {
    try {
      const result = await scheduleAll.mutateAsync(true);
      if (result.success) {
        toast.success(`Rescheduled ${result.scheduled} tasks`);
        refetch();
      } else {
        toast.error(result.error || 'Failed to reschedule');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to reschedule day');
    }
  };

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
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Today</h1>
          <p className="text-white/80">
            {new Date(plan.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <Button
          onClick={handleRescheduleDay}
          disabled={scheduleAll.isPending}
          variant="secondary"
        >
          {scheduleAll.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Reschedule My Day
        </Button>
      </div>

      {/* Quick Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Cost Summary */}
        {costSummary && (
          <Card className="bg-slate-900/50 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <DollarSign className="w-5 h-5 text-emerald-400" />
                <div className="flex-1">
                  <p className="text-xs text-slate-400">Today's Spend</p>
                  <p className="text-xl font-bold text-white">
                    {formatCurrency(costSummary.total_cost)}
                  </p>
                </div>
                <Link to="/cost">
                  <Button variant="ghost" size="sm">
                    View
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Pending Approvals */}
        {pendingApprovals.length > 0 && (
          <Card className="bg-slate-900/50 border-slate-700 border-amber-500/30">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-amber-400" />
                <div className="flex-1">
                  <p className="text-xs text-slate-400">Pending Approvals</p>
                  <p className="text-xl font-bold text-amber-400">
                    {pendingApprovals.length}
                  </p>
                </div>
                <Link to="/approvals">
                  <Button variant="secondary" size="sm">
                    Review
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Scheduled Count */}
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-blue-400" />
              <div className="flex-1">
                <p className="text-xs text-slate-400">Scheduled Tasks</p>
                <p className="text-xl font-bold text-white">
                  {plan.scheduled_tasks.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scheduled Tasks */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Scheduled Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            {plan.scheduled_tasks.length === 0 ? (
              <p className="text-gray-500 text-sm">No tasks scheduled for today</p>
            ) : (
              <div className="space-y-3">
                {plan.scheduled_tasks.map((task) => (
                  <div key={task.task_id} className="p-3 bg-gray-800 rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold text-white">{task.title}</h4>
                      {task.execution_mode !== 'HUMAN' && (
                        <span className="px-2 py-1 rounded text-xs bg-purple-500/20 text-purple-400">
                          {task.execution_mode}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-white/60">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(task.start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })} - {new Date(task.end).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                      </span>
                      {task.estimated_minutes && (
                        <span>{task.estimated_minutes}m</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* High Priority Unscheduled */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-400" />
              High Priority (Unscheduled)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {plan.unscheduled_high_priority.length === 0 ? (
              <p className="text-gray-500 text-sm">No high-priority unscheduled tasks</p>
            ) : (
              <div className="space-y-3">
                {plan.unscheduled_high_priority.map((task) => (
                  <div key={task.task_id} className="p-3 bg-gray-800 rounded-lg flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-white mb-1">{task.title}</h4>
                      <div className="flex items-center gap-3 text-xs text-white/60">
                        <span>Priority: {task.priority}</span>
                        {task.due_at && (
                          <span>Due: {new Date(task.due_at).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                    <Button
                      onClick={() => handleSchedule(task.task_id)}
                      variant="secondary"
                      size="sm"
                      disabled={scheduleTask.isPending}
                    >
                      {scheduleTask.isPending ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Calendar className="w-3 h-3" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Executable Tasks */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-400" />
              AI Can Do Now
            </CardTitle>
          </CardHeader>
          <CardContent>
            {plan.ai_executable_tasks.length === 0 ? (
              <p className="text-gray-500 text-sm">No AI-executable tasks available</p>
            ) : (
              <div className="space-y-3">
                {plan.ai_executable_tasks.map((task) => (
                  <div key={task.task_id} className="p-3 bg-gray-800 rounded-lg flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-white mb-1">{task.title}</h4>
                      {task.description && (
                        <p className="text-xs text-white/60 line-clamp-2">{task.description}</p>
                      )}
                    </div>
                    <Button
                      onClick={() => handleExecuteAI(task.task_id)}
                      variant="primary"
                      size="sm"
                      disabled={executeAI.isPending}
                    >
                      {executeAI.isPending ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Sparkles className="w-3 h-3" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* At Risk Tasks */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              At Risk
            </CardTitle>
          </CardHeader>
          <CardContent>
            {plan.at_risk_tasks.length === 0 ? (
              <p className="text-gray-500 text-sm">No tasks at risk</p>
            ) : (
              <div className="space-y-3">
                {plan.at_risk_tasks.map((task) => (
                  <div key={task.task_id} className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <h4 className="font-semibold text-white mb-1">{task.title}</h4>
                    <div className="flex items-center gap-3 text-xs text-red-400">
                      <span>Due: {new Date(task.due_at).toLocaleDateString()}</span>
                      {task.deadline_type === 'HARD' && (
                        <span className="px-2 py-1 rounded bg-red-500/20">Hard Deadline</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

