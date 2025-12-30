import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { 
  usePEC, 
  useGeneratePEC, 
  useApprovePEC, 
  useRejectPEC, 
  useUpdatePECChecklist, 
  useRegeneratePEC,
  useExecutionReadyCheck 
} from '@/lib/hooks';
import type { 
  ProjectExecutionConfirmation, 
  PECTaskToolMap, 
  PECRisk, 
  PECGap, 
  PECApprovalChecklistItem,
  PECAssumption,
  PECConstraint,
  PECPreference
} from '@/lib/api';
import toast from 'react-hot-toast';
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  AlertTriangle, 
  XCircle,
  RefreshCw,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Target,
  Clock,
  DollarSign,
  Shield,
  Lightbulb,
  Users,
  Zap
} from 'lucide-react';

interface PECDashboardProps {
  projectId: string;
  onBeginExecution?: () => void;
}

export const PECDashboard = ({ projectId, onBeginExecution }: PECDashboardProps) => {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    summary: true,
    tasks: true,
    risks: false,
    assumptions: false,
    checklist: true,
  });
  const [approvalNotes, setApprovalNotes] = useState('');

  const { data: pec, isLoading: pecLoading, refetch } = usePEC(projectId);
  const { data: executionReady } = useExecutionReadyCheck(projectId);
  const generatePEC = useGeneratePEC();
  const approvePEC = useApprovePEC();
  const rejectPEC = useRejectPEC();
  const updateChecklist = useUpdatePECChecklist();
  const regeneratePEC = useRegeneratePEC();

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const handleGeneratePEC = async () => {
    try {
      await generatePEC.mutateAsync({ projectId });
      toast.success('PEC generated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate PEC');
    }
  };

  const handleApprovePEC = async () => {
    if (!pec) return;
    try {
      await approvePEC.mutateAsync({ pecId: pec.id, approvalNotes });
      toast.success('PEC approved! Ready for execution.');
      setApprovalNotes('');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to approve PEC');
    }
  };

  const handleRejectPEC = async () => {
    if (!pec) return;
    try {
      await rejectPEC.mutateAsync({ pecId: pec.id, approvalNotes });
      toast.success('PEC rejected');
      setApprovalNotes('');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to reject PEC');
    }
  };

  const handleRegeneratePEC = async () => {
    if (!pec) return;
    try {
      await regeneratePEC.mutateAsync({ pecId: pec.id, reason: 'Manual regeneration' });
      toast.success('PEC regenerated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to regenerate PEC');
    }
  };

  const handleChecklistToggle = async (item: string, currentStatus: string) => {
    if (!pec) return;
    const newStatus = currentStatus === 'approved' ? 'pending' : 'approved';
    try {
      await updateChecklist.mutateAsync({ pecId: pec.id, item, status: newStatus });
    } catch (error: any) {
      toast.error('Failed to update checklist');
    }
  };

  const getFeasibilityBadge = (feasibility: string) => {
    switch (feasibility) {
      case 'FULLY_AUTONOMOUS':
        return <span className="px-2 py-1 text-xs bg-emerald-500/20 text-emerald-400 rounded">✅ Autonomous</span>;
      case 'PARTIAL':
        return <span className="px-2 py-1 text-xs bg-amber-500/20 text-amber-400 rounded">🟡 Partial</span>;
      case 'BLOCKED':
        return <span className="px-2 py-1 text-xs bg-red-500/20 text-red-400 rounded">🔴 Blocked</span>;
      default:
        return null;
    }
  };

  const getGateBadge = (gate: string) => {
    switch (gate) {
      case 'READY':
        return (
          <div className="flex items-center gap-2 px-3 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-semibold">Ready to Execute</span>
          </div>
        );
      case 'READY_WITH_QUESTIONS':
        return (
          <div className="flex items-center gap-2 px-3 py-2 bg-amber-500/20 text-amber-400 rounded-lg">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-semibold">Ready (Requires Answers)</span>
          </div>
        );
      case 'BLOCKED':
        return (
          <div className="flex items-center gap-2 px-3 py-2 bg-red-500/20 text-red-400 rounded-lg">
            <XCircle className="w-5 h-5" />
            <span className="font-semibold">Blocked</span>
          </div>
        );
      default:
        return null;
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      default:
        return <Lightbulb className="w-4 h-4 text-blue-400" />;
    }
  };

  if (pecLoading) {
    return (
      <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        </CardContent>
      </Card>
    );
  }

  if (!pec) {
    return (
      <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <FileCheck className="w-5 h-5 text-indigo-400" />
            Project Execution Confirmation
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center py-8">
          <div className="mb-6">
            <Target className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400 mb-2">No execution confirmation generated yet.</p>
            <p className="text-sm text-slate-500">
              Generate a PEC to validate scope, tools, and risks before execution.
            </p>
          </div>
          <Button
            onClick={handleGeneratePEC}
            variant="primary"
            disabled={generatePEC.isPending}
            className="bg-indigo-600 hover:bg-indigo-700"
          >
            {generatePEC.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Zap className="w-4 h-4 mr-2" />
            )}
            Generate Execution Confirmation
          </Button>
        </CardContent>
      </Card>
    );
  }

  const feasibilityStats = {
    autonomous: pec.task_tool_map?.filter(t => t.feasibility === 'FULLY_AUTONOMOUS').length || 0,
    partial: pec.task_tool_map?.filter(t => t.feasibility === 'PARTIAL').length || 0,
    blocked: pec.task_tool_map?.filter(t => t.feasibility === 'BLOCKED').length || 0,
  };

  return (
    <div className="space-y-6">
      {/* Header with Gate Status */}
      <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <FileCheck className="w-6 h-6 text-indigo-400" />
              <div>
                <h3 className="text-lg font-semibold text-white">
                  Execution Confirmation v{pec.version}
                </h3>
                <p className="text-sm text-slate-400">
                  Status: <span className="capitalize text-white">{pec.status}</span>
                  {pec.approved_at && ` • Approved ${new Date(pec.approved_at).toLocaleDateString()}`}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {getGateBadge(pec.execution_gate)}
              <Button
                onClick={handleRegeneratePEC}
                variant="secondary"
                size="sm"
                disabled={regeneratePEC.isPending}
              >
                <RefreshCw className={`w-4 h-4 ${regeneratePEC.isPending ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Section */}
      <Card className="bg-slate-900/50 border-slate-700">
        <CardHeader 
          className="cursor-pointer hover:bg-slate-800/50 rounded-t-lg transition-colors"
          onClick={() => toggleSection('summary')}
        >
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-white text-base">
              <Target className="w-4 h-4 text-indigo-400" />
              Project Summary
            </CardTitle>
            {expandedSections.summary ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </div>
        </CardHeader>
        {expandedSections.summary && pec.summary && (
          <CardContent className="border-t border-slate-700">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Total Tasks</p>
                <p className="text-2xl font-bold text-white">{pec.summary.total_tasks}</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Estimated Time</p>
                <p className="text-2xl font-bold text-white">
                  {Math.round((pec.summary.total_estimated_minutes || 0) / 60)}h
                </p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">AI Tasks</p>
                <p className="text-2xl font-bold text-indigo-400">{pec.summary.ai_executable_tasks}</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Human Tasks</p>
                <p className="text-2xl font-bold text-amber-400">{pec.summary.human_tasks}</p>
              </div>
            </div>
            {pec.summary.definition_of_success && pec.summary.definition_of_success.length > 0 && (
              <div>
                <p className="text-xs text-slate-400 mb-2 uppercase tracking-wide">Definition of Success</p>
                <ul className="space-y-1">
                  {pec.summary.definition_of_success.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Task Feasibility Section */}
      <Card className="bg-slate-900/50 border-slate-700">
        <CardHeader 
          className="cursor-pointer hover:bg-slate-800/50 rounded-t-lg transition-colors"
          onClick={() => toggleSection('tasks')}
        >
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-white text-base">
              <Zap className="w-4 h-4 text-indigo-400" />
              Task & Tool Mapping
              <span className="ml-2 text-xs text-slate-400">
                ({feasibilityStats.autonomous} ✅ / {feasibilityStats.partial} 🟡 / {feasibilityStats.blocked} 🔴)
              </span>
            </CardTitle>
            {expandedSections.tasks ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </div>
        </CardHeader>
        {expandedSections.tasks && pec.task_tool_map && (
          <CardContent className="border-t border-slate-700">
            <div className="space-y-3">
              {pec.task_tool_map.map((task: PECTaskToolMap) => (
                <div key={task.task_id} className="bg-slate-800/50 rounded-lg p-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-white truncate">{task.task_title}</h4>
                        {getFeasibilityBadge(task.feasibility)}
                      </div>
                      <p className="text-xs text-slate-400 mb-2">
                        Type: <span className="text-slate-300 capitalize">{task.task_type}</span>
                        {task.tools_required.length > 0 && (
                          <> • Tools: <span className="text-indigo-400">{task.tools_required.join(', ')}</span></>
                        )}
                      </p>
                      {task.required_approvals.length > 0 && (
                        <div className="text-xs text-amber-400 mb-1">
                          ⚠️ {task.required_approvals.join('; ')}
                        </div>
                      )}
                      {task.fallback_plan && (
                        <div className="text-xs text-red-400">
                          Fallback: {task.fallback_plan}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Risks & Gaps Section */}
      {((pec.risks && pec.risks.length > 0) || (pec.gaps && pec.gaps.length > 0)) && (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardHeader 
            className="cursor-pointer hover:bg-slate-800/50 rounded-t-lg transition-colors"
            onClick={() => toggleSection('risks')}
          >
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-white text-base">
                <Shield className="w-4 h-4 text-amber-400" />
                Risks & Gaps
                <span className="ml-2 text-xs text-slate-400">
                  ({(pec.risks?.length || 0) + (pec.gaps?.length || 0)} items)
                </span>
              </CardTitle>
              {expandedSections.risks ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
            </div>
          </CardHeader>
          {expandedSections.risks && (
            <CardContent className="border-t border-slate-700 space-y-4">
              {pec.risks && pec.risks.length > 0 && (
                <div>
                  <h4 className="text-xs text-slate-400 uppercase tracking-wide mb-2">Risks</h4>
                  <div className="space-y-2">
                    {pec.risks.map((risk: PECRisk) => (
                      <div key={risk.risk_id} className="flex items-start gap-3 bg-slate-800/50 rounded-lg p-3">
                        {getSeverityIcon(risk.severity)}
                        <div className="flex-1">
                          <p className="text-sm text-white">{risk.description}</p>
                          <p className="text-xs text-slate-400 mt-1">Mitigation: {risk.mitigation}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {pec.gaps && pec.gaps.length > 0 && (
                <div>
                  <h4 className="text-xs text-slate-400 uppercase tracking-wide mb-2">Gaps</h4>
                  <div className="space-y-2">
                    {pec.gaps.map((gap: PECGap) => (
                      <div key={gap.gap_id} className="flex items-start gap-3 bg-slate-800/50 rounded-lg p-3">
                        {getSeverityIcon(gap.severity)}
                        <div className="flex-1">
                          <p className="text-sm text-white">{gap.description}</p>
                          <p className="text-xs text-slate-400 mt-1">Recommendation: {gap.recommendation}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {/* Assumptions Section */}
      {pec.assumptions && pec.assumptions.length > 0 && (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardHeader 
            className="cursor-pointer hover:bg-slate-800/50 rounded-t-lg transition-colors"
            onClick={() => toggleSection('assumptions')}
          >
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-white text-base">
                <Lightbulb className="w-4 h-4 text-blue-400" />
                Assumptions & Constraints
              </CardTitle>
              {expandedSections.assumptions ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
            </div>
          </CardHeader>
          {expandedSections.assumptions && (
            <CardContent className="border-t border-slate-700 space-y-4">
              <div>
                <h4 className="text-xs text-slate-400 uppercase tracking-wide mb-2">Assumptions</h4>
                <ul className="space-y-2">
                  {pec.assumptions.map((assumption: PECAssumption) => (
                    <li key={assumption.assumption_id} className="flex items-start gap-2 text-sm text-slate-300">
                      <span className="text-indigo-400">•</span>
                      {assumption.description}
                    </li>
                  ))}
                </ul>
              </div>
              {pec.constraints_applied && pec.constraints_applied.length > 0 && (
                <div>
                  <h4 className="text-xs text-slate-400 uppercase tracking-wide mb-2">Constraints Applied</h4>
                  <ul className="space-y-2">
                    {pec.constraints_applied.map((constraint: PECConstraint, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                        <span className="text-amber-400">⚙️</span>
                        {constraint.description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {/* Cost Estimate */}
      {pec.cost_estimate && (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <DollarSign className="w-5 h-5 text-emerald-400" />
                <div>
                  <p className="text-xs text-slate-400">Estimated Cost</p>
                  <p className="text-xl font-bold text-white">
                    ${pec.cost_estimate.total_estimated_cost.toFixed(2)} {pec.cost_estimate.currency}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-400">Confidence</p>
                <p className="text-lg font-medium text-slate-300">
                  {Math.round(pec.cost_estimate.confidence * 100)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Approval Checklist */}
      {pec.status !== 'approved' && pec.approval_checklist && pec.approval_checklist.length > 0 && (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardHeader 
            className="cursor-pointer hover:bg-slate-800/50 rounded-t-lg transition-colors"
            onClick={() => toggleSection('checklist')}
          >
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-white text-base">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Approval Checklist
              </CardTitle>
              {expandedSections.checklist ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
            </div>
          </CardHeader>
          {expandedSections.checklist && (
            <CardContent className="border-t border-slate-700">
              <div className="space-y-2">
                {pec.approval_checklist.map((item: PECApprovalChecklistItem) => (
                  <div 
                    key={item.item} 
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                      item.status === 'approved' 
                        ? 'bg-emerald-500/10 hover:bg-emerald-500/20' 
                        : item.blocking 
                          ? 'bg-red-500/10 hover:bg-red-500/20'
                          : 'bg-slate-800/50 hover:bg-slate-700/50'
                    }`}
                    onClick={() => !item.blocking && handleChecklistToggle(item.item, item.status)}
                  >
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                      item.status === 'approved'
                        ? 'bg-emerald-500 border-emerald-500'
                        : item.blocking
                          ? 'border-red-500'
                          : 'border-slate-500'
                    }`}>
                      {item.status === 'approved' && <CheckCircle2 className="w-3 h-3 text-white" />}
                      {item.blocking && item.status !== 'approved' && <XCircle className="w-3 h-3 text-red-400" />}
                    </div>
                    <div className="flex-1">
                      <p className={`text-sm ${item.status === 'approved' ? 'text-emerald-400' : 'text-white'}`}>
                        {item.description}
                      </p>
                      {item.blocking && item.status !== 'approved' && (
                        <p className="text-xs text-red-400 mt-0.5">Blocking</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Approval Actions */}
      {pec.status !== 'approved' && (
        <Card className="bg-gradient-to-br from-indigo-900/30 to-slate-900 border-indigo-700/50">
          <CardContent className="py-6">
            <div className="space-y-4">
              <Textarea
                placeholder="Approval notes (optional)"
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                rows={2}
                className="bg-slate-800/50 border-slate-700"
              />
              <div className="flex items-center justify-between">
                <Button
                  onClick={handleRejectPEC}
                  variant="secondary"
                  disabled={rejectPEC.isPending}
                  className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                >
                  {rejectPEC.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4 mr-2" />}
                  Reject
                </Button>
                <Button
                  onClick={handleApprovePEC}
                  disabled={approvePEC.isPending || pec.execution_gate === 'BLOCKED'}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {approvePEC.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                  )}
                  Approve & Begin Execution
                </Button>
              </div>
              {pec.execution_gate === 'BLOCKED' && (
                <p className="text-xs text-red-400 text-center">
                  Cannot approve: Resolve blocking issues first
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Approved State */}
      {pec.status === 'approved' && (
        <Card className="bg-gradient-to-br from-emerald-900/30 to-slate-900 border-emerald-700/50">
          <CardContent className="py-6 text-center">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-white mb-1">Execution Confirmed</h3>
            <p className="text-sm text-slate-400 mb-4">
              Approved by {pec.approved_by} on {pec.approved_at && new Date(pec.approved_at).toLocaleDateString()}
            </p>
            {onBeginExecution && (
              <Button
                onClick={onBeginExecution}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                <Zap className="w-4 h-4 mr-2" />
                Begin Execution
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

