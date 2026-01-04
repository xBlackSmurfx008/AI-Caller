import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useRelationshipRuns, useTriggerRelationshipRunSync } from '@/lib/hooks';
import {
  Loader2,
  ArrowLeft,
  ArrowRight,
  Clock,
  CheckCircle2,
  XCircle,
  Play,
  RefreshCw,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { useState } from 'react';

export const RelationshipOpsRunsList = () => {
  const [filterType, setFilterType] = useState<string | undefined>();
  const { data: runs, isLoading, refetch } = useRelationshipRuns(50, filterType);
  const triggerRun = useTriggerRelationshipRunSync();

  const handleTriggerRun = async (runType: 'morning' | 'midday' | 'afternoon' | 'evening') => {
    try {
      await triggerRun.mutateAsync({ runType, force: true });
    } catch (e) {
      console.error('Failed to trigger run:', e);
    }
  };

  const getRunTypeConfig = (runType: string) => {
    switch (runType) {
      case 'morning':
        return { icon: '🌅', color: 'text-orange-400', bgColor: 'bg-orange-500/20' };
      case 'midday':
        return { icon: '☀️', color: 'text-yellow-400', bgColor: 'bg-yellow-500/20' };
      case 'afternoon':
        return { icon: '🌤️', color: 'text-blue-400', bgColor: 'bg-blue-500/20' };
      case 'evening':
        return { icon: '🌙', color: 'text-purple-400', bgColor: 'bg-purple-500/20' };
      default:
        return { icon: '⚡', color: 'text-slate-400', bgColor: 'bg-slate-500/20' };
    }
  };

  const runTypes = ['morning', 'midday', 'afternoon', 'evening'] as const;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link to="/command-center" className="inline-flex items-center text-white/60 hover:text-white mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Command Center
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Relationship Ops Runs</h1>
            <p className="text-white/60">History of all scheduled and manual relationship ops runs</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => refetch()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Quick Trigger */}
      <Card className="mb-6 bg-slate-900/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Trigger Manual Run</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 flex-wrap">
            {runTypes.map((type) => {
              const config = getRunTypeConfig(type);
              return (
                <Button
                  key={type}
                  variant="secondary"
                  onClick={() => handleTriggerRun(type)}
                  disabled={triggerRun.isPending}
                  className="flex items-center gap-2"
                >
                  {triggerRun.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <span>{config.icon}</span>
                      <Play className="w-4 h-4" />
                    </>
                  )}
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Filter */}
      <div className="mb-6 flex gap-2">
        <Button
          variant={!filterType ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => setFilterType(undefined)}
        >
          All
        </Button>
        {runTypes.map((type) => (
          <Button
            key={type}
            variant={filterType === type ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilterType(type)}
          >
            {getRunTypeConfig(type).icon} {type.charAt(0).toUpperCase() + type.slice(1)}
          </Button>
        ))}
      </div>

      {/* Runs List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
        </div>
      ) : !runs || runs.length === 0 ? (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <Clock className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400 mb-4">No runs found</p>
            <p className="text-sm text-slate-500">
              Trigger a run above or wait for the scheduled runs
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {runs.map((run) => {
            const config = getRunTypeConfig(run.run_type);
            return (
              <Link key={run.id} to={`/relationship-ops/runs/${run.id}`}>
                <Card className="bg-slate-900/50 border-slate-700 hover:border-purple-500/50 transition-colors">
                  <CardContent className="py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-lg ${config.bgColor}`}>
                          <span className="text-2xl">{config.icon}</span>
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="text-lg font-semibold text-white">
                              {run.summary_title || `${run.run_type.charAt(0).toUpperCase() + run.run_type.slice(1)} Run`}
                            </h3>
                            <span className={`text-xs px-2 py-0.5 rounded flex items-center gap-1 ${
                              run.status === 'completed'
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : run.status === 'failed'
                                ? 'bg-red-500/20 text-red-400'
                                : 'bg-amber-500/20 text-amber-400'
                            }`}>
                              {run.status === 'completed' ? (
                                <CheckCircle2 className="w-3 h-3" />
                              ) : run.status === 'failed' ? (
                                <XCircle className="w-3 h-3" />
                              ) : (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              )}
                              {run.status}
                            </span>
                          </div>
                          <p className="text-sm text-white/60 line-clamp-1">
                            {run.summary_text || 'No summary available'}
                          </p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
                            <span>{format(new Date(run.run_date), 'MMM d, yyyy h:mm a')}</span>
                            <span>•</span>
                            <span>{formatDistanceToNow(new Date(run.run_date), { addSuffix: true })}</span>
                            <span>•</span>
                            <span>{run.interactions_ingested} interactions</span>
                            <span>•</span>
                            <span>{run.contacts_updated} contacts updated</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-2xl font-bold text-white">
                            {run.top_actions?.length || 0}
                          </p>
                          <p className="text-xs text-white/40">Actions</p>
                        </div>
                        <ArrowRight className="w-5 h-5 text-white/40" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};


