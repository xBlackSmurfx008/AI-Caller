import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Loader2, CheckCircle2, XCircle, MessageSquare, Sparkles, FileCheck, AlertTriangle, Clock, Target, Send, Users, Heart, Zap } from 'lucide-react';
import toast from 'react-hot-toast';
import { messagingApi, tasksApi, pecApi, relationshipOpsApi } from '@/lib/api';
import { usePendingApprovals, useApproveAction, useDismissAction, useExecuteAction } from '@/lib/hooks';
import { Link } from 'react-router-dom';
import { format, formatDistanceToNow } from 'date-fns';

interface ApprovalItem {
  id: string;
  type: 'message' | 'task' | 'pec' | 'relationship';
  title: string;
  description: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  metadata?: Record<string, any>;
}

export const Approvals = () => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [selectedType, setSelectedType] = useState<'all' | 'message' | 'task' | 'pec' | 'relationship'>('all');

  // Relationship actions hooks
  const { data: pendingRelationshipApprovals } = usePendingApprovals(50);
  const approveRelationshipAction = useApproveAction();
  const dismissRelationshipAction = useDismissAction();
  const executeRelationshipAction = useExecuteAction();

  // Fetch pending messages
  const { data: conversations = [] } = useQuery({
    queryKey: ['messaging', 'conversations'],
    queryFn: () => messagingApi.listConversations(),
  });

  // Fetch pending tasks
  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list(),
  });

  // Fetch pending PECs
  const { data: projects = [] } = useQuery({
    queryKey: ['projects', 'active'],
    queryFn: async () => {
      const { projectsApi } = await import('@/lib/api');
      return projectsApi.list({ status: 'active' });
    },
  });

  // Collect all approval items
  const [approvalItems, setApprovalItems] = useState<ApprovalItem[]>([]);

  // Fetch pending messages from conversations
  useEffect(() => {
    const fetchPendingMessages = async () => {
      const items: ApprovalItem[] = [];
      
      for (const conv of conversations) {
        if (conv.contact_id) {
          try {
            const conversationData = await messagingApi.getConversation(conv.contact_id, conv.channel);
            const pendingMessages = conversationData.messages.filter(
              (msg) => msg.status === 'pending' && msg.direction === 'outbound'
            );
            
            pendingMessages.forEach((msg) => {
              items.push({
                id: msg.id,
                type: 'message',
                title: `Message to ${conv.contact_name}`,
                description: msg.text_content || '[Media]',
                status: 'pending',
                created_at: msg.timestamp,
                metadata: {
                  contact_id: conv.contact_id,
                  contact_name: conv.contact_name,
                  channel: conv.channel,
                },
              });
            });
          } catch (error) {
            // Skip if error fetching conversation
          }
        }
      }
      
      // Add pending tasks
      tasks.forEach((task) => {
        if (task.status === 'awaiting_confirmation') {
          items.push({
            id: task.task_id,
            type: 'task',
            title: task.task,
            description: `Task requires confirmation before execution`,
            status: 'pending',
            created_at: task.created_at,
            metadata: {
              requires_confirmation: task.requires_confirmation,
              planned_tool_calls: task.planned_tool_calls,
              policy_reasons: task.policy_reasons,
            },
          });
        }
      });
      
      // Add pending PECs
      const pecPromises = projects.map(async (project) => {
        try {
          const pec = await pecApi.getCurrent(project.id);
          if (pec && pec.status === 'pending_approval') {
            return {
              id: pec.id,
              type: 'pec' as const,
              title: `PEC for ${project.title}`,
              description: `Project Execution Confirmation v${pec.version} requires approval`,
              status: 'pending' as const,
              created_at: pec.created_at,
              metadata: {
                project_id: project.id,
                execution_gate: pec.execution_gate,
                summary: pec.summary,
              },
            };
          }
        } catch (error) {
          // Skip if PEC doesn't exist
        }
        return null;
      });
      
      const pecResults = await Promise.all(pecPromises);
      pecResults.forEach((pec) => {
        if (pec) items.push(pec);
      });
      
      setApprovalItems(items);
    };
    
    if (conversations.length > 0 || tasks.length > 0 || projects.length > 0) {
      fetchPendingMessages();
    }
  }, [conversations, tasks, projects]);

  // Add pending tasks
  tasks.forEach((task) => {
    if (task.status === 'awaiting_confirmation') {
      approvalItems.push({
        id: task.task_id,
        type: 'task',
        title: task.task,
        description: `Task requires confirmation before execution`,
        status: 'pending',
        created_at: task.created_at,
        metadata: {
          requires_confirmation: task.requires_confirmation,
          planned_tool_calls: task.planned_tool_calls,
          policy_reasons: task.policy_reasons,
        },
      });
    }
  });

  // Add pending PECs
  projects.forEach(async (project) => {
    try {
      const pec = await pecApi.getCurrent(project.id);
      if (pec && pec.status === 'pending_approval') {
        approvalItems.push({
          id: pec.id,
          type: 'pec',
          title: `PEC for ${project.title}`,
          description: `Project Execution Confirmation v${pec.version} requires approval`,
          status: 'pending',
          created_at: pec.created_at,
          metadata: {
            project_id: project.id,
            execution_gate: pec.execution_gate,
            summary: pec.summary,
          },
        });
      }
    } catch (error) {
      // Skip if PEC doesn't exist or error
    }
  });

  const filteredItems = approvalItems.filter((item) => {
    if (filter === 'all') return true;
    return item.status === filter;
  });

  const handleApprove = async (item: ApprovalItem) => {
    try {
      if (item.type === 'message') {
        await messagingApi.approveMessage(item.id, true);
        toast.success('Message approved');
      } else if (item.type === 'task') {
        await tasksApi.confirm(item.id, true);
        toast.success('Task approved');
      } else if (item.type === 'pec') {
        await pecApi.approve(item.id, 'user');
        toast.success('PEC approved');
      }
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['pec'] });
      queryClient.invalidateQueries({ queryKey: ['messaging'] });
      // Refresh approval items
      setApprovalItems((prev) => prev.filter((i) => i.id !== item.id));
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to approve');
    }
  };

  const handleReject = async (item: ApprovalItem) => {
    try {
      if (item.type === 'message') {
        await messagingApi.approveMessage(item.id, false);
        toast.success('Message rejected');
      } else if (item.type === 'task') {
        await tasksApi.confirm(item.id, false);
        toast.success('Task rejected');
      } else if (item.type === 'pec') {
        await pecApi.reject(item.id);
        toast.success('PEC rejected');
      }
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['pec'] });
      queryClient.invalidateQueries({ queryKey: ['messaging'] });
      // Refresh approval items
      setApprovalItems((prev) => prev.filter((i) => i.id !== item.id));
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to reject');
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'message':
        return <MessageSquare className="w-5 h-5" />;
      case 'task':
        return <Sparkles className="w-5 h-5" />;
      case 'pec':
        return <FileCheck className="w-5 h-5" />;
      default:
        return <AlertTriangle className="w-5 h-5" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'message':
        return 'text-blue-400 bg-blue-500/20';
      case 'task':
        return 'text-purple-400 bg-purple-500/20';
      case 'pec':
        return 'text-indigo-400 bg-indigo-500/20';
      default:
        return 'text-slate-400 bg-slate-500/20';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Approvals</h1>
        <p className="text-white/80">
          Review and approve pending AI actions, messages, and project confirmations
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={filter === 'all' ? 'primary' : 'ghost'}
          onClick={() => setFilter('all')}
          size="sm"
        >
          All
        </Button>
        <Button
          variant={filter === 'pending' ? 'primary' : 'ghost'}
          onClick={() => setFilter('pending')}
          size="sm"
        >
          Pending
        </Button>
        <Button
          variant={filter === 'approved' ? 'primary' : 'ghost'}
          onClick={() => setFilter('approved')}
          size="sm"
        >
          Approved
        </Button>
        <Button
          variant={filter === 'rejected' ? 'primary' : 'ghost'}
          onClick={() => setFilter('rejected')}
          size="sm"
        >
          Rejected
        </Button>
      </div>

      {/* Approval Items */}
      {filteredItems.length === 0 ? (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <CheckCircle2 className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-400 mb-2">
              {filter === 'pending' ? 'No pending approvals' : 'No items found'}
            </p>
            <p className="text-sm text-slate-500">
              {filter === 'pending'
                ? 'All items have been reviewed. Check back later for new approvals.'
                : 'Try adjusting your filter.'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item) => (
            <Card
              key={item.id}
              className={`bg-slate-900/50 border-slate-700 ${
                item.status === 'pending' ? 'border-amber-500/30' : ''
              }`}
            >
              <CardContent className="pt-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className={`p-2 rounded-lg ${getTypeColor(item.type)}`}>
                      {getTypeIcon(item.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-white">{item.title}</h3>
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          item.status === 'pending'
                            ? 'bg-amber-500/20 text-amber-400'
                            : item.status === 'approved'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}>
                          {item.status === 'pending' && (
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              Pending
                            </span>
                          )}
                          {item.status === 'approved' && 'Approved'}
                          {item.status === 'rejected' && 'Rejected'}
                        </span>
                        <span className="text-xs text-slate-400 capitalize">
                          {item.type}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mb-3">{item.description}</p>
                      <div className="flex items-center gap-4 text-xs text-slate-500">
                        <span>
                          {format(new Date(item.created_at), 'MMM d, h:mm a')}
                        </span>
                        {item.metadata?.policy_reasons && item.metadata.policy_reasons.length > 0 && (
                          <span className="text-amber-400">
                            ⚠️ {item.metadata.policy_reasons.length} policy reason(s)
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                {item.status === 'pending' && (
                  <div className="flex items-center gap-3 pt-4 border-t border-slate-700">
                    {item.type === 'pec' && item.metadata?.project_id && (
                      <Link to={`/projects/${item.metadata.project_id}`}>
                        <Button variant="ghost" size="sm">
                          View Project
                        </Button>
                      </Link>
                    )}
                    <div className="flex gap-2 ml-auto">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleReject(item)}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        Reject
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleApprove(item)}
                      >
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        Approve
                      </Button>
                    </div>
                  </div>
                )}

                {/* Metadata Details */}
                {item.metadata?.planned_tool_calls && item.metadata.planned_tool_calls.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-700">
                    <p className="text-xs text-slate-400 mb-2">Planned Actions:</p>
                    <div className="space-y-1">
                      {item.metadata.planned_tool_calls.map((call: any, idx: number) => (
                        <div key={idx} className="text-xs text-slate-300 bg-slate-800/50 rounded p-2">
                          <span className="font-medium">{call.name}</span>
                          {call.arguments && (
                            <pre className="text-xs mt-1 text-slate-400">
                              {JSON.stringify(call.arguments, null, 2)}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

