import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useRelationshipRun, useApproveAction, useDismissAction, useExecuteAction } from '@/lib/hooks';
import {
  Loader2,
  ArrowLeft,
  CheckCircle2,
  Clock,
  MessageSquare,
  AlertTriangle,
  Users,
  Sparkles,
  Target,
  Heart,
  Send,
  X,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { format } from 'date-fns';
import { useState } from 'react';

export const RelationshipOpsRun = () => {
  const { runId } = useParams<{ runId: string }>();
  const { data: run, isLoading, error } = useRelationshipRun(runId);
  const approveAction = useApproveAction();
  const dismissAction = useDismissAction();
  const executeAction = useExecuteAction();
  
  const [expandedSection, setExpandedSection] = useState<string | null>('top_actions');

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

  const getRunTypeConfig = (runType: string) => {
    switch (runType) {
      case 'morning':
        return {
          title: 'Morning Command Plan',
          icon: '🌅',
          color: 'from-orange-500/20 to-amber-500/10',
          borderColor: 'border-orange-500/30',
        };
      case 'midday':
        return {
          title: 'Midday Momentum Push',
          icon: '☀️',
          color: 'from-yellow-500/20 to-amber-500/10',
          borderColor: 'border-yellow-500/30',
        };
      case 'afternoon':
        return {
          title: 'Afternoon Coordination',
          icon: '🌤️',
          color: 'from-blue-500/20 to-purple-500/10',
          borderColor: 'border-blue-500/30',
        };
      case 'evening':
        return {
          title: 'Relationship Review',
          icon: '🌙',
          color: 'from-purple-500/20 to-indigo-500/10',
          borderColor: 'border-purple-500/30',
        };
      default:
        return {
          title: 'Relationship Ops Run',
          icon: '⚡',
          color: 'from-slate-500/20 to-slate-500/10',
          borderColor: 'border-slate-500/30',
        };
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
        </div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="bg-red-900/20 border-red-500/50">
          <CardContent className="py-8 text-center">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-red-400 font-semibold mb-4">Run not found</p>
            <Link to="/command-center">
              <Button variant="primary">Back to Command Center</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const config = getRunTypeConfig(run.run_type);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Link */}
      <Link to="/command-center" className="inline-flex items-center text-white/60 hover:text-white mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Command Center
      </Link>

      {/* Header Card */}
      <Card className={`mb-8 bg-gradient-to-r ${config.color} ${config.borderColor}`}>
        <CardContent className="py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">{config.icon}</span>
                <h1 className="text-2xl font-bold text-white">{config.title}</h1>
                <span className={`text-xs px-2 py-1 rounded ${
                  run.status === 'completed' 
                    ? 'bg-emerald-500/20 text-emerald-400' 
                    : run.status === 'failed'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-amber-500/20 text-amber-400'
                }`}>
                  {run.status.toUpperCase()}
                </span>
              </div>
              <p className="text-white/70">{run.summary_text}</p>
              <div className="flex items-center gap-4 mt-3 text-sm text-white/60">
                <span>{format(new Date(run.run_date), 'EEEE, MMMM d, yyyy')}</span>
                {run.completed_at && (
                  <span>Completed at {format(new Date(run.completed_at), 'h:mm a')}</span>
                )}
              </div>
            </div>
            <div className="text-right">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-white">{run.interactions_ingested}</p>
                  <p className="text-xs text-white/60">Interactions</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-white">{run.contacts_updated}</p>
                  <p className="text-xs text-white/60">Contacts Updated</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Top Actions */}
          {run.top_actions && run.top_actions.length > 0 && (
            <Card className="bg-slate-900/50 border-slate-700">
              <CardHeader
                className="cursor-pointer"
                onClick={() => setExpandedSection(expandedSection === 'top_actions' ? null : 'top_actions')}
              >
                <CardTitle className="text-white flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Target className="w-5 h-5 text-purple-400" />
                    Top Actions ({run.top_actions.length})
                  </span>
                  <span className="text-xs text-white/40">
                    {expandedSection === 'top_actions' ? '▼' : '▶'}
                  </span>
                </CardTitle>
              </CardHeader>
              {expandedSection === 'top_actions' && (
                <CardContent>
                  <div className="space-y-3">
                    {run.top_actions.map((action: any) => (
                      <div
                        key={action.action_id || action.id}
                        className="bg-slate-800/50 border border-slate-700 rounded-lg p-4"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs text-purple-400 uppercase">{action.type}</span>
                              {action.trust_risk && (
                                <span className="text-xs text-red-400 flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" />
                                  Risk
                                </span>
                              )}
                            </div>
                            <p className="text-white font-medium">{action.contact_name}</p>
                            <p className="text-sm text-white/70 mt-1">{action.description}</p>
                          </div>
                          {action.draft_available && (
                            <div className="flex gap-2">
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleApproveAndSend(action.action_id)}
                              >
                                <Send className="w-4 h-4 mr-1" />
                                Send
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDismiss(action.action_id)}
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              )}
            </Card>
          )}

          {/* Trust Risks */}
          {run.trust_risks && run.trust_risks.length > 0 && (
            <Card className="bg-slate-900/50 border-red-500/30">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  Trust Risks ({run.trust_risks.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {run.trust_risks.map((risk: any) => (
                    <div
                      key={risk.action_id || risk.id}
                      className="bg-red-900/20 border border-red-500/30 rounded-lg p-4"
                    >
                      <p className="text-white font-medium">{risk.contact_name}</p>
                      <p className="text-sm text-white/70 mt-1">{risk.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Value-First Moves */}
          {run.value_first_moves && run.value_first_moves.length > 0 && (
            <Card className="bg-slate-900/50 border-emerald-500/30">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-emerald-400" />
                  Value-First Opportunities ({run.value_first_moves.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {run.value_first_moves.map((move: any) => (
                    <div
                      key={move.action_id || move.id}
                      className="bg-emerald-900/20 border border-emerald-500/30 rounded-lg p-4"
                    >
                      <p className="text-white font-medium">{move.contact_name}</p>
                      <p className="text-sm text-white/70 mt-1">{move.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Evening-specific: Relationship Review */}
          {run.run_type === 'evening' && (
            <>
              {/* Wins */}
              {run.relationship_wins && run.relationship_wins.length > 0 && (
                <Card className="bg-slate-900/50 border-emerald-500/30">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-emerald-400" />
                      Today's Relationship Wins
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {run.relationship_wins.map((win: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-3 p-3 bg-emerald-900/20 rounded-lg">
                          <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                          <div>
                            <p className="text-white font-medium">{win.contact_name}</p>
                            <p className="text-sm text-white/70">{win.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Slips */}
              {run.relationship_slips && run.relationship_slips.length > 0 && (
                <Card className="bg-slate-900/50 border-red-500/30">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <TrendingDown className="w-5 h-5 text-red-400" />
                      What Slipped Today
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {run.relationship_slips.map((slip: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-3 p-3 bg-red-900/20 rounded-lg">
                          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                          <div>
                            <p className="text-white font-medium">{slip.contact_name}</p>
                            <p className="text-sm text-white/70">
                              {slip.description}
                              {slip.days_overdue > 0 && (
                                <span className="text-red-400 ml-2">({slip.days_overdue} days overdue)</span>
                              )}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Reconnect Tomorrow */}
              {run.reconnect_tomorrow && run.reconnect_tomorrow.length > 0 && (
                <Card className="bg-slate-900/50 border-blue-500/30">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Heart className="w-5 h-5 text-blue-400" />
                      Reconnect Tomorrow
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {run.reconnect_tomorrow.map((contact: any, idx: number) => (
                        <Link
                          key={idx}
                          to={`/contacts/${contact.contact_id}`}
                          className="flex items-center gap-3 p-3 bg-blue-900/20 rounded-lg hover:bg-blue-900/30 transition-colors"
                        >
                          <Users className="w-5 h-5 text-blue-400 flex-shrink-0" />
                          <div>
                            <p className="text-white font-medium">{contact.contact_name}</p>
                            <p className="text-sm text-white/70">{contact.reason}</p>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Messages to Reply */}
          {run.messages_to_reply && run.messages_to_reply.length > 0 && (
            <Card className="bg-slate-900/50 border-blue-500/30">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-400" />
                  Messages to Reply ({run.messages_to_reply.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {run.messages_to_reply.map((msg: any) => (
                    <div
                      key={msg.action_id || msg.id}
                      className="bg-blue-900/20 rounded-lg p-3"
                    >
                      <p className="text-sm font-medium text-white">{msg.contact_name}</p>
                      <p className="text-xs text-white/60 mt-1 line-clamp-2">{msg.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Intros to Consider */}
          {run.intros_to_consider && run.intros_to_consider.length > 0 && (
            <Card className="bg-slate-900/50 border-purple-500/30">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Users className="w-5 h-5 text-purple-400" />
                  Intro Opportunities ({run.intros_to_consider.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {run.intros_to_consider.map((intro: any) => (
                    <div
                      key={intro.action_id || intro.id}
                      className="bg-purple-900/20 rounded-lg p-3"
                    >
                      <p className="text-sm font-medium text-white">{intro.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Health Score */}
          {run.health_score_trend !== undefined && run.health_score_trend !== null && (
            <Card className="bg-slate-900/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  Network Health
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-4xl font-bold text-white">
                    {Math.round(run.health_score_trend * 100)}%
                  </p>
                  <p className="text-sm text-white/60 mt-1">Average Relationship Score</p>
                  <div className="w-full bg-slate-700 rounded-full h-3 mt-4">
                    <div
                      className={`h-3 rounded-full ${
                        run.health_score_trend >= 0.7
                          ? 'bg-emerald-500'
                          : run.health_score_trend >= 0.4
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${run.health_score_trend * 100}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

