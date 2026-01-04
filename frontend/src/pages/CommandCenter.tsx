import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  useTodayCommandCenter,
  useApproveAction,
  useDismissAction,
  useExecuteAction,
  useTriggerRelationshipRunSync,
} from '@/lib/hooks';
import {
  Loader2,
  Zap,
  MessageSquare,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Send,
  X,
  Play,
  RefreshCw,
  Users,
  Target,
  Heart,
  TrendingUp,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { useState } from 'react';

export const CommandCenter = () => {
  const { data, isLoading, error, refetch } = useTodayCommandCenter();
  const approveAction = useApproveAction();
  const dismissAction = useDismissAction();
  const executeAction = useExecuteAction();
  const triggerRun = useTriggerRelationshipRunSync();
  
  const [expandedAction, setExpandedAction] = useState<string | null>(null);
  const [editingDraft, setEditingDraft] = useState<string | null>(null);
  const [draftText, setDraftText] = useState('');

  const handleApproveAndSend = async (actionId: string) => {
    try {
      await approveAction.mutateAsync({ actionId });
      await executeAction.mutateAsync(actionId);
    } catch (e) {
      console.error('Failed to approve and send:', e);
    }
  };

  const handleDismiss = async (actionId: string) => {
    try {
      await dismissAction.mutateAsync({ actionId });
    } catch (e) {
      console.error('Failed to dismiss:', e);
    }
  };

  const handleTriggerRun = async (runType: 'morning' | 'midday' | 'afternoon' | 'evening') => {
    try {
      await triggerRun.mutateAsync({ runType, force: true });
    } catch (e) {
      console.error('Failed to trigger run:', e);
    }
  };

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'reply':
        return <MessageSquare className="w-4 h-4" />;
      case 'follow_up':
        return <Clock className="w-4 h-4" />;
      case 'check_in':
        return <Heart className="w-4 h-4" />;
      case 'value_first':
        return <Sparkles className="w-4 h-4" />;
      case 'intro':
        return <Users className="w-4 h-4" />;
      case 'project_leverage':
        return <Target className="w-4 h-4" />;
      default:
        return <Zap className="w-4 h-4" />;
    }
  };

  const getActionColor = (type: string, hasRisk: boolean) => {
    if (hasRisk) return 'border-red-500/50 bg-red-500/10';
    switch (type) {
      case 'reply':
        return 'border-blue-500/50 bg-blue-500/10';
      case 'value_first':
        return 'border-emerald-500/50 bg-emerald-500/10';
      case 'follow_up':
        return 'border-amber-500/50 bg-amber-500/10';
      default:
        return 'border-purple-500/50 bg-purple-500/10';
    }
  };

  const getPriorityLabel = (score: number) => {
    if (score >= 0.8) return { label: 'URGENT', color: 'text-red-400 bg-red-500/20' };
    if (score >= 0.6) return { label: 'HIGH', color: 'text-amber-400 bg-amber-500/20' };
    if (score >= 0.4) return { label: 'MEDIUM', color: 'text-blue-400 bg-blue-500/20' };
    return { label: 'LOW', color: 'text-slate-400 bg-slate-500/20' };
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
          <span className="ml-3 text-white/60">Loading Command Center...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="bg-red-900/20 border-red-500/50">
          <CardContent className="py-8 text-center">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-red-400 font-semibold mb-2">Failed to load Command Center</p>
            <Button variant="primary" onClick={() => refetch()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
              Today's Command Center
            </span>
            <Zap className="w-8 h-8 text-amber-400" />
          </h1>
          <p className="text-white/60">
            {format(new Date(), 'EEEE, MMMM d, yyyy')} • Your relationship ops at a glance
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <Card className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border-purple-500/30">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Target className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{data?.top_actions?.length || 0}</p>
                <p className="text-xs text-purple-300/80">Actions Today</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border-blue-500/30">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <MessageSquare className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{data?.must_reply_messages?.length || 0}</p>
                <p className="text-xs text-blue-300/80">Must Reply</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-900/50 to-amber-800/30 border-amber-500/30">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/20">
                <CheckCircle2 className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{data?.pending_approvals_count || 0}</p>
                <p className="text-xs text-amber-300/80">Pending Approvals</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-900/50 to-red-800/30 border-red-500/30">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/20">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{data?.at_risk_commitments?.length || 0}</p>
                <p className="text-xs text-red-300/80">At Risk</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-900/50 to-emerald-800/30 border-emerald-500/30">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/20">
                <Sparkles className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{data?.ai_ready_actions?.length || 0}</p>
                <p className="text-xs text-emerald-300/80">AI Ready</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Column - Top Actions */}
        <div className="lg:col-span-2 space-y-6">
          {/* Top Relationship Actions */}
          <Card className="bg-slate-900/50 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-400" />
                Top Relationship Actions
              </CardTitle>
              <Link to="/relationship-ops/runs">
                <Button variant="ghost" size="sm">
                  View All Runs <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {!data?.top_actions || data.top_actions.length === 0 ? (
                <div className="text-center py-8">
                  <Sparkles className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                  <p className="text-slate-400 mb-4">No actions yet. Trigger a run to generate recommendations.</p>
                  <div className="flex gap-2 justify-center flex-wrap">
                    {(['morning', 'midday', 'afternoon', 'evening'] as const).map((type) => (
                      <Button
                        key={type}
                        variant="secondary"
                        size="sm"
                        onClick={() => handleTriggerRun(type)}
                        disabled={triggerRun.isPending}
                      >
                        {triggerRun.isPending ? (
                          <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                        ) : (
                          <Play className="w-4 h-4 mr-1" />
                        )}
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                      </Button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {data.top_actions.map((action) => {
                    const priority = getPriorityLabel(action.priority_score);
                    const hasRisk = action.risk_flags && action.risk_flags.length > 0;
                    const isExpanded = expandedAction === action.id;

                    return (
                      <div
                        key={action.id}
                        className={`rounded-lg border p-4 transition-all ${getActionColor(action.type, hasRisk)}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3 flex-1">
                            <div className={`p-2 rounded-lg ${hasRisk ? 'bg-red-500/20' : 'bg-white/10'}`}>
                              {getActionIcon(action.type)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`text-xs font-semibold px-2 py-0.5 rounded ${priority.color}`}>
                                  {priority.label}
                                </span>
                                <span className="text-xs text-white/60 uppercase">
                                  {action.type.replace('_', ' ')}
                                </span>
                                {hasRisk && (
                                  <span className="text-xs text-red-400 flex items-center gap-1">
                                    <AlertTriangle className="w-3 h-3" />
                                    Trust Risk
                                  </span>
                                )}
                              </div>
                              <p className="text-white font-medium mb-1">
                                {action.contact_name || 'Unknown Contact'}
                              </p>
                              <p className="text-sm text-white/70 line-clamp-2">
                                {action.description}
                              </p>
                              
                              {/* Expandable Draft Section */}
                              {action.draft_message && (
                                <button
                                  onClick={() => setExpandedAction(isExpanded ? null : action.id)}
                                  className="text-xs text-purple-400 hover:text-purple-300 mt-2 flex items-center gap-1"
                                >
                                  {isExpanded ? 'Hide' : 'Show'} Draft
                                  <ArrowRight className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                                </button>
                              )}
                              
                              {isExpanded && action.draft_message && (
                                <div className="mt-3 p-3 bg-slate-800/50 rounded-lg">
                                  <p className="text-xs text-slate-400 mb-1">
                                    Draft via {action.draft_channel?.toUpperCase() || 'SMS'}:
                                  </p>
                                  <p className="text-sm text-white whitespace-pre-wrap">
                                    {action.draft_message}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Action Buttons */}
                          <div className="flex items-center gap-2 ml-4">
                            {action.draft_message && (
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleApproveAndSend(action.id)}
                                disabled={approveAction.isPending || executeAction.isPending}
                              >
                                {(approveAction.isPending || executeAction.isPending) ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <>
                                    <Send className="w-4 h-4 mr-1" />
                                    Send
                                  </>
                                )}
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDismiss(action.id)}
                              disabled={dismissAction.isPending}
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* At-Risk Commitments */}
          {data?.at_risk_commitments && data.at_risk_commitments.length > 0 && (
            <Card className="bg-slate-900/50 border-red-500/30">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  At-Risk Commitments
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {data.at_risk_commitments.map((commitment) => (
                    <div
                      key={commitment.id}
                      className="bg-red-900/20 border border-red-500/30 rounded-lg p-4"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-white font-medium">{commitment.contact_name}</p>
                          <p className="text-sm text-white/70 mt-1">{commitment.description}</p>
                          {commitment.deadline && (
                            <p className="text-xs text-red-400 mt-2">
                              Due: {format(new Date(commitment.deadline), 'MMM d, h:mm a')}
                            </p>
                          )}
                        </div>
                        <span className={`text-xs px-2 py-1 rounded ${
                          commitment.status === 'overdue' 
                            ? 'bg-red-500/20 text-red-400' 
                            : 'bg-amber-500/20 text-amber-400'
                        }`}>
                          {commitment.status.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Today's Runs */}
          <Card className="bg-slate-900/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Calendar className="w-5 h-5 text-blue-400" />
                Today's Runs
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!data?.today_runs || data.today_runs.length === 0 ? (
                <p className="text-slate-400 text-sm">No runs completed today</p>
              ) : (
                <div className="space-y-3">
                  {data.today_runs.map((run) => (
                    <Link
                      key={run.id}
                      to={`/relationship-ops/runs/${run.id}`}
                      className="block bg-slate-800/50 rounded-lg p-3 hover:bg-slate-700/50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-white">{run.title}</span>
                        <span className="text-xs text-slate-400">
                          {run.completed_at && formatDistanceToNow(new Date(run.completed_at), { addSuffix: true })}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2">{run.summary}</p>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Must Reply Messages */}
          {data?.must_reply_messages && data.must_reply_messages.length > 0 && (
            <Card className="bg-slate-900/50 border-blue-500/30">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-400" />
                  Must Reply
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {data.must_reply_messages.slice(0, 5).map((msg) => (
                    <Link
                      key={msg.id}
                      to={`/messaging?contact=${msg.contact_id}`}
                      className="block bg-slate-800/50 rounded-lg p-3 hover:bg-slate-700/50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-white">{msg.contact_name}</span>
                        <span className="text-xs text-blue-400 uppercase">{msg.channel}</span>
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

          {/* Quick Actions */}
          <Card className="bg-slate-900/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-400" />
                Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link to="/contacts" className="block">
                <Button variant="secondary" className="w-full justify-start">
                  <Users className="w-4 h-4 mr-2" />
                  View All Contacts
                </Button>
              </Link>
              <Link to="/projects" className="block">
                <Button variant="secondary" className="w-full justify-start">
                  <Target className="w-4 h-4 mr-2" />
                  View Projects
                </Button>
              </Link>
              <Link to="/messaging" className="block">
                <Button variant="secondary" className="w-full justify-start">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Open Messaging
                </Button>
              </Link>
              <Link to="/approvals" className="block">
                <Button variant="secondary" className="w-full justify-start">
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Review Approvals
                  {data?.pending_approvals_count && data.pending_approvals_count > 0 && (
                    <span className="ml-auto bg-amber-500 text-white text-xs font-bold rounded-full px-2 py-0.5">
                      {data.pending_approvals_count}
                    </span>
                  )}
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};


