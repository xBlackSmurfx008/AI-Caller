import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { contactsApi, memoryApi, messagingApi, relationshipOpsApi } from '@/lib/api';
import { Loader2, ArrowLeft, Phone, Mail, Building, MessageSquare, TrendingUp, TrendingDown, Minus, Calendar, Star, AlertCircle, Target, Clock, Sparkles, AlertTriangle, Send, CheckCircle2, Users, Heart } from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';

export const ContactDetail = () => {
  const { id } = useParams<{ id: string }>();

  const { data: contact, isLoading: contactLoading } = useQuery({
    queryKey: ['contacts', id],
    queryFn: () => contactsApi.get(id!),
    enabled: !!id,
  });

  const { data: interactions, isLoading: interactionsLoading } = useQuery({
    queryKey: ['memory', 'contact', id],
    queryFn: () => memoryApi.getContactInteractions(id!, 50, 0),
    enabled: !!id,
  });

  const { data: conversations = [] } = useQuery({
    queryKey: ['messaging', 'conversations'],
    queryFn: () => messagingApi.listConversations(),
    enabled: !!id,
  });

  const { data: pendingActions = [] } = useQuery({
    queryKey: ['relationship-ops', 'actions', { contact_id: id, status: 'pending' }],
    queryFn: () => relationshipOpsApi.listActions({ contact_id: id!, status: 'pending', limit: 10 }),
    enabled: !!id,
  });

  const contactConversations = conversations.filter(
    (conv) => conv.contact_id === id
  );

  if (contactLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-red-400 font-semibold mb-2">Contact not found</p>
            <Link to="/contacts">
              <Button variant="primary">Back to Contacts</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const relationshipScore = contact.relationship_score || 0;
  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-emerald-400';
    if (score >= 0.4) return 'text-amber-400';
    return 'text-red-400';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 0.7) return 'Strong';
    if (score >= 0.4) return 'Moderate';
    return 'Weak';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/contacts" className="inline-flex items-center text-white/60 hover:text-white mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Contacts
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Contact Info */}
        <Card className="bg-slate-900/50 border-slate-700 lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-white text-2xl">{contact.name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Relationship Score */}
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">Relationship Score</span>
                <span className={`text-lg font-bold ${getScoreColor(relationshipScore)}`}>
                  {Math.round(relationshipScore * 100)}%
                </span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2 mb-1">
                <div
                  className={`h-2 rounded-full transition-all ${
                    relationshipScore >= 0.7
                      ? 'bg-emerald-500'
                      : relationshipScore >= 0.4
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${relationshipScore * 100}%` }}
                />
              </div>
              <p className="text-xs text-slate-400">{getScoreLabel(relationshipScore)} relationship</p>
            </div>

            {/* Contact Details */}
            <div className="space-y-3">
              {contact.phone_number && (
                <div className="flex items-center gap-3 text-sm">
                  <Phone className="w-4 h-4 text-slate-400" />
                  <a href={`tel:${contact.phone_number}`} className="text-white hover:text-purple-400">
                    {contact.phone_number}
                  </a>
                </div>
              )}
              {contact.email && (
                <div className="flex items-center gap-3 text-sm">
                  <Mail className="w-4 h-4 text-slate-400" />
                  <a href={`mailto:${contact.email}`} className="text-white hover:text-purple-400">
                    {contact.email}
                  </a>
                </div>
              )}
              {contact.organization && (
                <div className="flex items-center gap-3 text-sm">
                  <Building className="w-4 h-4 text-slate-400" />
                  <span className="text-white">{contact.organization}</span>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="pt-4 border-t border-slate-700 space-y-2">
              <Link to={`/messaging?contact=${id}`}>
                <Button variant="primary" className="w-full">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Send Message
                </Button>
              </Link>
              <Link to="/command-center">
                <Button variant="secondary" className="w-full">
                  <Target className="w-4 h-4 mr-2" />
                  View in Command Center
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Pending Actions for this Contact */}
        {pendingActions.length > 0 && (
          <Card className="bg-slate-900/50 border-purple-500/30 lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                Suggested Actions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {pendingActions.slice(0, 3).map((action) => (
                  <div
                    key={action.id}
                    className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-3"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xs text-purple-400 uppercase font-medium">
                        {action.action_type.replace('_', ' ')}
                      </span>
                      {action.risk_flags && action.risk_flags.length > 0 && (
                        <span className="text-xs text-red-400 flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" />
                          Risk
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-white mb-2">{action.why_now}</p>
                    {action.draft_message && (
                      <div className="mt-2 p-2 bg-slate-800/50 rounded text-xs text-slate-300">
                        "{action.draft_message.slice(0, 100)}..."
                      </div>
                    )}
                    <div className="flex gap-2 mt-3">
                      <Link to="/command-center" className="flex-1">
                        <Button variant="primary" size="sm" className="w-full">
                          <Send className="w-3 h-3 mr-1" />
                          Review
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Interaction Timeline */}
          <Card className="bg-slate-900/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Interaction Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              {interactionsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                </div>
              ) : !interactions?.items || interactions.items.length === 0 ? (
                <div className="text-center py-8">
                  <MessageSquare className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
                  <p className="text-slate-400">No interactions yet</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {interactions.items.map((interaction) => (
                    <div
                      key={interaction.id}
                      className="bg-slate-800/50 rounded-lg p-4 border-l-4 border-purple-500"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium text-purple-400 uppercase">
                            {interaction.channel}
                          </span>
                          <span className="text-xs text-slate-400">
                            {interaction.metadata?.direction === 'outbound' ? 'Sent' : 'Received'}
                          </span>
                        </div>
                        <span className="text-xs text-slate-400">
                          {format(new Date(interaction.created_at), 'MMM d, h:mm a')}
                        </span>
                      </div>
                      <p className="text-sm text-white mb-2 line-clamp-3">
                        {interaction.raw_content}
                      </p>
                      {interaction.summary && (
                        <div className="mt-2 pt-2 border-t border-slate-700">
                          <p className="text-xs text-slate-400 mb-1">AI Summary:</p>
                          <p className="text-xs text-slate-300">{interaction.summary.summary}</p>
                          {interaction.summary.sentiment_explanation && (
                            <p className="text-xs text-slate-500 mt-1">
                              Sentiment: {interaction.summary.sentiment_explanation}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Conversations */}
          {contactConversations.length > 0 && (
            <Card className="bg-slate-900/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Active Conversations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {contactConversations.map((conv) => (
                    <Link
                      key={conv.conversation_id}
                      to={`/messaging?contact=${conv.contact_id}&channel=${conv.channel}`}
                      className="block bg-slate-800/50 rounded-lg p-3 hover:bg-slate-700/50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-sm font-medium text-white capitalize">
                            {conv.channel}
                          </span>
                          {conv.unread_count > 0 && (
                            <span className="ml-2 bg-red-500 text-white text-xs font-bold rounded-full px-2 py-0.5">
                              {conv.unread_count}
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-slate-400">
                          {format(new Date(conv.latest_message.timestamp), 'MMM d, h:mm a')}
                        </span>
                      </div>
                      <p className="text-sm text-slate-300 mt-1 line-clamp-1">
                        {conv.latest_message.text_content || '[Media]'}
                      </p>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Notes */}
          {contact.notes && (
            <Card className="bg-slate-900/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Notes</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-300 whitespace-pre-wrap">{contact.notes}</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

