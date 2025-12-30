import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useCostSummary, useCostByProvider, useCostByProject, useBudgets, useCostAlerts, useCheckBudgets } from '@/lib/hooks';
import { Loader2, DollarSign, TrendingUp, AlertTriangle, CheckCircle2, RefreshCw, Calendar, BarChart3, PieChart } from 'lucide-react';
import toast from 'react-hot-toast';
import { Link } from 'react-router-dom';

export const CostMonitoring = () => {
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('week');
  const [projectRange, setProjectRange] = useState<'day' | 'week' | 'month'>('month');
  
  const { data: summary, isLoading: summaryLoading } = useCostSummary(timeRange);
  const { data: byProvider, isLoading: providerLoading } = useCostByProvider(timeRange);
  const { data: byProject, isLoading: projectLoading } = useCostByProject(projectRange);
  const { data: budgets = [], isLoading: budgetsLoading } = useBudgets(true);
  const { data: alerts = [], isLoading: alertsLoading } = useCostAlerts(true);
  const checkBudgets = useCheckBudgets();

  const handleCheckBudgets = async () => {
    try {
      const result = await checkBudgets.mutateAsync();
      toast.success(`Checked budgets. ${result.alerts_generated} new alerts generated.`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to check budgets');
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
          <h1 className="text-3xl font-bold text-white mb-2">Cost Monitoring</h1>
          <p className="text-white/80">
            Track AI service costs, budgets, and spending alerts
          </p>
        </div>
        <Button
          onClick={handleCheckBudgets}
          disabled={checkBudgets.isPending}
          variant="secondary"
        >
          {checkBudgets.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Check Budgets
        </Button>
      </div>

      {/* Alerts Banner */}
      {!alertsLoading && alerts.length > 0 && (
        <Card className="mb-6 bg-red-500/10 border-red-500/30">
          <CardContent className="py-4">
            <div className="flex items-center gap-3 mb-3">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <h3 className="font-semibold text-white">Active Cost Alerts</h3>
            </div>
            <div className="space-y-2">
              {alerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="bg-slate-800/50 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-white">{alert.message}</p>
                      <p className="text-xs text-slate-400 mt-1">
                        {alert.scope} {alert.scope_id && `• ${alert.scope_id}`}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-red-400">
                        {formatCurrency(alert.current_spend)} / {formatCurrency(alert.limit)}
                      </p>
                      <p className="text-xs text-slate-400">
                        {Math.round(alert.percentage_used)}% used
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400">Today</p>
              <DollarSign className="w-4 h-4 text-slate-400" />
            </div>
            {summaryLoading ? (
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            ) : (
              <p className="text-2xl font-bold text-white">
                {summary ? formatCurrency(summary.total_cost) : '$0.00'}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400">This Week</p>
              <TrendingUp className="w-4 h-4 text-slate-400" />
            </div>
            {summaryLoading ? (
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            ) : (
              <p className="text-2xl font-bold text-white">
                {summary && timeRange === 'week' ? formatCurrency(summary.total_cost) : '—'}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400">This Month</p>
              <Calendar className="w-4 h-4 text-slate-400" />
            </div>
            {summaryLoading ? (
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            ) : (
              <p className="text-2xl font-bold text-white">
                {summary && timeRange === 'month' ? formatCurrency(summary.total_cost) : '—'}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400">Active Budgets</p>
              <CheckCircle2 className="w-4 h-4 text-slate-400" />
            </div>
            {budgetsLoading ? (
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            ) : (
              <p className="text-2xl font-bold text-white">{budgets.length}</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Cost Breakdown by Provider */}
        <Card className="bg-slate-900/50 border-slate-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Cost by Provider
              </CardTitle>
              <div className="flex gap-2">
                <Button
                  variant={timeRange === 'day' ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setTimeRange('day')}
                >
                  Day
                </Button>
                <Button
                  variant={timeRange === 'week' ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setTimeRange('week')}
                >
                  Week
                </Button>
                <Button
                  variant={timeRange === 'month' ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setTimeRange('month')}
                >
                  Month
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {providerLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
              </div>
            ) : !byProvider || byProvider.length === 0 ? (
              <p className="text-slate-400 text-center py-8">No cost data available</p>
            ) : (
              <div className="space-y-3">
                {byProvider.map((item) => (
                  <div key={item.provider} className="bg-slate-800/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-white">{item.provider}</span>
                      <span className="text-sm font-semibold text-white">
                        {formatCurrency(item.total_cost)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>{item.event_count} events</span>
                      <span>
                        {summary && summary.total_cost > 0
                          ? `${Math.round((item.total_cost / summary.total_cost) * 100)}%`
                          : '0%'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cost by Project */}
        <Card className="bg-slate-900/50 border-slate-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-white flex items-center gap-2">
                <PieChart className="w-5 h-5" />
                Cost by Project
              </CardTitle>
              <div className="flex gap-2">
                <Button
                  variant={projectRange === 'day' ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setProjectRange('day')}
                >
                  Day
                </Button>
                <Button
                  variant={projectRange === 'week' ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setProjectRange('week')}
                >
                  Week
                </Button>
                <Button
                  variant={projectRange === 'month' ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setProjectRange('month')}
                >
                  Month
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {projectLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
              </div>
            ) : !byProject || byProject.length === 0 ? (
              <p className="text-slate-400 text-center py-8">No project costs available</p>
            ) : (
              <div className="space-y-3">
                {byProject.map((item) => (
                  <Link
                    key={item.project_id}
                    to={`/projects/${item.project_id}`}
                    className="block bg-slate-800/50 rounded-lg p-3 hover:bg-slate-700/50 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-white">Project {item.project_id.slice(0, 8)}</span>
                      <span className="text-sm font-semibold text-white">
                        {formatCurrency(item.total_cost)}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">
                      {item.event_count} events
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Budgets */}
      <Card className="bg-slate-900/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            Active Budgets
          </CardTitle>
        </CardHeader>
        <CardContent>
          {budgetsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            </div>
          ) : budgets.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-400 mb-4">No active budgets configured</p>
              <p className="text-sm text-slate-500">
                Budgets help you track and limit spending. Configure them in Settings.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {budgets.map((budget) => {
                const isOverBudget = budget.percentage_used >= 100;
                const isWarning = budget.percentage_used >= 80;
                
                return (
                  <div key={budget.id} className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-white">
                          {budget.scope} {budget.scope_id && `• ${budget.scope_id}`}
                        </h4>
                        <p className="text-sm text-slate-400">
                          {budget.period} • {budget.enforcement_mode}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={`text-lg font-bold ${
                          isOverBudget ? 'text-red-400' : isWarning ? 'text-amber-400' : 'text-white'
                        }`}>
                          {formatCurrency(budget.current_spend)} / {formatCurrency(budget.limit)}
                        </p>
                        <p className="text-xs text-slate-400">
                          {Math.round(budget.percentage_used)}% used
                        </p>
                      </div>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2 mb-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          isOverBudget
                            ? 'bg-red-500'
                            : isWarning
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(budget.percentage_used, 100)}%` }}
                      />
                    </div>
                    {budget.forecasted_spend > budget.limit && (
                      <p className="text-xs text-amber-400">
                        ⚠️ Forecasted: {formatCurrency(budget.forecasted_spend)} (exceeds limit)
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

