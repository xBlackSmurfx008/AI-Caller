import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { useCreateTask, useContacts, useMessageHistory } from '@/lib/hooks';
import { tasksApi } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { toast } from 'react-hot-toast';
import { MessageSquare, Mail, Send, Sparkles, Loader2, History, FileText, Edit2, X, Check } from 'lucide-react';
import { format } from 'date-fns';

type MessageType = 'email' | 'sms';
type MessageStatus = 'draft' | 'polishing' | 'ready' | 'sending' | 'sent' | 'error';

interface Message {
  id: string;
  type: MessageType;
  to: string;
  toName?: string;
  subject?: string;
  body: string;
  polishedBody?: string;
  status: MessageStatus;
  createdAt: string;
}

export const Messages = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [selectedHistoryMessage, setSelectedHistoryMessage] = useState<{id: string; channel: string; raw_content: string; created_at: string; metadata?: Record<string, unknown>; summary?: {summary?: string; sentiment_explanation?: string}} | null>(null);
  const [activeTab, setActiveTab] = useState<'drafts' | 'history'>('drafts');
  const [composeType, setComposeType] = useState<MessageType>('email');
  const [to, setTo] = useState('');
  const [toName, setToName] = useState('');
  const [subject, setSubject] = useState('');
  const [draftBody, setDraftBody] = useState('');
  const [polishing, setPolishing] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editBody, setEditBody] = useState('');
  const [polishError, setPolishError] = useState<string | null>(null);
  const [searchQuery] = useState('');
  const [dateFilter] = useState<'all' | 'today' | 'week' | 'month'>('all');
  const [polishedText, setPolishedText] = useState('');
  
  const createTask = useCreateTask();
  const { godfatherSettings } = useAppStore();
  const { data: contacts } = useContacts();
  const { data: messageHistoryData, isLoading: historyLoading } = useMessageHistory(100);
  const messageHistory = messageHistoryData?.items || [];

  const waitForTaskCompletion = async (taskId: string, autoApprove = true) => {
    const maxAttempts = 30;
    for (let attempts = 0; attempts < maxAttempts; attempts++) {
      const updatedTask = await tasksApi.get(taskId);

        if (updatedTask.status === 'awaiting_confirmation') {
        if (autoApprove) {
          try {
            await tasksApi.confirm(taskId, true);
          } catch (err: unknown) {
            const axiosErr = err as { response?: { data?: { detail?: string } } };
            throw new Error(axiosErr?.response?.data?.detail || 'Failed to approve task');
          }
          // Continue polling after approval attempt
          await new Promise((resolve) => setTimeout(resolve, 1000));
          continue;
        }
        return updatedTask;
      }

      if (['completed', 'failed', 'rejected'].includes(updatedTask.status)) {
        return updatedTask;
      }

      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    throw new Error('Task did not complete in time');
  };

  const handleCompose = () => {
    if (!to.trim() || !draftBody.trim()) {
      toast.error('Please fill in recipient and message');
      return;
    }

    // Find contact name if available
    const contact = contacts?.find(
      (c) => c.email === to || c.phone_number === to
    );
    const name = contact?.name || toName || to;

    const newMessage: Message = {
      id: Date.now().toString(),
      type: composeType,
      to,
      toName: name,
      subject: composeType === 'email' ? subject : undefined,
      body: draftBody,
      status: 'draft',
      createdAt: new Date().toISOString(),
    };

    setMessages([newMessage, ...messages]);
    setSelectedMessage(newMessage);
    setDraftBody('');
    setSubject('');
    setTo('');
    setToName('');
    toast.success('Message draft created');
  };

  const handleEdit = (message: Message) => {
    setEditingMessageId(message.id);
    setEditBody(message.body);
  };

  const handleSaveEdit = (messageId: string) => {
    setMessages(prev => prev.map(m => 
      m.id === messageId ? { ...m, body: editBody } : m
    ));
    setSelectedMessage(prev => prev?.id === messageId 
      ? { ...prev, body: editBody }
      : prev
    );
    setEditingMessageId(null);
    setEditBody('');
    toast.success('Draft updated');
  };

  const handleCancelEdit = () => {
    setEditingMessageId(null);
    setEditBody('');
  };

  const handlePolish = async (message: Message) => {
    if (!message.body.trim()) {
      toast.error('Message body is empty');
      return;
    }

    setPolishing(true);
    setPolishedText('');
    setPolishError(null);
    
    setMessages(prev => prev.map(m => 
      m.id === message.id ? { ...m, status: 'polishing' } : m
    ));
    setSelectedMessage(prev => prev?.id === message.id 
      ? { ...prev, status: 'polishing' }
      : prev
    );

    try {
      // Create a task to polish the message
      const polishPrompt = `Polish and improve this ${message.type === 'email' ? 'email' : 'SMS message'} for ${message.toName || message.to}:

${message.type === 'email' ? `Subject: ${message.subject || '(no subject)'}\n\n` : ''}Message:
${message.body}

Please:
1. Improve the tone and clarity
2. Make it professional but friendly
3. Ensure it's concise and effective
4. Return ONLY the polished message text (no explanations, no markdown)
${message.type === 'email' ? '5. If subject needs improvement, suggest a better one' : ''}

Return the polished message in this format:
${message.type === 'email' ? 'SUBJECT: [improved subject]\n\n' : ''}[polished message text]`;

      const taskResponse = await createTask.mutateAsync({
        task: polishPrompt,
        actor_phone: (godfatherSettings.phone_numbers_csv.split(',')[0] || '').trim() || undefined,
        actor_email: godfatherSettings.email || undefined,
      });

      if (taskResponse.requires_confirmation) {
        await tasksApi.confirm(taskResponse.task_id, true);
      }

      const completedTask = await waitForTaskCompletion(taskResponse.task_id, taskResponse.requires_confirmation);

      if (completedTask.status !== 'completed' || !completedTask.result?.response) {
        const errorMsg = completedTask.error || 'Failed to polish message';
        throw new Error(errorMsg);
      }

      const responseText = completedTask.result.response;

      // Parse the response
      let polishedSubject = message.subject;
      let polishedBody = responseText;

      if (message.type === 'email' && responseText.includes('SUBJECT:')) {
        const lines = responseText.split('\n');
        const subjectLine = lines.find(l => l.startsWith('SUBJECT:'));
        if (subjectLine) {
          polishedSubject = subjectLine.replace('SUBJECT:', '').trim();
          polishedBody = lines.slice(lines.indexOf(subjectLine) + 1).join('\n').trim();
        }
      }

      setPolishedText(polishedBody);

      // Update message
      const updatedMessage = {
        ...message,
        polishedBody,
        subject: polishedSubject || message.subject,
        status: 'ready' as MessageStatus
      };

      setMessages(prev => prev.map(m => 
        m.id === message.id ? updatedMessage : m
      ));

      setSelectedMessage(updatedMessage);

      setPolishing(false);
      toast.success('Message polished successfully');
    } catch (error: unknown) {
      setPolishing(false);
      const axiosErr = error as { response?: { data?: { detail?: string } } };
      const errorMsg = error instanceof Error ? error.message : (axiosErr?.response?.data?.detail || 'Failed to polish message');
      setPolishError(errorMsg);
      setMessages(prev => prev.map(m => 
        m.id === message.id ? { ...m, status: 'draft' } : m
      ));
      setSelectedMessage(prev => prev?.id === message.id 
        ? { ...prev, status: 'draft' }
        : prev
      );
      toast.error(errorMsg);
    }
  };

  const handleSend = async (message: Message) => {
    const bodyToSend = message.polishedBody || message.body;
    const subjectToSend = message.type === 'email' ? (message.subject || 'No Subject') : undefined;

    if (!bodyToSend.trim()) {
      toast.error('Message body is empty');
      return;
    }

    // Update message status
    setMessages(prev => prev.map(m => 
      m.id === message.id ? { ...m, status: 'sending' } : m
    ));

    try {
      let taskPrompt = '';
      if (message.type === 'email') {
        taskPrompt = `Send an email to ${message.toName || message.to} at ${message.to} with subject "${subjectToSend}" and body: ${bodyToSend}`;
      } else {
        taskPrompt = `Send an SMS to ${message.toName || message.to} at ${message.to} with message: ${bodyToSend}`;
      }

      const taskResponse = await createTask.mutateAsync({
        task: taskPrompt,
        actor_phone: (godfatherSettings.phone_numbers_csv.split(',')[0] || '').trim() || undefined,
        actor_email: godfatherSettings.email || undefined,
      });

      if (taskResponse.requires_confirmation) {
        await tasksApi.confirm(taskResponse.task_id, true);
      }

      const completedTask = await waitForTaskCompletion(taskResponse.task_id, taskResponse.requires_confirmation);

      if (completedTask.status !== 'completed') {
        throw new Error(completedTask.error || 'Message task failed or was rejected');
      }

      // Update message status
      setMessages(prev => prev.map(m => 
        m.id === message.id ? { ...m, status: 'sent' } : m
      ));
      
      setSelectedMessage(prev => prev?.id === message.id 
        ? { ...prev, status: 'sent' }
        : prev
      );

      toast.success(`${message.type === 'email' ? 'Email' : 'SMS'} sent successfully`);
    } catch (error) {
      setMessages(prev => prev.map(m => 
        m.id === message.id ? { ...m, status: 'error' } : m
      ));
      toast.error(error instanceof Error ? error.message : 'Failed to send message');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Messages</h1>
        <p className="text-white/80">
          Compose, polish, and send emails and SMS messages
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Compose Section */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Compose Message
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type
                </label>
                <div className="flex gap-2">
                  <Button
                    variant={composeType === 'email' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setComposeType('email')}
                    className="flex-1"
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Email
                  </Button>
                  <Button
                    variant={composeType === 'sms' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setComposeType('sms')}
                    className="flex-1"
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    SMS
                  </Button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  To {composeType === 'email' ? '(Email)' : '(Phone)'}
                </label>
                <Input
                  type={composeType === 'email' ? 'email' : 'tel'}
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  placeholder={composeType === 'email' ? 'email@example.com' : '+1234567890'}
                />
              </div>

              {composeType === 'email' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subject
                  </label>
                  <Input
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="Email subject"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message (Draft)
                </label>
                <Textarea
                  value={draftBody}
                  onChange={(e) => setDraftBody(e.target.value)}
                  placeholder="Write your message draft here..."
                  rows={6}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Write a rough draft. AI will polish it before sending.
                </p>
              </div>

              <Button
                onClick={handleCompose}
                disabled={!to.trim() || !draftBody.trim()}
                className="w-full"
              >
                Create Draft
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Messages List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Messages</CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant={activeTab === 'drafts' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setActiveTab('drafts')}
                    className="flex items-center gap-2"
                  >
                    <FileText className="w-4 h-4" />
                    Drafts
                  </Button>
                  <Button
                    variant={activeTab === 'history' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setActiveTab('history')}
                    className="flex items-center gap-2"
                  >
                    <History className="w-4 h-4" />
                    History
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {activeTab === 'drafts' ? (
                messages.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No drafts yet. Create a draft to get started.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                          selectedMessage?.id === message.id
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedMessage(message)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              {message.type === 'email' ? (
                                <Mail className="w-4 h-4 text-gray-500" />
                              ) : (
                                <MessageSquare className="w-4 h-4 text-gray-500" />
                              )}
                              <span className="font-semibold text-gray-900">
                                {message.toName || message.to}
                              </span>
                              <span className="text-xs text-gray-500">
                                ({message.type.toUpperCase()})
                              </span>
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${
                                  message.status === 'sent'
                                    ? 'bg-green-100 text-green-800'
                                    : message.status === 'ready'
                                    ? 'bg-blue-100 text-blue-800'
                                    : message.status === 'draft'
                                    ? 'bg-gray-100 text-gray-800'
                                    : message.status === 'sending' || message.status === 'polishing'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-red-100 text-red-800'
                                }`}
                              >
                                {message.status}
                              </span>
                            </div>
                            {message.type === 'email' && message.subject && (
                              <p className="text-sm font-medium text-gray-700 mb-1">
                                {message.subject}
                              </p>
                            )}
                            <p className="text-sm text-gray-600 line-clamp-2">
                              {message.polishedBody || message.body}
                            </p>
                          </div>
                        </div>

                        {selectedMessage?.id === message.id && (
                          <div className="mt-4 pt-4 border-t space-y-3">
                            <div>
                              <div className="flex items-center justify-between mb-1">
                                <label className="block text-xs font-medium text-gray-700">
                                  Original Draft
                                </label>
                                {message.status !== 'sent' && !editingMessageId && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleEdit(message);
                                    }}
                                    className="h-6 px-2 text-xs"
                                  >
                                    <Edit2 className="w-3 h-3 mr-1" />
                                    Edit
                                  </Button>
                                )}
                              </div>
                              {editingMessageId === message.id ? (
                                <div className="space-y-2">
                                  <Textarea
                                    value={editBody}
                                    onChange={(e) => setEditBody(e.target.value)}
                                    rows={4}
                                    className="text-sm"
                                  />
                                  <div className="flex gap-2">
                                    <Button
                                      size="sm"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleSaveEdit(message.id);
                                      }}
                                      className="flex items-center gap-1"
                                    >
                                      <Check className="w-3 h-3" />
                                      Save
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleCancelEdit();
                                      }}
                                      className="flex items-center gap-1"
                                    >
                                      <X className="w-3 h-3" />
                                      Cancel
                                    </Button>
                                  </div>
                                </div>
                              ) : (
                                <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded whitespace-pre-wrap">
                                  {message.body}
                                </div>
                              )}
                            </div>

                            {message.polishedBody && (
                              <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1 flex items-center gap-2">
                                  <Sparkles className="w-3 h-3 text-purple-600" />
                                  AI Polished Version
                                </label>
                                <div className="text-sm text-gray-900 bg-gradient-to-r from-purple-50 to-blue-50 p-3 rounded border border-purple-200">
                                  {message.type === 'email' && message.subject && (
                                    <div className="mb-2 pb-2 border-b border-purple-200">
                                      <span className="font-semibold">Subject: </span>
                                      <span>{message.subject}</span>
                                    </div>
                                  )}
                                  <div className="whitespace-pre-wrap">{message.polishedBody}</div>
                                </div>
                              </div>
                            )}

                            {message.status === 'polishing' && (
                              <div className="flex items-center gap-2 text-sm text-yellow-700 bg-yellow-50 p-2 rounded">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>AI is polishing your message...</span>
                              </div>
                            )}
                            
                            {message.status === 'sending' && (
                              <div className="flex items-center gap-2 text-sm text-blue-700 bg-blue-50 p-2 rounded">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>Sending {message.type === 'email' ? 'email' : 'SMS'}...</span>
                              </div>
                            )}

                            {polishError && selectedMessage?.id === message.id && (
                              <div className="bg-red-50 border border-red-200 rounded p-3 space-y-2">
                                <div className="flex items-center gap-2 text-sm text-red-800">
                                  <X className="w-4 h-4" />
                                  <span className="font-medium">Polish failed</span>
                                </div>
                                <p className="text-xs text-red-700">{polishError}</p>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setPolishError(null);
                                    handlePolish(message);
                                  }}
                                  className="flex items-center gap-2 mt-2"
                                >
                                  <Sparkles className="w-4 h-4" />
                                  Retry Polish
                                </Button>
                              </div>
                            )}

                            <div className="flex gap-2 flex-wrap">
                              {!message.polishedBody && message.status !== 'polishing' && message.status !== 'sent' && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setPolishError(null);
                                    handlePolish(message);
                                  }}
                                  disabled={polishing}
                                  className="flex items-center gap-2"
                                >
                                  {polishing && selectedMessage?.id === message.id ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <Sparkles className="w-4 h-4" />
                                  )}
                                  Polish with AI
                                </Button>
                              )}
                              {(message.polishedBody || message.body) && message.status !== 'sent' && message.status !== 'polishing' && (
                                <Button
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSend(message);
                                  }}
                                  disabled={message.status === 'sending'}
                                  className="flex items-center gap-2"
                                >
                                  {message.status === 'sending' ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <Send className="w-4 h-4" />
                                  )}
                                  Send {message.type === 'email' ? 'Email' : 'SMS'}
                                </Button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )
              ) : (
                // History Tab
                historyLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                  </div>
                ) : !messageHistory || messageHistory.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No message history yet. Messages will appear here after being sent.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {(() => {
                      // Filter messages by search query and date
                      let filtered = messageHistory;
                      
                      // Apply search filter
                      if (searchQuery.trim()) {
                        const query = searchQuery.toLowerCase();
                        filtered = filtered.filter(interaction => {
                          const contactName = (interaction.metadata?.contact_name || '').toLowerCase();
                          const content = interaction.raw_content.toLowerCase();
                          const subject = (interaction.metadata?.subject || '').toLowerCase();
                          return contactName.includes(query) || 
                                 content.includes(query) || 
                                 subject.includes(query);
                        });
                      }
                      
                      // Apply date filter
                      if (dateFilter !== 'all') {
                        const now = new Date();
                        const filterDate = new Date();
                        
                        switch (dateFilter) {
                          case 'today':
                            filterDate.setHours(0, 0, 0, 0);
                            break;
                          case 'week':
                            filterDate.setDate(now.getDate() - 7);
                            break;
                          case 'month':
                            filterDate.setMonth(now.getMonth() - 1);
                            break;
                        }
                        
                        filtered = filtered.filter(interaction => {
                          const interactionDate = new Date(interaction.created_at);
                          return interactionDate >= filterDate;
                        });
                      }
                      
                      if (filtered.length === 0) {
                        return (
                          <div className="text-center py-8 text-gray-500">
                            <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                            <p>No messages found matching your filters.</p>
                          </div>
                        );
                      }
                      
                      return filtered.map((interaction) => {
                      const isEmail = interaction.channel === 'email';
                      const contactName = interaction.metadata?.contact_name || 'Unknown';
                      const direction = interaction.metadata?.direction || 'outbound';
                      const isOutbound = direction === 'outbound';
                      const subject = interaction.metadata?.subject;
                      
                      // Extract message content from raw_content
                      let messageContent = interaction.raw_content;
                      if (isEmail && messageContent.includes('Subject:')) {
                        const lines = messageContent.split('\n');
                        const subjectIndex = lines.findIndex(l => l.startsWith('Subject:'));
                        if (subjectIndex !== -1) {
                          messageContent = lines.slice(subjectIndex + 1).join('\n').trim();
                        }
                      }
                      
                      return (
                        <div
                          key={interaction.id}
                          className={`flex ${isOutbound ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[85%] rounded-lg p-4 cursor-pointer transition-colors ${
                              selectedHistoryMessage?.id === interaction.id
                                ? 'ring-2 ring-purple-500'
                                : ''
                            } ${
                              isOutbound
                                ? 'bg-purple-600 text-white'
                                : 'bg-gray-100 text-gray-900'
                            }`}
                            onClick={() => setSelectedHistoryMessage(interaction)}
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-2 flex-wrap">
                                  {isEmail ? (
                                    <Mail className={`w-4 h-4 flex-shrink-0 ${isOutbound ? 'text-white/70' : 'text-gray-500'}`} />
                                  ) : (
                                    <MessageSquare className={`w-4 h-4 flex-shrink-0 ${isOutbound ? 'text-white/70' : 'text-gray-500'}`} />
                                  )}
                                  <span className={`font-semibold ${isOutbound ? 'text-white' : 'text-gray-900'}`}>
                                    {isOutbound ? `You → ${contactName}` : `${contactName} → You`}
                                  </span>
                                  <span className={`text-xs ${isOutbound ? 'text-white/70' : 'text-gray-500'}`}>
                                    ({interaction.channel.toUpperCase()})
                                  </span>
                                </div>
                                <div className={`text-xs mb-2 ${isOutbound ? 'text-white/70' : 'text-gray-500'}`}>
                                  {format(new Date(interaction.created_at), 'MMM d, yyyy · h:mm a')}
                                </div>
                                {isEmail && subject && (
                                  <p className={`text-sm font-medium mb-1 ${isOutbound ? 'text-white/90' : 'text-gray-700'}`}>
                                    {subject}
                                  </p>
                                )}
                                <p className={`text-sm line-clamp-2 ${isOutbound ? 'text-white/90' : 'text-gray-600'}`}>
                                  {messageContent}
                                </p>
                                {interaction.summary && (
                                  <div className={`mt-2 pt-2 border-t ${isOutbound ? 'border-white/20' : 'border-gray-200'}`}>
                                    <p className={`text-xs italic ${isOutbound ? 'text-white/70' : 'text-gray-500'}`}>
                                      {interaction.summary.summary}
                                    </p>
                                  </div>
                                )}
                              </div>
                            </div>

                            {selectedHistoryMessage?.id === interaction.id && (
                              <div className={`mt-4 pt-4 border-t space-y-3 ${isOutbound ? 'border-white/20' : 'border-gray-200'}`}>
                                <div>
                                  <label className={`block text-xs font-medium mb-1 ${isOutbound ? 'text-white/80' : 'text-gray-700'}`}>
                                    Full Message
                                  </label>
                                  <div className={`text-sm p-3 rounded whitespace-pre-wrap ${isOutbound ? 'bg-purple-700/50 text-white' : 'bg-white text-gray-900'}`}>
                                    {messageContent}
                                  </div>
                                </div>
                                
                                {interaction.summary && (
                                  <div>
                                    <label className={`block text-xs font-medium mb-1 ${isOutbound ? 'text-white/80' : 'text-gray-700'}`}>
                                      AI Summary
                                    </label>
                                    <div className={`text-sm p-3 rounded ${isOutbound ? 'bg-purple-700/50 text-white' : 'bg-blue-50 text-gray-700'}`}>
                                      <p className="mb-2">{interaction.summary.summary}</p>
                                      {interaction.summary.sentiment_explanation && (
                                        <p className={`text-xs italic ${isOutbound ? 'text-white/70' : 'text-gray-600'}`}>
                                          Sentiment: {interaction.summary.sentiment_explanation}
                                        </p>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                      });
                    })()}
                  </div>
                )
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

