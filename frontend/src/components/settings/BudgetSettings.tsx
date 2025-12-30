import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Loader2, DollarSign, Plus, Trash2, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import { useBudgets, useCheckBudgets } from '@/lib/hooks';
import { Link } from 'react-router-dom';

interface BudgetForm {
  scope: 'overall' | 'provider' | 'project';
  scope_id: string;
  period: 'daily' | 'weekly' | 'monthly';
  limit: number;
  enforcement_mode: 'warn' | 'require_confirmation' | 'hard_stop';
}

export const BudgetSettings = () => {
  const { data: budgets = [], isLoading } = useBudgets(false);
  const checkBudgets = useCheckBudgets();
  const [showForm, setShowForm] = useState(false);
  const [newBudget, setNewBudget] = useState<BudgetForm>({
    scope: 'overall',
    scope_id: '',
    period: 'monthly',
    limit: 100,
    enforcement_mode: 'warn',
  });

  const handleCreateBudget = async () => {
    try {
      // This would call an API endpoint to create budgets
      // For now, show a message that this feature is coming
      toast.success('Budget creation API coming soon. Use Cost Monitoring page to view budgets.');
      setShowForm(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create budget');
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
    <Card className="bg-slate-900/50 border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            Budget Policies
          </CardTitle>
          <div className="flex gap-2">
            <Link to="/cost">
              <Button variant="secondary" size="sm">
                View Costs
              </Button>
            </Link>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowForm(!showForm)}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Budget
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {showForm && (
          <div className="bg-slate-800/50 rounded-lg p-4 space-y-4 border border-slate-700">
            <h3 className="text-white font-semibold">Create New Budget</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Scope
                </label>
                <select
                  value={newBudget.scope}
                  onChange={(e) =>
                    setNewBudget({ ...newBudget, scope: e.target.value as any })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                >
                  <option value="overall">Overall</option>
                  <option value="provider">Provider</option>
                  <option value="project">Project</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Period
                </label>
                <select
                  value={newBudget.period}
                  onChange={(e) =>
                    setNewBudget({ ...newBudget, period: e.target.value as any })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Limit ($)
                </label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={newBudget.limit}
                  onChange={(e) =>
                    setNewBudget({ ...newBudget, limit: parseFloat(e.target.value) || 0 })
                  }
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Enforcement Mode
                </label>
                <select
                  value={newBudget.enforcement_mode}
                  onChange={(e) =>
                    setNewBudget({ ...newBudget, enforcement_mode: e.target.value as any })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                >
                  <option value="warn">Warn Only</option>
                  <option value="require_confirmation">Require Confirmation</option>
                  <option value="hard_stop">Hard Stop</option>
                </select>
              </div>
            </div>
            {newBudget.scope !== 'overall' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  {newBudget.scope === 'provider' ? 'Provider Name' : 'Project ID'}
                </label>
                <Input
                  value={newBudget.scope_id}
                  onChange={(e) =>
                    setNewBudget({ ...newBudget, scope_id: e.target.value })
                  }
                  placeholder={newBudget.scope === 'provider' ? 'e.g., openai' : 'Project ID'}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
            )}
            <div className="flex gap-2">
              <Button onClick={handleCreateBudget} variant="primary">
                Create Budget
              </Button>
              <Button onClick={() => setShowForm(false)} variant="ghost">
                Cancel
              </Button>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
          </div>
        ) : budgets.length === 0 ? (
          <div className="text-center py-8">
            <DollarSign className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
            <p className="text-slate-400 mb-2">No budgets configured</p>
            <p className="text-sm text-slate-500 mb-4">
              Create budgets to track and limit spending
            </p>
            <Link to="/cost">
              <Button variant="secondary">View Cost Monitoring</Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {budgets.map((budget) => {
              const isOverBudget = budget.percentage_used >= 100;
              const isWarning = budget.percentage_used >= 80;

              return (
                <div
                  key={budget.id}
                  className="bg-slate-800/50 rounded-lg p-4 border border-slate-700"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-semibold text-white">
                        {budget.scope} {budget.scope_id && `• ${budget.scope_id}`}
                      </h4>
                      <p className="text-sm text-slate-400">
                        {budget.period} • {budget.enforcement_mode}
                      </p>
                    </div>
                    <div className="text-right">
                      <p
                        className={`text-lg font-bold ${
                          isOverBudget
                            ? 'text-red-400'
                            : isWarning
                            ? 'text-amber-400'
                            : 'text-white'
                        }`}
                      >
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
                  {!budget.is_active && (
                    <p className="text-xs text-slate-500">Inactive</p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-blue-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-400 mb-1">Budget Enforcement</p>
              <ul className="text-xs text-blue-300 space-y-1">
                <li>
                  <strong>Warn:</strong> Shows alerts but allows spending
                </li>
                <li>
                  <strong>Require Confirmation:</strong> Asks for approval before exceeding budget
                </li>
                <li>
                  <strong>Hard Stop:</strong> Blocks spending when budget is exceeded
                </li>
              </ul>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

