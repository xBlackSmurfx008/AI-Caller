import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useProjects, useProjectTasks, useCreateProjectTask, useScheduleTask, useExecuteAITask, usePEC, useExecutionReadyCheck, useGenerateProjectPlan, useProjectStakeholders, useAddStakeholder, useRemoveStakeholder, useContacts } from '@/lib/hooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { PECDashboard } from '@/components/PECDashboard';
import { Loader2, ArrowLeft, Plus, Calendar, Sparkles, CheckCircle2, Clock, AlertCircle, FileCheck, Users, X, UserPlus, Search, Mail, Phone, Building2 } from 'lucide-react';
import toast from 'react-hot-toast';

export const ProjectDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [showPEC, setShowPEC] = useState(false);
  const [showAddPerson, setShowAddPerson] = useState(false);
  const [personSearch, setPersonSearch] = useState('');
  const [selectedContact, setSelectedContact] = useState<string | null>(null);
  const [personRole, setPersonRole] = useState('');
  const [howTheyHelp, setHowTheyHelp] = useState('');
  const [howWeHelp, setHowWeHelp] = useState('');
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    estimated_minutes: 60,
    priority: 5,
    execution_mode: 'HUMAN' as 'HUMAN' | 'AI' | 'HYBRID',
  });

  const { data: project, isLoading: projectLoading } = useProjects('active');
  const projectData = project?.find(p => p.id === id);
  const { data: tasks = [], isLoading: tasksLoading, refetch } = useProjectTasks(id);
  const { data: pec } = usePEC(id);
  const { data: executionReady } = useExecutionReadyCheck(id);
  const { data: stakeholders = [], isLoading: stakeholdersLoading } = useProjectStakeholders(id);
  const { data: contacts = [] } = useContacts(personSearch);
  const createTask = useCreateProjectTask();
  const scheduleTask = useScheduleTask();
  const executeAI = useExecuteAITask();
  const generatePlan = useGenerateProjectPlan();
  const addStakeholder = useAddStakeholder();
  const removeStakeholder = useRemoveStakeholder();

  const handleCreateTask = async () => {
    if (!newTask.title.trim() || !id) {
      toast.error('Task title is required');
      return;
    }

    try {
      await createTask.mutateAsync({
        project_id: id,
        ...newTask,
      });
      toast.success('Task created successfully');
      setShowTaskForm(false);
      setNewTask({
        title: '',
        description: '',
        estimated_minutes: 60,
        priority: 5,
        execution_mode: 'HUMAN',
      });
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create task');
    }
  };

  const handleSchedule = async (taskId: string) => {
    try {
      const result = await scheduleTask.mutateAsync(taskId);
      if (result.success) {
        toast.success('Task scheduled successfully');
      } else {
        toast.error(result.error || 'Failed to schedule task');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to schedule task');
    }
  };

  const handleExecuteAI = async (taskId: string) => {
    try {
      const result = await executeAI.mutateAsync(taskId);
      if (result.success) {
        toast.success('AI task execution started');
        if (result.required_approvals && result.required_approvals.length > 0) {
          toast('Some actions require approval', { icon: '⚠️' });
        }
      } else {
        toast.error(result.error || 'Failed to execute task');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to execute task');
    }
  };

  const handleAddPerson = async () => {
    if (!selectedContact || !id) {
      toast.error('Please select a contact');
      return;
    }
    try {
      await addStakeholder.mutateAsync({
        projectId: id,
        data: {
          contact_id: selectedContact,
          role: personRole || undefined,
          how_they_help: howTheyHelp || undefined,
          how_we_help: howWeHelp || undefined,
        },
      });
      toast.success('Person added to project');
      setShowAddPerson(false);
      setSelectedContact(null);
      setPersonRole('');
      setHowTheyHelp('');
      setHowWeHelp('');
      setPersonSearch('');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add person');
    }
  };

  const handleRemovePerson = async (stakeholderId: string, name: string) => {
    if (!id) return;
    try {
      await removeStakeholder.mutateAsync({ projectId: id, stakeholderId });
      toast.success(`${name} removed from project`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to remove person');
    }
  };

  // Filter contacts not already stakeholders
  const availableContacts = contacts.filter(
    (c) => !stakeholders.some((s) => s.contact_id === c.id)
  );

  if (projectLoading || tasksLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      </div>
    );
  }

  if (!projectData) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <p className="text-red-600 font-semibold mb-2">Project not found</p>
            <Link to="/projects">
              <Button variant="primary">Back to Projects</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const statusColors = {
    todo: 'bg-gray-500/20 text-gray-400',
    scheduled: 'bg-blue-500/20 text-blue-400',
    in_progress: 'bg-yellow-500/20 text-yellow-400',
    blocked: 'bg-red-500/20 text-red-400',
    done: 'bg-green-500/20 text-green-400',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/projects" className="inline-flex items-center text-white/60 hover:text-white mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Projects
      </Link>

      <div className="mb-8">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{projectData.title}</h1>
            {projectData.description && (
              <p className="text-white/80">{projectData.description}</p>
            )}
          </div>
          <div className="flex gap-2">
            {tasks.length === 0 && projectData.description && (
              <Button
                onClick={async () => {
                  try {
                    await generatePlan.mutateAsync({
                      projectId: id!,
                      goalDescription: projectData.description!,
                      targetDueDate: projectData.target_due_date,
                      priority: projectData.priority,
                    });
                    toast.success('AI plan generated! Tasks created.');
                    refetch();
                  } catch (error: any) {
                    toast.error(error.response?.data?.detail || 'Failed to generate plan');
                  }
                }}
                variant="secondary"
                disabled={generatePlan.isPending}
              >
                {generatePlan.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                AI Plan This
              </Button>
            )}
            <Button
              onClick={() => setShowPEC(!showPEC)}
              variant="secondary"
              className={pec?.status === 'approved' ? 'border-emerald-500/50 text-emerald-400' : ''}
            >
              <FileCheck className="w-4 h-4 mr-2" />
              {pec ? (showPEC ? 'Hide' : 'Show') + ' PEC' : 'Generate PEC'}
              {pec?.status === 'approved' && <CheckCircle2 className="w-4 h-4 ml-2" />}
            </Button>
            <Button
              onClick={() => setShowTaskForm(true)}
              variant="primary"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Task
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm text-white/60 mb-4">
          <span>Status: <span className="capitalize text-white">{projectData.status}</span></span>
          <span>Priority: <span className="text-white">P{projectData.priority >= 8 ? '0' : projectData.priority >= 6 ? '1' : projectData.priority >= 4 ? '2' : '3'}</span></span>
          {projectData.target_due_date && (
            <span>Due: <span className="text-white">{new Date(projectData.target_due_date).toLocaleDateString()}</span></span>
          )}
          {executionReady && (
            <span className={`flex items-center gap-1 ${executionReady.execution_ready ? 'text-emerald-400' : 'text-amber-400'}`}>
              {executionReady.execution_ready ? (
                <><CheckCircle2 className="w-3 h-3" /> Ready</>
              ) : (
                <><AlertCircle className="w-3 h-3" /> {executionReady.reason || 'Not Ready'}</>
              )}
            </span>
          )}
        </div>

        {/* Progress Bar */}
        {tasks.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm text-slate-400 mb-2">
              <span>Project Progress</span>
              <span className="text-white font-semibold">
                {tasks.filter((t) => t.status === 'done').length} / {tasks.length} tasks completed
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-purple-600 to-indigo-600 h-3 rounded-full transition-all"
                style={{
                  width: `${(tasks.filter((t) => t.status === 'done').length / tasks.length) * 100}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* PEC Dashboard */}
      {showPEC && id && (
        <div className="mb-8">
          <PECDashboard 
            projectId={id} 
            onBeginExecution={() => {
              toast.success('Starting project execution...');
              // Could trigger task scheduling or AI execution here
            }}
          />
        </div>
      )}

      {/* People on this Project */}
      <Card className="mb-6 bg-slate-900/50 border-slate-700">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-400" />
            People ({stakeholders.length})
          </CardTitle>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowAddPerson(!showAddPerson)}
          >
            {showAddPerson ? <X className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
          </Button>
        </CardHeader>
        <CardContent>
          {/* Add Person Form */}
          {showAddPerson && (
            <div className="mb-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <h4 className="text-sm font-semibold text-white mb-3">Add Person to Project</h4>
              <div className="space-y-3">
                {/* Contact Search */}
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Search Contacts</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      value={personSearch}
                      onChange={(e) => setPersonSearch(e.target.value)}
                      placeholder="Search by name, email, or phone..."
                      className="pl-10"
                    />
                  </div>
                </div>
                
                {/* Contact Selection */}
                {personSearch && (
                  <div className="max-h-40 overflow-y-auto space-y-1 border border-slate-700 rounded-lg p-2 bg-slate-900/50">
                    {availableContacts.length === 0 ? (
                      <p className="text-sm text-slate-400 text-center py-2">No matching contacts found</p>
                    ) : (
                      availableContacts.slice(0, 8).map((contact) => (
                        <div
                          key={contact.id}
                          className={`p-2 rounded-lg cursor-pointer transition-colors ${
                            selectedContact === contact.id
                              ? 'bg-purple-600 text-white'
                              : 'hover:bg-slate-700 text-slate-200'
                          }`}
                          onClick={() => setSelectedContact(contact.id)}
                        >
                          <p className="font-medium text-sm">{contact.name}</p>
                          <p className="text-xs opacity-75">
                            {contact.organization || contact.email || contact.phone_number || 'No details'}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {selectedContact && (
                  <>
                    {/* Role */}
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Role (optional)</label>
                      <select
                        value={personRole}
                        onChange={(e) => setPersonRole(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm"
                      >
                        <option value="">Select a role...</option>
                        <option value="collaborator">Collaborator</option>
                        <option value="advisor">Advisor</option>
                        <option value="partner">Partner</option>
                        <option value="stakeholder">Stakeholder</option>
                        <option value="client">Client</option>
                        <option value="vendor">Vendor</option>
                      </select>
                    </div>

                    {/* How They Help */}
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">How they help (optional)</label>
                      <Input
                        value={howTheyHelp}
                        onChange={(e) => setHowTheyHelp(e.target.value)}
                        placeholder="e.g., Provides technical expertise..."
                      />
                    </div>

                    {/* How We Help */}
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">How we help them (optional)</label>
                      <Input
                        value={howWeHelp}
                        onChange={(e) => setHowWeHelp(e.target.value)}
                        placeholder="e.g., Marketing exposure..."
                      />
                    </div>
                  </>
                )}

                <div className="flex gap-2 pt-2">
                  <Button
                    onClick={handleAddPerson}
                    variant="primary"
                    size="sm"
                    disabled={!selectedContact || addStakeholder.isPending}
                  >
                    {addStakeholder.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-1" />
                    ) : (
                      <UserPlus className="w-4 h-4 mr-1" />
                    )}
                    Add Person
                  </Button>
                  <Button
                    onClick={() => {
                      setShowAddPerson(false);
                      setSelectedContact(null);
                      setPersonSearch('');
                      setPersonRole('');
                      setHowTheyHelp('');
                      setHowWeHelp('');
                    }}
                    variant="ghost"
                    size="sm"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Stakeholders List */}
          {stakeholdersLoading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
            </div>
          ) : stakeholders.length === 0 ? (
            <div className="text-center py-6">
              <Users className="w-10 h-10 text-slate-500 mx-auto mb-2" />
              <p className="text-slate-400 text-sm mb-2">No people added yet</p>
              <p className="text-slate-500 text-xs">
                Add contacts to help the AI understand who's involved in this project
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {stakeholders.map((stakeholder) => (
                <div
                  key={stakeholder.id}
                  className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-lg border border-slate-700 group"
                >
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-semibold text-sm">
                      {stakeholder.contact_name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Link 
                        to={`/contacts/${stakeholder.contact_id}`}
                        className="font-medium text-white hover:text-purple-400 transition-colors truncate"
                      >
                        {stakeholder.contact_name}
                      </Link>
                      {stakeholder.role && (
                        <span className="px-2 py-0.5 rounded text-xs bg-blue-500/20 text-blue-400 capitalize">
                          {stakeholder.role}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                      {stakeholder.contact_organization && (
                        <span className="flex items-center gap-1">
                          <Building2 className="w-3 h-3" />
                          {stakeholder.contact_organization}
                        </span>
                      )}
                      {stakeholder.contact_email && (
                        <span className="flex items-center gap-1">
                          <Mail className="w-3 h-3" />
                          {stakeholder.contact_email}
                        </span>
                      )}
                      {stakeholder.contact_phone && (
                        <span className="flex items-center gap-1">
                          <Phone className="w-3 h-3" />
                          {stakeholder.contact_phone}
                        </span>
                      )}
                    </div>
                    {(stakeholder.how_they_help || stakeholder.how_we_help) && (
                      <div className="mt-2 text-xs text-slate-400 space-y-1">
                        {stakeholder.how_they_help && (
                          <p><span className="text-slate-500">They help:</span> {stakeholder.how_they_help}</p>
                        )}
                        {stakeholder.how_we_help && (
                          <p><span className="text-slate-500">We help:</span> {stakeholder.how_we_help}</p>
                        )}
                      </div>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300 hover:bg-red-500/10"
                    onClick={() => handleRemovePerson(stakeholder.id, stakeholder.contact_name)}
                    disabled={removeStakeholder.isPending}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {showTaskForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Create New Task</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              placeholder="Task title"
              value={newTask.title}
              onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
            />
            <Textarea
              placeholder="Description (optional)"
              value={newTask.description}
              onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
              rows={3}
            />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-white/80 mb-1">Estimated Minutes</label>
                <Input
                  type="number"
                  value={newTask.estimated_minutes}
                  onChange={(e) => setNewTask({ ...newTask, estimated_minutes: parseInt(e.target.value) || 60 })}
                />
              </div>
              <div>
                <label className="block text-sm text-white/80 mb-1">Priority (1-10)</label>
                <Input
                  type="number"
                  min="1"
                  max="10"
                  value={newTask.priority}
                  onChange={(e) => setNewTask({ ...newTask, priority: parseInt(e.target.value) || 5 })}
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-white/80 mb-1">Execution Mode</label>
              <select
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                value={newTask.execution_mode}
                onChange={(e) => setNewTask({ ...newTask, execution_mode: e.target.value as any })}
              >
                <option value="HUMAN">Human</option>
                <option value="AI">AI</option>
                <option value="HYBRID">Hybrid</option>
              </select>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleCreateTask}
                variant="primary"
                disabled={createTask.isPending || !newTask.title.trim()}
              >
                {createTask.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : null}
                Create
              </Button>
              <Button
                onClick={() => {
                  setShowTaskForm(false);
                  setNewTask({
                    title: '',
                    description: '',
                    estimated_minutes: 60,
                    priority: 5,
                    execution_mode: 'HUMAN',
                  });
                }}
                variant="secondary"
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="text-2xl font-semibold text-white mb-4">Tasks</h2>
        {tasks.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">No tasks yet</p>
              <Button onClick={() => setShowTaskForm(true)} variant="primary">
                Create your first task
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {tasks.map((task) => (
              <Card key={task.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-white">{task.title}</h3>
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${statusColors[task.status]}`}>
                          {task.status}
                        </span>
                        {task.execution_mode !== 'HUMAN' && (
                          <span className="px-2 py-1 rounded text-xs bg-purple-500/20 text-purple-400">
                            {task.execution_mode}
                          </span>
                        )}
                      </div>
                      {task.description && (
                        <p className="text-sm text-white/60 mb-2">{task.description}</p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-white/50">
                        {task.estimated_minutes && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {task.estimated_minutes}m
                          </span>
                        )}
                        {task.due_at && (
                          <span>Due: {new Date(task.due_at).toLocaleDateString()}</span>
                        )}
                        {task.calendar_blocks && task.calendar_blocks.length > 0 && (
                          <span className="flex items-center gap-1 text-green-400">
                            <Calendar className="w-3 h-3" />
                            Scheduled
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {task.status !== 'done' && task.execution_mode !== 'HUMAN' && (
                        <Button
                          onClick={() => handleExecuteAI(task.id)}
                          variant="secondary"
                          size="sm"
                          disabled={executeAI.isPending}
                        >
                          {executeAI.isPending ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <Sparkles className="w-3 h-3" />
                          )}
                        </Button>
                      )}
                      {task.status === 'todo' && (
                        <Button
                          onClick={() => handleSchedule(task.id)}
                          variant="secondary"
                          size="sm"
                          disabled={scheduleTask.isPending}
                        >
                          {scheduleTask.isPending ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <Calendar className="w-3 h-3" />
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

