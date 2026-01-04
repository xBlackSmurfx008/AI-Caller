import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { useState } from 'react';
import { useTasks } from '@/lib/hooks';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Loader2, AlertCircle, ArrowRight } from 'lucide-react';

type Props = {
  limit?: number;
};

const statusConfig: Record<
  string,
  { variant: 'info' | 'warning' | 'success' | 'error'; label: string; dotClass: string }
> = {
  planning: { variant: 'info', label: 'Planning', dotClass: 'bg-slate-400' },
  processing: { variant: 'warning', label: 'Processing', dotClass: 'bg-amber-400' },
  awaiting_confirmation: { variant: 'warning', label: 'Needs approval', dotClass: 'bg-amber-400' },
  completed: { variant: 'success', label: 'Completed', dotClass: 'bg-emerald-400' },
  failed: { variant: 'error', label: 'Failed', dotClass: 'bg-red-400' },
  rejected: { variant: 'error', label: 'Rejected', dotClass: 'bg-red-400' },
};

export const RecentTasksCompact = ({ limit = 5 }: Props) => {
  const { data: tasks, isLoading, error, refetch, isFetching } = useTasks();
  const [expanded, setExpanded] = useState(false);

  if (isLoading && !tasks) {
    return (
      <Card className="bg-slate-900/50 border-slate-700">
        <CardContent className="py-8 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-slate-900/50 border-slate-700">
        <CardContent className="py-8 text-center space-y-3">
          <AlertCircle className="w-6 h-6 text-red-400 mx-auto" />
          <p className="text-sm text-slate-300">Failed to load tasks</p>
          <Button onClick={() => refetch()} variant="secondary" size="sm" disabled={isFetching}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const all = tasks || [];
  const approvals = all.filter((t) => t.status === 'awaiting_confirmation');
  const failures = all.filter((t) => t.status === 'failed');
  const completed = all.filter((t) => t.status === 'completed');

  const approvalsToShow = approvals.slice(0, 3);
  const outcomesSource = failures.length > 0 ? failures : completed;
  const outcomesLabel = failures.length > 0 ? 'Recent failures' : 'Recent completed';
  const outcomesToShow = outcomesSource.slice(0, expanded ? limit : 3);

  if (all.length === 0) {
    return (
      <Card className="bg-slate-900/50 border-slate-700">
        <CardContent className="py-8 text-center">
          <p className="text-sm text-slate-400">No tasks yet. Create one above to get started.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-900/50 border-slate-700">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-white">Recent Tasks</h3>
            {isFetching && <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />}
          </div>
          <Link to="/tasks">
            <Button variant="secondary" size="sm" className="h-8">
              View all
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>

        <div className="space-y-4">
          {approvalsToShow.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-amber-300">Pending approvals</p>
                <Badge variant="warning">{approvals.length}</Badge>
              </div>
              <div className="space-y-2">
                {approvalsToShow.map((t) => {
                  const cfg = statusConfig[t.status] || statusConfig.planning;
                  return (
                    <div
                      key={t.task_id}
                      className="flex items-start gap-3 p-3 rounded-lg border border-amber-500/20 bg-amber-500/5"
                    >
                      <div className={`w-2 h-2 rounded-full mt-2 ${cfg.dotClass}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant={cfg.variant}>{cfg.label}</Badge>
                          <span className="text-xs text-slate-500">
                            {formatDistanceToNow(new Date(t.created_at), { addSuffix: true })}
                          </span>
                        </div>
                        <p className="text-sm text-slate-100 truncate">{t.task}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold text-slate-300">{outcomesLabel}</p>
              {outcomesSource.length > 3 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-slate-300"
                  onClick={() => setExpanded((v) => !v)}
                >
                  {expanded ? 'Show less' : 'Show more'}
                </Button>
              )}
            </div>

            {outcomesToShow.length === 0 ? (
              <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30">
                <p className="text-sm text-slate-400">
                  {failures.length > 0 ? 'No failures to show.' : 'No completed tasks yet.'}
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {outcomesToShow.map((t) => {
                  const cfg = statusConfig[t.status] || statusConfig.planning;
                  return (
                    <div
                      key={t.task_id}
                      className="flex items-start gap-3 p-3 rounded-lg border border-slate-800 bg-slate-950/30"
                    >
                      <div className={`w-2 h-2 rounded-full mt-2 ${cfg.dotClass}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant={cfg.variant}>{cfg.label}</Badge>
                          <span className="text-xs text-slate-500">
                            {formatDistanceToNow(new Date(t.created_at), { addSuffix: true })}
                          </span>
                        </div>
                        <p className="text-sm text-slate-200 truncate">{t.task}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};


