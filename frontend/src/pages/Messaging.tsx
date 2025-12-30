import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { messagingApi, contactsApi, type Conversation, type MessageDraft, type Contact } from '@/lib/api';
import { Loader2, MessageSquare, Send, Check, X, Sparkles, Inbox, Phone, MessageCircle, Plus, Search, UserPlus } from 'lucide-react';
import { format } from 'date-fns';

export const Messaging = () => {
  const [selectedConversation, setSelectedConversation] = useState<{ contactId: string; channel: string } | null>(null);
  const [composeContact, setComposeContact] = useState<string>('');
  const [composeChannel, setComposeChannel] = useState<'sms' | 'whatsapp'>('sms');
  const [composeText, setComposeText] = useState('');
  const [showCompose, setShowCompose] = useState(false);
  const [showNewConversation, setShowNewConversation] = useState(false);
  const [contactSearch, setContactSearch] = useState('');

  const queryClient = useQueryClient();

  // Fetch conversations
  const { data: conversations = [], isLoading: conversationsLoading } = useQuery<Conversation[]>({
    queryKey: ['messaging', 'conversations'],
    queryFn: () => messagingApi.listConversations(),
    refetchInterval: 30000, // Poll every 30 seconds
  });

  // Fetch selected conversation messages
  const { data: conversationData, isLoading: messagesLoading } = useQuery({
    queryKey: ['messaging', 'conversation', selectedConversation?.contactId, selectedConversation?.channel],
    queryFn: () => messagingApi.getConversation(selectedConversation!.contactId, selectedConversation!.channel),
    enabled: !!selectedConversation,
    refetchInterval: 10000, // Poll every 10 seconds for active conversation
  });

  // Fetch contacts for compose
  const { data: contacts = [] } = useQuery<Contact[]>({
    queryKey: ['contacts'],
    queryFn: () => contactsApi.list(),
  });

  // Fetch drafts for selected contact
  const { data: drafts = [] } = useQuery<MessageDraft[]>({
    queryKey: ['messaging', 'drafts', selectedConversation?.contactId],
    queryFn: () => messagingApi.getDrafts(selectedConversation!.contactId, selectedConversation?.channel),
    enabled: !!selectedConversation && showCompose,
  });

  // Send message mutation
  const sendMessage = useMutation({
    mutationFn: (data: { contact_id: string; channel: string; text_content: string }) =>
      messagingApi.sendMessage(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messaging'] });
      toast.success('Message draft created. Please approve to send.');
      setComposeText('');
      setShowCompose(false);
    },
    onError: (error: unknown) => {
      const axiosErr = error as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr.response?.data?.detail || 'Failed to create message draft');
    },
  });

  // Approve message mutation
  const approveMessage = useMutation({
    mutationFn: ({ messageId, approved }: { messageId: string; approved: boolean }) =>
      messagingApi.approveMessage(messageId, approved),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['messaging'] });
      if (variables.approved) {
        toast.success('Message sent successfully');
      } else {
        toast.success('Message rejected');
      }
    },
    onError: (error: unknown) => {
      const axiosErr = error as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr.response?.data?.detail || 'Failed to approve message');
    },
  });

  // Mark as read mutation
  const markAsRead = useMutation({
    mutationFn: ({ contactId, channel }: { contactId: string; channel: string }) =>
      messagingApi.markAsRead(contactId, channel),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messaging'] });
    },
  });

  const handleSelectConversation = (contactId: string, channel: string) => {
    setSelectedConversation({ contactId, channel });
    setShowCompose(false);
    // Mark as read when opening
    markAsRead.mutate({ contactId, channel });
  };

  const handleSendDraft = (draft: MessageDraft) => {
    if (!selectedConversation) return;
    sendMessage.mutate({
      contact_id: selectedConversation.contactId,
      channel: draft.channel,
      text_content: draft.draft,
    });
  };

  const handleCompose = () => {
    if (!composeContact || !composeText.trim()) {
      toast.error('Please select a contact and enter a message');
      return;
    }
    sendMessage.mutate({
      contact_id: composeContact,
      channel: composeChannel,
      text_content: composeText,
    });
  };

  const selectedContact = contacts.find(c => c.id === selectedConversation?.contactId);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Messaging</h1>
        <p className="text-white/80">
          Unified inbox for SMS, MMS, and WhatsApp messages
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Conversations List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Inbox className="w-5 h-5" />
                  Conversations
                </CardTitle>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setShowNewConversation(true)}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  New
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {conversationsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="mb-4">No conversations yet</p>
                  <Button
                    variant="primary"
                    onClick={() => setShowNewConversation(true)}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Start New Conversation
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {conversations.map((conv) => (
                    <div
                      key={conv.conversation_id}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedConversation?.contactId === conv.contact_id &&
                        selectedConversation?.channel === conv.channel
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-800 hover:bg-gray-700 text-white'
                      }`}
                      onClick={() => conv.contact_id && handleSelectConversation(conv.contact_id, conv.channel)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            {conv.channel === 'whatsapp' ? (
                              <MessageCircle className="w-4 h-4 flex-shrink-0" />
                            ) : (
                              <Phone className="w-4 h-4 flex-shrink-0" />
                            )}
                            <span className="font-semibold truncate">{conv.contact_name}</span>
                            <span className="text-xs opacity-75">({conv.channel})</span>
                          </div>
                          <p className="text-sm opacity-90 truncate">
                            {conv.latest_message.text_content || '[Media]'}
                          </p>
                          <p className="text-xs opacity-75 mt-1">
                            {format(new Date(conv.latest_message.timestamp), 'MMM d, h:mm a')}
                          </p>
                        </div>
                        {conv.unread_count > 0 && (
                          <span className="ml-2 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                            {conv.unread_count}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Conversation View */}
        <div className="lg:col-span-2">
          {selectedConversation ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    {selectedConversation.channel === 'whatsapp' ? (
                      <MessageCircle className="w-5 h-5" />
                    ) : (
                      <Phone className="w-5 h-5" />
                    )}
                    {selectedContact?.name || 'Unknown Contact'}
                    <span className="text-sm font-normal text-gray-400">
                      ({selectedConversation.channel.toUpperCase()})
                    </span>
                  </CardTitle>
                  <div className="flex gap-2">
                    <Link to={`/contacts/${selectedConversation.contactId}`}>
                      <Button variant="ghost" size="sm">
                        View Contact
                      </Button>
                    </Link>
                    <Link to={`/trusted-list?add=${selectedConversation.contactId}`}>
                      <Button variant="ghost" size="sm">
                        Add to Trusted
                      </Button>
                    </Link>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowCompose(!showCompose)}
                    >
                      {showCompose ? 'Cancel' : 'Compose'}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {showCompose ? (
                  <div className="space-y-4">
                    {/* AI Drafts */}
                    {drafts.length > 0 && (
                      <div>
                        <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                          <Sparkles className="w-4 h-4" />
                          AI-Generated Drafts
                        </h3>
                        <div className="space-y-2 mb-4">
                          {drafts.map((draft, idx) => (
                            <div key={idx} className="bg-gray-800 p-3 rounded-lg">
                              <p className="text-white text-sm mb-2">{draft.draft}</p>
                              {draft.rationale && (
                                <p className="text-xs text-gray-400 mb-2">{draft.rationale}</p>
                              )}
                              {draft.risk_flags && draft.risk_flags.length > 0 && (
                                <div className="text-xs text-yellow-400 mb-2">
                                  ⚠️ {draft.risk_flags.join(', ')}
                                </div>
                              )}
                              <Button
                                size="sm"
                                onClick={() => handleSendDraft(draft)}
                                disabled={sendMessage.isPending}
                                className="w-full"
                              >
                                {sendMessage.isPending ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <>
                                    <Send className="w-4 h-4 mr-2" />
                                    Use This Draft
                                  </>
                                )}
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Manual Compose */}
                    <div>
                      <h3 className="text-sm font-semibold text-white mb-2">Compose Message</h3>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-1">
                            Channel
                          </label>
                          <div className="flex gap-2">
                            <Button
                              variant={composeChannel === 'sms' ? 'primary' : 'outline'}
                              size="sm"
                              onClick={() => setComposeChannel('sms')}
                              className="flex-1"
                            >
                              <Phone className="w-4 h-4 mr-2" />
                              SMS
                            </Button>
                            <Button
                              variant={composeChannel === 'whatsapp' ? 'primary' : 'outline'}
                              size="sm"
                              onClick={() => setComposeChannel('whatsapp')}
                              className="flex-1"
                            >
                              <MessageCircle className="w-4 h-4 mr-2" />
                              WhatsApp
                            </Button>
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-1">
                            Message
                          </label>
                          <Textarea
                            value={composeText}
                            onChange={(e) => setComposeText(e.target.value)}
                            placeholder="Type your message..."
                            rows={4}
                            className="bg-gray-800 text-white border-gray-700"
                          />
                        </div>
                        <Button
                          onClick={handleCompose}
                          disabled={!composeText.trim() || sendMessage.isPending}
                          className="w-full"
                        >
                          {sendMessage.isPending ? (
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                          ) : (
                            <Send className="w-4 h-4 mr-2" />
                          )}
                          Create Draft
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    {messagesLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                      </div>
                    ) : conversationData?.messages.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No messages in this conversation</p>
                      </div>
                    ) : (
                      <div className="space-y-4 max-h-[600px] overflow-y-auto">
                        {conversationData?.messages.map((msg) => (
                          <div
                            key={msg.id}
                            className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                          >
                            <div
                              className={`max-w-[80%] rounded-lg p-3 ${
                                msg.direction === 'outbound'
                                  ? 'bg-purple-600 text-white'
                                  : 'bg-gray-800 text-white'
                              }`}
                            >
                              <p className="text-sm whitespace-pre-wrap">{msg.text_content || '[Media]'}</p>
                              {msg.media_urls && msg.media_urls.length > 0 && (
                                <div className="mt-2 space-y-1">
                                  {msg.media_urls.map((url, idx) => (
                                    <a
                                      key={idx}
                                      href={url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs underline opacity-75"
                                    >
                                      Media {idx + 1}
                                    </a>
                                  ))}
                                </div>
                              )}
                              <div className="flex items-center justify-between mt-2">
                                <span className="text-xs opacity-75">
                                  {format(new Date(msg.timestamp), 'h:mm a')}
                                </span>
                                {msg.status && (
                                  <span className="text-xs opacity-75 ml-2">
                                    {msg.status === 'pending' && '⏳ Pending approval'}
                                    {msg.status === 'sent' && '✓ Sent'}
                                    {msg.status === 'delivered' && '✓✓ Delivered'}
                                    {msg.status === 'failed' && '✗ Failed'}
                                  </span>
                                )}
                                {msg.status === 'pending' && msg.direction === 'outbound' && (
                                  <div className="flex gap-1 ml-2">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="h-6 px-2"
                                      onClick={() => approveMessage.mutate({ messageId: msg.id, approved: true })}
                                      disabled={approveMessage.isPending}
                                    >
                                      <Check className="w-3 h-3" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="h-6 px-2"
                                      onClick={() => approveMessage.mutate({ messageId: msg.id, approved: false })}
                                      disabled={approveMessage.isPending}
                                    >
                                      <X className="w-3 h-3" />
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center text-slate-400">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="mb-4">Select a conversation to view messages</p>
                  <p className="text-sm text-slate-500">Or start a new conversation</p>
                  <Button
                    variant="primary"
                    className="mt-4"
                    onClick={() => setShowNewConversation(true)}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    New Conversation
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* New Conversation Modal */}
      {showNewConversation && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <UserPlus className="w-5 h-5" />
                  Start New Conversation
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowNewConversation(false);
                    setComposeContact('');
                    setComposeText('');
                    setContactSearch('');
                  }}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Contact Search */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Select Contact *
                </label>
                <div className="relative mb-2">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    value={contactSearch}
                    onChange={(e) => setContactSearch(e.target.value)}
                    placeholder="Search contacts..."
                    className="pl-10"
                  />
                </div>
                <div className="max-h-48 overflow-y-auto space-y-1 border border-slate-700 rounded-lg p-2 bg-slate-800/50">
                  {contacts
                    .filter(c => 
                      !contactSearch.trim() ||
                      c.name.toLowerCase().includes(contactSearch.toLowerCase()) ||
                      c.phone_number?.includes(contactSearch) ||
                      c.email?.toLowerCase().includes(contactSearch.toLowerCase())
                    )
                    .slice(0, 10)
                    .map(contact => (
                      <div
                        key={contact.id}
                        className={`p-2 rounded-lg cursor-pointer transition-colors ${
                          composeContact === contact.id
                            ? 'bg-purple-600 text-white'
                            : 'hover:bg-slate-700 text-slate-200'
                        }`}
                        onClick={() => setComposeContact(contact.id)}
                      >
                        <p className="font-medium">{contact.name}</p>
                        <p className="text-xs opacity-75">
                          {contact.phone_number || contact.email || 'No contact info'}
                        </p>
                      </div>
                    ))}
                  {contacts.length === 0 && (
                    <p className="text-slate-400 text-sm text-center py-4">
                      No contacts available. Add contacts first.
                    </p>
                  )}
                </div>
              </div>

              {/* Channel Selection */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Message Channel
                </label>
                <div className="flex gap-2">
                  <Button
                    variant={composeChannel === 'sms' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setComposeChannel('sms')}
                    className="flex-1"
                  >
                    <Phone className="w-4 h-4 mr-2" />
                    SMS
                  </Button>
                  <Button
                    variant={composeChannel === 'whatsapp' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setComposeChannel('whatsapp')}
                    className="flex-1"
                  >
                    <MessageCircle className="w-4 h-4 mr-2" />
                    WhatsApp
                  </Button>
                </div>
              </div>

              {/* Message */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Message *
                </label>
                <Textarea
                  value={composeText}
                  onChange={(e) => setComposeText(e.target.value)}
                  placeholder="Type your message..."
                  rows={4}
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowNewConversation(false);
                    setComposeContact('');
                    setComposeText('');
                    setContactSearch('');
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={() => {
                    if (!composeContact) {
                      toast.error('Please select a contact');
                      return;
                    }
                    if (!composeText.trim()) {
                      toast.error('Please enter a message');
                      return;
                    }
                    sendMessage.mutate({
                      contact_id: composeContact,
                      channel: composeChannel,
                      text_content: composeText.trim(),
                    });
                    setShowNewConversation(false);
                    setComposeContact('');
                    setComposeText('');
                    setContactSearch('');
                  }}
                  disabled={!composeContact || !composeText.trim() || sendMessage.isPending}
                >
                  {sendMessage.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Send className="w-4 h-4 mr-2" />
                  )}
                  Create Draft
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

