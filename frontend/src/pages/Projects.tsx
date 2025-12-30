import { useState, useEffect, useRef } from 'react';
import { useProjects, useCreateProject, useScheduleAllTasks, useProjectTasks, useGenerateProjectPlan } from '@/lib/hooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Tooltip } from '@/components/ui/Tooltip';
import { Loader2, Plus, Calendar, Sparkles, AlertCircle, Zap, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

export const Projects = () => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newProject, setNewProject] = useState({
    title: '',
    description: '',
    priority: 5,
    target_due_date: '',
  });
  
  const { data: projects = [], isLoading, error, refetch } = useProjects('active');
  const createProject = useCreateProject();
  const scheduleAll = useScheduleAllTasks();

  // Keyboard shortcut: Enter to submit form
  useEffect(() => {
    if (!showCreateForm) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        if (newProject.title.trim()) {
          handleCreate();
        }
      }
      if (e.key === 'Escape') {
        setShowCreateForm(false);
        setNewProject({ title: '', description: '', priority: 5, target_due_date: '' });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showCreateForm, newProject.title]);

  const handleCreate = async () => {
    if (!newProject.title.trim()) {
      toast.error('Project title is required');
      return;
    }

    try {
      await createProject.mutateAsync({
        ...newProject,
        target_due_date: newProject.target_due_date || undefined,
      });
      toast.success('Project created successfully');
      setShowCreateForm(false);
      setNewProject({ title: '', description: '', priority: 5, target_due_date: '' });
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create project');
    }
  };

  const handleScheduleAll = async () => {
    try {
      const result = await scheduleAll.mutateAsync(false);
      if (result.success) {
        toast.success(`Scheduled ${result.scheduled} tasks. ${result.failed} failed.`);
        if (result.warnings && result.warnings.length > 0) {
          result.warnings.forEach((w: string) => toast(w, { icon: '⚠️' }));
        }
      } else {
        toast.error(result.error || 'Failed to schedule tasks');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to schedule tasks');
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="py-12 text-center space-y-4">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto" />
            <div>
              <p className="text-red-600 font-semibold mb-2">Failed to load projects</p>
              <Button onClick={() => refetch()} variant="primary" size="sm">
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Projects</h1>
          <p className="text-white/80">
            Manage your projects and tasks with AI-powered scheduling
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleScheduleAll}
            variant="secondary"
            disabled={scheduleAll.isPending}
          >
            {scheduleAll.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Calendar className="w-4 h-4 mr-2" />
            )}
            Schedule All
          </Button>
          <Button
            onClick={() => setShowCreateForm(true)}
            variant="primary"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>
      </div>

      {showCreateForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Create New Project</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Project Title *
              </label>
              <Input
                placeholder="Enter project title"
                value={newProject.title}
                onChange={(e) => setNewProject({ ...newProject, title: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Description (Optional)
              </label>
              <Textarea
                placeholder="Describe the project goals and scope..."
                value={newProject.description}
                onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                rows={3}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                  <Clock className="w-4 h-4" />
                  Target Due Date
                  <Tooltip content="Set a target completion date. The AI scheduler will prioritize tasks to meet this deadline." />
                </label>
                <Input
                  type="date"
                  value={newProject.target_due_date}
                  onChange={(e) => setNewProject({ ...newProject, target_due_date: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                />
                <p className="text-xs text-slate-500 mt-1">
                  When should this project be completed?
                </p>
              </div>
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                  Priority
                  <Tooltip content="P0 = Critical (urgent), P1 = High, P2 = Medium, P3 = Low. Higher priority projects are scheduled first." />
                </label>
                <select
                  value={newProject.priority}
                  onChange={(e) => setNewProject({ ...newProject, priority: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
                >
                  <option value={9}>P0 - Critical</option>
                  <option value={7}>P1 - High</option>
                  <option value={5}>P2 - Medium</option>
                  <option value={3}>P3 - Low</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <Button
                onClick={handleCreate}
                variant="primary"
                disabled={createProject.isPending || !newProject.title.trim()}
              >
                {createProject.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : null}
                Create Project
              </Button>
              <Button
                onClick={() => {
                  setShowCreateForm(false);
                  setNewProject({ title: '', description: '', priority: 5, target_due_date: '' });
                }}
                variant="secondary"
              >
                Cancel
              </Button>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              💡 Tip: Press <kbd className="px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded text-xs">⌘/Ctrl + Enter</kbd> to submit, <kbd className="px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded text-xs">Esc</kbd> to cancel
            </p>
          </CardContent>
        </Card>
      )}

      {projects.length === 0 ? (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <Sparkles className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
            <p className="text-slate-400 mb-4">No projects yet</p>
            <Button onClick={() => setShowCreateForm(true)} variant="primary">
              Create your first project
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
};

const ProjectCard = ({ project }: { project: any }) => {
  const { data: tasks = [] } = useProjectTasks(project.id);
  const generatePlan = useGenerateProjectPlan();

  const handleAIPlan = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!project.description) {
      toast.error('Please add a project description first');
      return;
    }

    try {
      await generatePlan.mutateAsync({
        projectId: project.id,
        goalDescription: project.description,
        targetDueDate: project.target_due_date,
        priority: project.priority,
      });
      toast.success('AI plan generated! Check the project for new tasks.');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate plan');
    }
  };

  // Calculate progress
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t: any) => t.status === 'done').length;
  const progress = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  return (
    <Link to={`/projects/${project.id}`}>
      <Card className="bg-slate-900/50 border-slate-700 hover:shadow-lg transition-shadow cursor-pointer h-full">
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-lg text-white">{project.title}</CardTitle>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${
              project.priority >= 8 ? 'bg-red-500/20 text-red-400' :
              project.priority >= 6 ? 'bg-orange-500/20 text-orange-400' :
              'bg-blue-500/20 text-blue-400'
            }`}>
              P{project.priority >= 8 ? '0' : project.priority >= 6 ? '1' : project.priority >= 4 ? '2' : '3'}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          {project.description && (
            <p className="text-sm text-slate-400 mb-3 line-clamp-2">
              {project.description}
            </p>
          )}
          
          {/* Progress Bar */}
          {totalTasks > 0 && (
            <div className="mb-3">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Progress</span>
                <span>{completedTasks}/{totalTasks} tasks</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-purple-600 to-indigo-600 h-2 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span className="capitalize">{project.status}</span>
            {project.target_due_date && (
              <span>{new Date(project.target_due_date).toLocaleDateString()}</span>
            )}
          </div>

          {/* AI Plan Button */}
          {totalTasks === 0 && project.description && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleAIPlan}
              disabled={generatePlan.isPending}
              className="w-full mt-2"
            >
              {generatePlan.isPending ? (
                <Loader2 className="w-3 h-3 animate-spin mr-2" />
              ) : (
                <Zap className="w-3 h-3 mr-2" />
              )}
              AI Plan This
            </Button>
          )}
        </CardContent>
      </Card>
    </Link>
  );
};

