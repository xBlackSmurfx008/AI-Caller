import { useState } from 'react';
import { useCreateTask, useProjects, useCreateProject } from '@/lib/hooks';
import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { toast } from 'react-hot-toast';
import { Plus, X, MessageSquare, FileText, FolderOpen, Loader2, Calendar, AlertTriangle } from 'lucide-react';

type TaskMode = 'quick' | 'detailed';
type DeadlineType = 'HARD' | 'FLEX' | '';

export const TaskInput = () => {
  const [mode, setMode] = useState<TaskMode>('quick');
  const [task, setTask] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [context, setContext] = useState('');
  const [projectId, setProjectId] = useState<string>('');
  const [dueDate, setDueDate] = useState('');
  const [deadlineType, setDeadlineType] = useState<DeadlineType>('');
  const [showForm, setShowForm] = useState(false);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newProjectDueDate, setNewProjectDueDate] = useState('');
  
  const createTask = useCreateTask();
  const createProject = useCreateProject();
  const { godfatherSettings } = useAppStore();
  const { data: projects = [], refetch: refetchProjects } = useProjects('active');

  const resetForm = () => {
    setTask('');
    setTitle('');
    setDescription('');
    setContext('');
    setProjectId('');
    setDueDate('');
    setDeadlineType('');
    setShowForm(false);
    setMode('quick');
  };

  const handleCreateProject = async () => {
    if (!newProjectTitle.trim()) {
      toast.error('Project title is required');
      return;
    }

    try {
      const newProject = await createProject.mutateAsync({
        title: newProjectTitle.trim(),
        description: newProjectDescription.trim() || undefined,
        priority: 5,
        target_due_date: newProjectDueDate || undefined,
      });
      
      // Select the newly created project
      setProjectId(newProject.id);
      setShowProjectModal(false);
      setNewProjectTitle('');
      setNewProjectDescription('');
      setNewProjectDueDate('');
      toast.success('Project created successfully');
      
      // Refetch projects to update the list
      refetchProjects();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to create project');
    }
  };

  const handleSubmit = async () => {
    if (mode === 'quick') {
      if (!task.trim()) {
        toast.error('Please enter a task');
        return;
      }

      // Build context for quick mode with deadline if provided
      const quickContext: Record<string, any> = {};
      if (dueDate) {
        quickContext.due_at = dueDate;
        quickContext.deadline_type = deadlineType || 'FLEX';
      }

      try {
        await createTask.mutateAsync({
          task: task.trim(),
          context: Object.keys(quickContext).length > 0 ? quickContext : undefined,
          actor_phone: (godfatherSettings.phone_numbers_csv.split(',')[0] || '').trim() || undefined,
          actor_email: godfatherSettings.email || undefined,
          project_id: projectId || undefined,
        });
        resetForm();
        toast.success('Task submitted successfully');
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Failed to submit task');
      }
    } else {
      // Detailed mode
      if (!title.trim() && !description.trim()) {
        toast.error('Please enter a title or description');
        return;
      }

      // Build task string from form fields
      const taskParts: string[] = [];
      if (title.trim()) {
        taskParts.push(title.trim());
      }
      if (description.trim()) {
        taskParts.push(description.trim());
      }
      const taskString = taskParts.join(': ');

      // Build context object
      const taskContext: Record<string, any> = {};
      if (context.trim()) {
        try {
          // Try to parse as JSON, otherwise use as plain text
          const parsed = JSON.parse(context.trim());
          Object.assign(taskContext, parsed);
        } catch {
          // Not JSON, store as additional context
          taskContext.additional_context = context.trim();
        }
      }
      if (title.trim()) {
        taskContext.title = title.trim();
      }
      if (description.trim()) {
        taskContext.description = description.trim();
      }
      // Add deadline info
      if (dueDate) {
        taskContext.due_at = dueDate;
        taskContext.deadline_type = deadlineType || 'FLEX';
      }

      try {
        await createTask.mutateAsync({
          task: taskString,
          context: Object.keys(taskContext).length > 0 ? taskContext : undefined,
          actor_phone: (godfatherSettings.phone_numbers_csv.split(',')[0] || '').trim() || undefined,
          actor_email: godfatherSettings.email || undefined,
          project_id: projectId || undefined,
        });
        resetForm();
        toast.success('Task created successfully');
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Failed to create task');
      }
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          {mode === 'quick' ? (
            <>
              <MessageSquare className="w-5 h-5" />
              New Task
            </>
          ) : (
            <>
              <FileText className="w-5 h-5" />
              New Task Details
            </>
          )}
        </CardTitle>
        <div className="flex items-center gap-2">
          {!showForm && (
            <Button
              onClick={() => {
                setShowForm(true);
                setMode('quick');
              }}
              variant="secondary"
              size="sm"
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Task
            </Button>
          )}
          {showForm && (
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setMode(mode === 'quick' ? 'detailed' : 'quick')}
                variant="ghost"
                size="sm"
              >
                {mode === 'quick' ? 'Add Details' : 'Simple Mode'}
              </Button>
              <Button
                onClick={resetForm}
                variant="ghost"
                size="sm"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      
      {showForm && (
        <CardContent className="space-y-4">
          {/* Project Selector - shown in both modes */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-300">
                <FolderOpen className="w-4 h-4 inline mr-1" />
                Attach to Project (Optional)
              </label>
              <Button
                type="button"
                onClick={() => setShowProjectModal(true)}
                variant="ghost"
                size="sm"
                className="text-purple-400 hover:text-purple-300 text-xs"
              >
                <Plus className="w-3 h-3 mr-1" />
                New Project
              </Button>
            </div>
            <select
              value={projectId}
              onChange={(e) => {
                if (e.target.value === '__create__') {
                  setShowProjectModal(true);
                  setProjectId('');
                } else {
                  setProjectId(e.target.value);
                }
              }}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
              disabled={createTask.isPending}
            >
              <option value="">No project</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.title}
                </option>
              ))}
              <option value="__create__" className="text-purple-400 font-medium">
                + Create New Project...
              </option>
            </select>
            {projects.length === 0 && (
              <p className="text-xs text-gray-500 mt-1">
                No active projects available. Click "New Project" to create one.
              </p>
            )}
          </div>

          {mode === 'quick' ? (
            <>
              <Textarea
                value={task}
                onChange={(e) => setTask(e.target.value)}
                placeholder="Example: Call John at +1234567890 and ask about the meeting..."
                rows={4}
                disabled={createTask.isPending}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    handleSubmit();
                  }
                }}
              />
              
              {/* Deadline Section - Quick Mode */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                    <Calendar className="w-4 h-4" />
                    Due Date (Optional)
                  </label>
                  <Input
                    type="datetime-local"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    disabled={createTask.isPending}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    Deadline Type
                  </label>
                  <select
                    value={deadlineType}
                    onChange={(e) => setDeadlineType(e.target.value as DeadlineType)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
                    disabled={createTask.isPending || !dueDate}
                  >
                    <option value="">Select type...</option>
                    <option value="HARD">🔴 Hard Deadline (Cannot miss)</option>
                    <option value="FLEX">🟡 Soft Deadline (Flexible)</option>
                  </select>
                  <p className="text-xs text-slate-500 mt-1">
                    {deadlineType === 'HARD' ? 'This deadline cannot be moved' : 
                     deadlineType === 'FLEX' ? 'This deadline can be adjusted if needed' : 
                     'Hard deadlines are immovable, soft deadlines are flexible'}
                  </p>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <p className="text-sm text-slate-400">
                  Press Cmd/Ctrl + Enter to submit
                </p>
                <Button
                  onClick={handleSubmit}
                  disabled={createTask.isPending || !task.trim()}
                  variant="primary"
                >
                  {createTask.isPending ? 'Processing...' : 'Create Task'}
                </Button>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Title *
                </label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Task title (e.g., Schedule doctor appointment)"
                  disabled={createTask.isPending}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Description *
                </label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detailed task description..."
                  rows={4}
                  disabled={createTask.isPending}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Notes / Requirements (Optional)
                </label>
                <Textarea
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  placeholder="e.g. High priority, budget $50, specific requirements..."
                  rows={3}
                  disabled={createTask.isPending}
                />
              </div>
              
              {/* Deadline Section - Detailed Mode */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                    <Calendar className="w-4 h-4" />
                    Due Date
                  </label>
                  <Input
                    type="datetime-local"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    disabled={createTask.isPending}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    Deadline Type
                  </label>
                  <select
                    value={deadlineType}
                    onChange={(e) => setDeadlineType(e.target.value as DeadlineType)}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
                    disabled={createTask.isPending || !dueDate}
                  >
                    <option value="">Select type...</option>
                    <option value="HARD">🔴 Hard Deadline (Cannot miss)</option>
                    <option value="FLEX">🟡 Soft Deadline (Flexible)</option>
                  </select>
                  <p className="text-xs text-slate-500 mt-1">
                    {deadlineType === 'HARD' ? 'This deadline cannot be moved' : 
                     deadlineType === 'FLEX' ? 'This deadline can be adjusted if needed' : 
                     'Hard deadlines are immovable, soft deadlines are flexible'}
                  </p>
                </div>
              </div>
              
              <div className="flex justify-end gap-2">
                <Button
                  onClick={resetForm}
                  variant="secondary"
                  disabled={createTask.isPending}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={createTask.isPending || (!title.trim() && !description.trim())}
                  variant="primary"
                >
                  {createTask.isPending ? 'Creating...' : 'Create Task'}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      )}
      
      {!showForm && (
        <CardContent>
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">Click "Add Task" to create a new task</p>
            <Button
              onClick={() => {
                setShowForm(true);
                setMode('quick');
              }}
              variant="primary"
              className="flex items-center gap-2 mx-auto"
            >
              <Plus className="w-4 h-4" />
              Add Task
            </Button>
          </div>
        </CardContent>
      )}

      {/* Create Project Modal */}
      {showProjectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Create New Project</CardTitle>
              <Button
                onClick={() => {
                  setShowProjectModal(false);
                  setNewProjectTitle('');
                  setNewProjectDescription('');
                }}
                variant="ghost"
                size="sm"
              >
                <X className="w-4 h-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Project Title *
                </label>
                <Input
                  value={newProjectTitle}
                  onChange={(e) => setNewProjectTitle(e.target.value)}
                  placeholder="Enter project title"
                  disabled={createProject.isPending}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !createProject.isPending && newProjectTitle.trim()) {
                      handleCreateProject();
                    }
                  }}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Description (Optional)
                </label>
                <Textarea
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                  placeholder="Project description..."
                  rows={3}
                  disabled={createProject.isPending}
                />
              </div>
              
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                  <Calendar className="w-4 h-4" />
                  Target Due Date
                </label>
                <Input
                  type="date"
                  value={newProjectDueDate}
                  onChange={(e) => setNewProjectDueDate(e.target.value)}
                  disabled={createProject.isPending}
                  className="w-full"
                />
                <p className="text-xs text-slate-500 mt-1">
                  When should this project be completed?
                </p>
              </div>
              
              <div className="flex justify-end gap-2">
                <Button
                  onClick={() => {
                    setShowProjectModal(false);
                    setNewProjectTitle('');
                    setNewProjectDescription('');
                    setNewProjectDueDate('');
                  }}
                  variant="secondary"
                  disabled={createProject.isPending}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateProject}
                  disabled={createProject.isPending || !newProjectTitle.trim()}
                  variant="primary"
                >
                  {createProject.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Project'
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </Card>
  );
};

