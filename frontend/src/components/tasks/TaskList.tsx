import { useTasks } from '@/lib/hooks';
import { TaskCard } from './TaskCard';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Loader2, AlertCircle } from 'lucide-react';

export const TaskList = () => {
  const { data: tasks, isLoading, error, refetch, isFetching } = useTasks();

  if (isLoading && !tasks) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12 text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto" />
          <div>
            <p className="text-red-600 font-semibold mb-2">Failed to load tasks</p>
            <p className="text-sm text-gray-600 mb-4">
              {error instanceof Error ? error.message : 'Unable to connect to the API. Is the backend running?'}
            </p>
            <Button onClick={() => refetch()} variant="primary" size="sm">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!tasks || tasks.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-gray-500 italic">No tasks yet. Submit a task above to get started!</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {isFetching && (
        <div className="flex items-center justify-center py-2">
          <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
        </div>
      )}
      {tasks.map((task) => (
        <TaskCard key={task.task_id} task={task} />
      ))}
    </div>
  );
};

