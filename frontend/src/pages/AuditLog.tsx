import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Loader2, FileText, Search, Filter, Sparkles, MessageSquare, Calendar, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { format } from 'date-fns';
import { tasksApi, messagingApi, memoryApi } from '@/lib/api';
import { Link } from 'react-router-dom';

interface AuditEntry {
  id: string;
  timestamp: string;
  type: 'task' | 'message' | 'scheduling' | 'memory';
  action: string;
  description: string;
  status: 'completed' | 'failed' | 'pending' | 'rejected';
  metadata?: Record<string, any>;
}

export const AuditLog = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'task' | 'message' | 'scheduling' | 'memory'>('all');
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'failed' | 'pending' | 'rejected'>('all');

  // Fetch tasks for audit log
  const { data: tasks = [], isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list(),
  });

  // Fetch recent interactions for audit log
  const { data: interactions, isLoading: interactionsLoading } = useQuery({
    queryKey: ['memory', 'all-interactions'],
    queryFn: () => memoryApi.getAllInteractions(100, 0),
  });

  const isLoading = tasksLoading || interactionsLoading;

  // Build audit entries from tasks
  const auditEntries: AuditEntry[] = [];

  tasks.forEach((task) => {
    if (task.status === 'completed' || task.status === 'failed' || task.status === 'rejected') {
      auditEntries.push({
        id: task.task_id,
        timestamp: task.updated_at,
        type: 'task',
        action: 'AI Task Execution',
        description: task.task,
        status: task.status === 'completed' ? 'completed' : task.status === 'failed' ? 'failed' : 'rejected',
        metadata: {
          task_id: task.task_id,
          result: task.result,
          error: task.error,
          planned_tool_calls: task.planned_tool_calls,
        },
      });
    }
  });

  // Add message interactions
  if (interactions?.items) {
    interactions.items
      .filter((interaction) => interaction.metadata?.direction === 'outbound')
      .forEach((interaction) => {
        auditEntries.push({
          id: interaction.id,
          timestamp: interaction.created_at,
          type: 'message',
          action: `Sent ${interaction.channel.toUpperCase()}`,
          description: interaction.raw_content.substring(0, 100),
          status: 'completed',
          metadata: {
            contact_id: interaction.metadata?.contact_id,
            contact_name: interaction.metadata?.contact_name,
            channel: interaction.channel,
          },
        });
      });
  }

  // Sort by timestamp (newest first)
  auditEntries.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  // Filter entries
  const filteredEntries = auditEntries.filter((entry) => {
    if (filterType !== 'all' && entry.type !== filterType) return false;
    if (filterStatus !== 'all' && entry.status !== filterStatus) return false;
    if (searchTerm && !entry.description.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'task':
        return <Sparkles className="w-4 h-4" />;
      case 'message':
        return <MessageSquare className="w-4 h-4" />;
      case 'scheduling':
        return <Calendar className="w-4 h-4" />;
      case 'memory':
        return <FileText className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="px-2 py-1 rounded text-xs bg-emerald-500/20 text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Completed
          </span>
        );
      case 'failed':
        return (
          <span className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400 flex items-center gap-1">
            <XCircle className="w-3 h-3" />
            Failed
          </span>
        );
      case 'pending':
        return (
          <span className="px-2 py-1 rounded text-xs bg-amber-500/20 text-amber-400 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Pending
          </span>
        );
      case 'rejected':
        return (
          <span className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400 flex items-center gap-1">
            <XCircle className="w-3 h-3" />
            Rejected
          </span>
        );
      default:
        return null;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'task':
        return 'text-purple-400 bg-purple-500/20';
      case 'message':
        return 'text-blue-400 bg-blue-500/20';
      case 'scheduling':
        return 'text-indigo-400 bg-indigo-500/20';
      case 'memory':
        return 'text-emerald-400 bg-emerald-500/20';
      default:
        return 'text-slate-400 bg-slate-500/20';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Audit Log</h1>
        <p className="text-white/80">
          Review all AI actions and system activities
        </p>
      </div>

      {/* Filters */}
      <Card className="bg-slate-900/50 border-slate-700 mb-6">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                type="text"
                placeholder="Search actions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as any)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
              >
                <option value="all">All Types</option>
                <option value="task">Tasks</option>
                <option value="message">Messages</option>
                <option value="scheduling">Scheduling</option>
                <option value="memory">Memory</option>
              </select>
            </div>
            <div>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as any)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
              >
                <option value="all">All Statuses</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit Entries */}
      {isLoading ? (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </CardContent>
        </Card>
      ) : filteredEntries.length === 0 ? (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
            <p className="text-slate-400 mb-2">
              {searchTerm || filterType !== 'all' || filterStatus !== 'all'
                ? 'No entries match your filters'
                : 'No audit entries yet'}
            </p>
            <p className="text-sm text-slate-500">
              AI actions and system activities will appear here
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredEntries.map((entry) => (
            <Card key={entry.id} className="bg-slate-900/50 border-slate-700">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className={`p-2 rounded-lg ${getTypeColor(entry.type)}`}>
                      {getTypeIcon(entry.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-white">{entry.action}</h3>
                        {getStatusBadge(entry.status)}
                        <span className="text-xs text-slate-400 capitalize">{entry.type}</span>
                      </div>
                      <p className="text-sm text-slate-300 mb-2">{entry.description}</p>
                      <div className="flex items-center gap-4 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {format(new Date(entry.timestamp), 'MMM d, yyyy h:mm a')}
                        </span>
                        {entry.metadata?.contact_name && (
                          <span>Contact: {entry.metadata.contact_name}</span>
                        )}
                        {entry.metadata?.channel && (
                          <span className="capitalize">Channel: {entry.metadata.channel}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Metadata Details */}
                {entry.metadata && (
                  <div className="mt-4 pt-4 border-t border-slate-700">
                    {entry.metadata.planned_tool_calls && entry.metadata.planned_tool_calls.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-slate-400 mb-2">Planned Actions:</p>
                        <div className="space-y-1">
                          {entry.metadata.planned_tool_calls.map((call: any, idx: number) => (
                            <div key={idx} className="text-xs text-slate-300 bg-slate-800/50 rounded p-2">
                              <span className="font-medium">{call.name}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {entry.metadata.error && (
                      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                        <p className="text-xs text-red-400 font-medium mb-1">Error:</p>
                        <p className="text-xs text-red-300">{entry.metadata.error}</p>
                      </div>
                    )}
                    {entry.metadata.result && (
                      <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
                        <p className="text-xs text-emerald-400 font-medium mb-1">Result:</p>
                        <pre className="text-xs text-emerald-300 overflow-x-auto">
                          {typeof entry.metadata.result === 'string'
                            ? entry.metadata.result
                            : JSON.stringify(entry.metadata.result, null, 2)}
                        </pre>
                      </div>
                    )}
                    {entry.metadata.contact_id && (
                      <div className="mt-2">
                        <Link to={`/contacts/${entry.metadata.contact_id}`}>
                          <Button variant="ghost" size="sm">
                            View Contact
                          </Button>
                        </Link>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Summary Stats */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-400 mb-1">Total Entries</p>
            <p className="text-2xl font-bold text-white">{auditEntries.length}</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-400 mb-1">Completed</p>
            <p className="text-2xl font-bold text-emerald-400">
              {auditEntries.filter((e) => e.status === 'completed').length}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-400 mb-1">Failed</p>
            <p className="text-2xl font-bold text-red-400">
              {auditEntries.filter((e) => e.status === 'failed').length}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-400 mb-1">Tasks</p>
            <p className="text-2xl font-bold text-purple-400">
              {auditEntries.filter((e) => e.type === 'task').length}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

