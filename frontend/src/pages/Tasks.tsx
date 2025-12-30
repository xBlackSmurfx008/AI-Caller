import { TaskInput } from '@/components/tasks/TaskInput';
import { TaskList } from '@/components/tasks/TaskList';

export const Tasks = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Tasks</h1>
        <p className="text-white/80">
          Create and manage your AI assistant tasks
        </p>
      </div>

      <div className="mb-8">
        <TaskInput />
      </div>

      <div>
        <h2 className="text-2xl font-semibold text-white mb-4">All Tasks</h2>
        <TaskList />
      </div>
    </div>
  );
};

