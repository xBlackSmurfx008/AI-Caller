import { format } from 'date-fns';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useConfirmTask } from '@/lib/hooks';
import { type Task } from '@/lib/api';
import { toast } from 'react-hot-toast';
import { CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react';

interface TaskCardProps {
  task: Task;
}

const statusConfig = {
  planning: { variant: 'info' as const, icon: Clock, label: 'Planning' },
  processing: { variant: 'warning' as const, icon: Clock, label: 'Processing' },
  awaiting_confirmation: { variant: 'warning' as const, icon: AlertCircle, label: 'Awaiting Confirmation' },
  completed: { variant: 'success' as const, icon: CheckCircle2, label: 'Completed' },
  failed: { variant: 'error' as const, icon: XCircle, label: 'Failed' },
  rejected: { variant: 'error' as const, icon: XCircle, label: 'Rejected' },
};

export const TaskCard = ({ task }: TaskCardProps) => {
  const confirmTask = useConfirmTask();
  const statusInfo = statusConfig[task.status as keyof typeof statusConfig] || statusConfig.planning;
  const StatusIcon = statusInfo.icon;

  const handleConfirm = async (approve: boolean) => {
    try {
      await confirmTask.mutateAsync({ taskId: task.task_id, approve });
      toast.success(approve ? 'Task approved' : 'Task rejected');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to confirm task');
    }
  };

  return (
    <Card className={task.status === 'awaiting_confirmation' ? 'ring-2 ring-yellow-400' : ''}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <StatusIcon className="w-5 h-5 text-gray-400" />
            <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
          </div>
          <span className="text-sm text-gray-500">
            {format(new Date(task.created_at), 'MMM d, yyyy h:mm a')}
          </span>
        </div>

        <p className="text-gray-900 mb-4">{task.task}</p>

        {task.status === 'awaiting_confirmation' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <h4 className="font-semibold text-yellow-900 mb-2">Needs Confirmation</h4>
            {task.policy_reasons && task.policy_reasons.length > 0 && (
              <p className="text-sm text-yellow-800 mb-2">
                <strong>Reasons:</strong> {task.policy_reasons.join(', ')}
              </p>
            )}
            {task.planned_tool_calls && task.planned_tool_calls.length > 0 && (
              <details className="mt-2">
                <summary className="text-sm text-yellow-800 cursor-pointer font-medium">
                  View planned actions
                </summary>
                <pre className="mt-2 text-xs bg-yellow-100 p-2 rounded overflow-auto">
                  {JSON.stringify(task.planned_tool_calls, null, 2)}
                </pre>
              </details>
            )}
            <div className="flex gap-2 mt-4">
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleConfirm(true)}
                disabled={confirmTask.isPending}
              >
                Approve
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleConfirm(false)}
                disabled={confirmTask.isPending}
              >
                Reject
              </Button>
            </div>
          </div>
        )}

        {task.result && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <h4 className="font-semibold text-green-900 mb-2">Result</h4>
            <pre className="text-sm text-green-800 whitespace-pre-wrap overflow-auto">
              {JSON.stringify(task.result, null, 2)}
            </pre>
          </div>
        )}

        {task.error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="font-semibold text-red-900 mb-2">Error</h4>
            <p className="text-sm text-red-800">{task.error}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

