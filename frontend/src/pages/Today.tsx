import { useState } from 'react';
import { Link } from 'react-router-dom';
import { TaskIntaker } from '@/components/tasks/TaskIntaker';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  useDailyPlan,
  useCostSummary,
  useTasks,
  useScheduleTask,
  useExecuteAITask,
  useScheduleAllTasks,
  useTodayCommandCenter,
  useApproveAction,
  useDismissAction,
  useCalendarEvents,
} from '@/lib/hooks';
import {
  Loader2,
  Calendar,
  Sparkles,
  AlertTriangle,
  Clock,
  RefreshCw,
  DollarSign,
  CheckCircle2,
  MessageSquare,
  Send,
  X,
  Users,
  Target,
  ArrowRight,
  Inbox,
  Zap,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

export const Today = () => {
  // Core data
  const { data: plan, isLoading: planLoading, refetch: refetchPlan } = useDailyPlan();
  const { data: costSummary } = useCostSummary('day');
  const { data: tasks = [] } = useTasks();
  const { data: commandCenter, refetch: refetchCC } = useTodayCommandCenter();
  const { data: calendarData } = useCalendarEvents(5);
  
  // Mutations
  const scheduleTask = useScheduleTask();
  const executeAI = useExecuteAITask();
  const scheduleAll = useScheduleAllTasks();
  const approveAction = useApproveAction();
  const dismissAction = useDismissAction();

  // Local state
  const [expandedAction, setExpandedAction] = useState<string | null>(null);

  const pendingApprovals = tasks.filter((t) => t.status === 'awaiting_confirmation');
  const calendarEvents = calendarData?.events || [];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const handleRescheduleDay = async () => {
    try {
      const result = await scheduleAll.mutateAsync(true);
      if (result.success) {
        toast.success(`Rescheduled ${result.scheduled} tasks`);
        refetchPlan();
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to reschedule day');
    }
  };

  const handleSchedule = async (taskId: string) => {
    try {
      const result = await scheduleTask.mutateAsync(taskId);
      if (result.success) {
        toast.success('Task scheduled');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to schedule');
    }
  };

  const handleExecuteAI = async (taskId: string) => {
    try {
      const result = await executeAI.mutateAsync(taskId);
      if (result.success) {
        toast.success('AI task started');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to execute');
    }
  };

  const handleApproveAndSend = async (actionId: string) => {
    try {
      await approveAction.mutateAsync({ actionId });
      toast.success('Action approved and sent');
    } catch (e) {
      toast.error('Failed to approve');
    }
  };

  const handleDismiss = async (actionId: string) => {
    try {
      await dismissAction.mutateAsync({ actionId });
      toast.success('Dismissed');
    } catch (e) {
      toast.error('Failed to dismiss');
    }
  };

  const getPriorityColor = (score: number) => {
    if (score >= 0.8) return 'text-red-400 bg-red-500/20';
    if (score >= 0.6) return 'text-amber-400 bg-amber-500/20';
    return 'text-blue-400 bg-blue-500/20';
  };

  if (planLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
          <span className="ml-3 text-white/60">Loading your day...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Today</h1>
          <p className="text-white/60 text-sm">
            {format(new Date(), 'EEEE, MMMM d, yyyy')}
          </p>
        </div>
        <Button
          onClick={handleRescheduleDay}
          disabled={scheduleAll.isPending}
          variant="secondary"
          size="sm"
        >
          {scheduleAll.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Reschedule Day
        </Button>
      </div>

      {/* AI Command Bar */}
      <TaskIntaker />

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="bg-slate-900/60 border-slate-700/50">
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-blue-400" />
              <div>
                <p className="text-xs text-slate-400">Scheduled</p>
                <p className="text-xl font-bold text-white">
                  {plan?.scheduled_tasks?.length || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {costSummary && (
          <Link to="/settings/costs">
            <Card className="bg-slate-900/60 border-slate-700/50 hover:border-emerald-500/40 transition-colors cursor-pointer">
              <CardContent className="pt-4 pb-3">
                <div className="flex items-center gap-3">
                  <DollarSign className="w-5 h-5 text-emerald-400" />
                  <div>
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

        <Link to="/approvals">
          <Card className={`bg-slate-900/60 border-slate-700/50 hover:border-amber-500/40 transition-colors cursor-pointer ${pendingApprovals.length > 0 ? 'border-amber-500/30' : ''}`}>
            <CardContent className="pt-4 pb-3">
              <div className="flex items-center gap-3">
                <CheckCircle2 className={`w-5 h-5 ${pendingApprovals.length > 0 ? 'text-amber-400' : 'text-slate-400'}`} />
                <div>
                  <p className="text-xs text-slate-400">Approvals</p>
                  <p className={`text-xl font-bold ${pendingApprovals.length > 0 ? 'text-amber-400' : 'text-white'}`}>
                    {pendingApprovals.length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link to="/messaging">
          <Card className="bg-slate-900/60 border-slate-700/50 hover:border-blue-500/40 transition-colors cursor-pointer">
            <CardContent className="pt-4 pb-3">
              <div className="flex items-center gap-3">
                <Inbox className="w-5 h-5 text-blue-400" />
                <div>
                  <p className="text-xs text-slate-400">Messages</p>
                  <p className="text-xl font-bold text-white">
                    {commandCenter?.must_reply_messages?.length || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Schedule & Actions */}
        <div className="lg:col-span-2 space-y-6">
          {/* Today's Schedule */}
          <Card className="bg-slate-900/60 border-slate-700/50">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-white flex items-center gap-2 text-lg">
                <Calendar className="w-5 h-5 text-blue-400" />
                Today's Schedule
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!plan?.scheduled_tasks || plan.scheduled_tasks.length === 0 ? (
                <p className="text-slate-400 text-sm py-4">No tasks scheduled for today</p>
              ) : (
                <div className="space-y-2">
                  {plan.scheduled_tasks.slice(0, 6).map((task) => (
                    <div key={task.task_id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-white truncate">{task.title}</h4>
                        <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {format(new Date(task.start), 'h:mm a')} - {format(new Date(task.end), 'h:mm a')}
                          </span>
                          {task.execution_mode !== 'HUMAN' && (
                            <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400">
                              {task.execution_mode}
                            </span>
                          )}
                        </div>
                      </div>
                      {task.execution_mode !== 'HUMAN' && (
                        <Button
                          onClick={() => handleExecuteAI(task.task_id)}
                          variant="ghost"
                          size="sm"
                          disabled={executeAI.isPending}
                        >
                          <Sparkles className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Relationship Actions */}
          {commandCenter?.top_actions && commandCenter.top_actions.length > 0 && (
            <Card className="bg-slate-900/60 border-slate-700/50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-white flex items-center gap-2 text-lg">
                  <Target className="w-5 h-5 text-purple-400" />
                  Relationship Actions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {commandCenter.top_actions.slice(0, 5).map((action) => {
                    const hasRisk = action.risk_flags && action.risk_flags.length > 0;
                    const isExpanded = expandedAction === action.id;

                    return (
                      <div
                        key={action.id}
                        className={`rounded-lg border p-4 transition-all ${
                          hasRisk 
                            ? 'border-red-500/40 bg-red-500/10' 
                            : 'border-slate-600 bg-slate-800/50'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1 flex-wrap">
                              <span className={`text-xs font-semibold px-2 py-0.5 rounded ${getPriorityColor(action.priority_score)}`}>
                                {action.type.replace('_', ' ').toUpperCase()}
                              </span>
                              {hasRisk && (
                                <span className="text-xs text-red-400 flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" />
                                  Risk
                                </span>
                              )}
                            </div>
                            <p className="text-white font-medium">
                              {action.contact_name || 'Unknown'}
                            </p>
                            <p className="text-sm text-slate-400 line-clamp-2 mt-1">
                              {action.description}
                            </p>
                            
                            {action.draft_message && (
                              <>
                                <button
                                  onClick={() => setExpandedAction(isExpanded ? null : action.id)}
                                  className="text-xs text-purple-400 hover:text-purple-300 mt-2"
                                >
                                  {isExpanded ? 'Hide' : 'Show'} Draft
                                </button>
                                
                                {isExpanded && (
                                  <div className="mt-2 p-3 bg-slate-700/50 rounded-lg">
                                    <p className="text-xs text-slate-400 mb-1">
                                      via {action.draft_channel?.toUpperCase() || 'SMS'}:
                                    </p>
                                    <p className="text-sm text-white whitespace-pre-wrap">
                                      {action.draft_message}
                                    </p>
                                  </div>
                                )}
                              </>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            {action.draft_message && (
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleApproveAndSend(action.id)}
                                disabled={approveAction.isPending}
                              >
                                <Send className="w-3 h-3" />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDismiss(action.id)}
                              disabled={dismissAction.isPending}
                            >
                              <X className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* High Priority Unscheduled */}
          {plan?.unscheduled_high_priority && plan.unscheduled_high_priority.length > 0 && (
            <Card className="bg-slate-900/60 border-amber-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-white flex items-center gap-2 text-lg">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  High Priority (Unscheduled)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {plan.unscheduled_high_priority.slice(0, 4).map((task) => (
                    <div key={task.task_id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div>
                        <h4 className="font-medium text-white">{task.title}</h4>
                        <p className="text-xs text-slate-400 mt-1">
                          Priority: {task.priority} {task.due_at && `• Due: ${format(new Date(task.due_at), 'MMM d')}`}
                        </p>
                      </div>
                      <Button
                        onClick={() => handleSchedule(task.task_id)}
                        variant="secondary"
                        size="sm"
                        disabled={scheduleTask.isPending}
                      >
                        <Calendar className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-6">
          {/* Calendar Events */}
          {calendarEvents.length > 0 && (
            <Card className="bg-slate-900/60 border-slate-700/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-white flex items-center gap-2 text-lg">
                  <Calendar className="w-5 h-5 text-indigo-400" />
                  Upcoming Events
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {calendarEvents.slice(0, 4).map((event) => {
                    const eventStart = event.start.dateTime || event.start.date;
                    return (
                      <div key={event.id} className="p-3 bg-slate-800/50 rounded-lg">
                        <h4 className="font-medium text-white text-sm truncate">{event.summary}</h4>
                        {eventStart && (
                          <p className="text-xs text-slate-400 mt-1">
                            {format(new Date(eventStart), 'h:mm a')}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Must Reply */}
          {commandCenter?.must_reply_messages && commandCenter.must_reply_messages.length > 0 && (
            <Card className="bg-slate-900/60 border-blue-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-white flex items-center gap-2 text-lg">
                  <MessageSquare className="w-5 h-5 text-blue-400" />
                  Must Reply
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {commandCenter.must_reply_messages.slice(0, 4).map((msg) => (
                    <Link
                      key={msg.id}
                      to={`/messaging?contact=${msg.contact_id}`}
                      className="block p-3 bg-slate-800/50 rounded-lg hover:bg-slate-700/50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-white truncate">{msg.contact_name}</span>
                        <span className="text-xs text-blue-400 uppercase flex-shrink-0">{msg.channel}</span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2">{msg.preview}</p>
                      <p className="text-xs text-slate-500 mt-1">
                        {formatDistanceToNow(new Date(msg.timestamp), { addSuffix: true })}
                      </p>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* AI Can Execute */}
          {plan?.ai_executable_tasks && plan.ai_executable_tasks.length > 0 && (
            <Card className="bg-slate-900/60 border-purple-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-white flex items-center gap-2 text-lg">
                  <Sparkles className="w-5 h-5 text-purple-400" />
                  AI Can Do Now
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {plan.ai_executable_tasks.slice(0, 4).map((task) => (
                    <div key={task.task_id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-white text-sm truncate">{task.title}</h4>
                      </div>
                      <Button
                        onClick={() => handleExecuteAI(task.task_id)}
                        variant="primary"
                        size="sm"
                        disabled={executeAI.isPending}
                      >
                        <Sparkles className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Quick Links */}
          <Card className="bg-slate-900/60 border-slate-700/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-white flex items-center gap-2 text-lg">
                <Zap className="w-5 h-5 text-amber-400" />
                Quick Access
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link to="/contacts" className="block">
                <Button variant="ghost" className="w-full justify-start text-slate-300 hover:text-white">
                  <Users className="w-4 h-4 mr-2" />
                  Contacts
                </Button>
              </Link>
              <Link to="/projects" className="block">
                <Button variant="ghost" className="w-full justify-start text-slate-300 hover:text-white">
                  <Target className="w-4 h-4 mr-2" />
                  Projects
                </Button>
              </Link>
              <Link to="/messaging" className="block">
                <Button variant="ghost" className="w-full justify-start text-slate-300 hover:text-white">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Messaging
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

