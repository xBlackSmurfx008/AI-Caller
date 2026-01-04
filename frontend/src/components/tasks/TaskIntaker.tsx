import { useState, useRef, useEffect, useCallback } from 'react';
import { useCreateTask } from '@/lib/hooks';
import { chatApi } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { toast } from 'react-hot-toast';
import { 
  Mic, 
  MicOff, 
  Send, 
  Loader2, 
  Sparkles,
  Bot,
  User,
  Volume2,
  VolumeX,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Clock,
  AlertTriangle,
  X
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  status?: 'pending' | 'completed' | 'failed' | 'awaiting_confirmation';
  taskId?: string;
  toolCalls?: { name: string; arguments: Record<string, any> }[];
}

// Check for speech recognition support
const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
const speechSynthesis = window.speechSynthesis;

export const TaskIntaker = () => {
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hi! I'm your AI assistant. Tell me what you need—type or use voice. I can make calls, send messages, schedule events, and more.",
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  
  const recognitionRef = useRef<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const createTask = useCreateTask();

  // Load (or create) a durable chat session on mount
  useEffect(() => {
    let cancelled = false;

    async function initSession() {
      try {
        // Backwards compatible key migration:
        // - old key: chat_session_id
        // - new key: chat_session_id_global
        const legacy = localStorage.getItem('chat_session_id');
        if (legacy && !localStorage.getItem('chat_session_id_global')) {
          localStorage.setItem('chat_session_id_global', legacy);
          localStorage.removeItem('chat_session_id');
        }

        const existing = localStorage.getItem('chat_session_id_global');
        if (existing) {
          const detail = await chatApi.getSession(existing, 200);
          if (cancelled) return;
          setChatSessionId(detail.session.id);

          // Hydrate local UI messages from persisted history
          const hydrated: Message[] = detail.messages
            .filter((m) => m.role === 'user' || m.role === 'assistant')
            .map((m) => ({
              id: m.id,
              role: m.role as 'user' | 'assistant',
              content: m.content,
              timestamp: new Date(m.created_at),
            }));

          if (hydrated.length > 0) {
            setMessages(hydrated);
          }
          return;
        }

        const created = await chatApi.createSession({ scope_type: 'global' });
        if (cancelled) return;
        localStorage.setItem('chat_session_id_global', created.id);
        setChatSessionId(created.id);
      } catch (e) {
        // If session init fails, fall back to non-persistent mode.
        console.warn('Failed to init chat session', e);
      }
    }

    initSession();
    return () => {
      cancelled = true;
    };
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize speech recognition
  useEffect(() => {
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0])
          .map((result: any) => result.transcript)
          .join('');
        
        setInputText(transcript);
        
        // If final result, auto-submit
        if (event.results[0].isFinal) {
          // Small delay to show the text
          setTimeout(() => {
            handleSubmit(transcript);
          }, 500);
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        if (event.error === 'not-allowed') {
          toast.error('Microphone access denied. Please allow microphone access.');
        }
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  const toggleListening = useCallback(() => {
    if (!SpeechRecognition) {
      toast.error('Voice input not supported in this browser');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      setInputText('');
      recognitionRef.current?.start();
      setIsListening(true);
    }
  }, [isListening]);

  const speakText = useCallback((text: string) => {
    if (!speechSynthesis || !voiceEnabled) return;
    
    // Cancel any ongoing speech
    speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    speechSynthesis.speak(utterance);
  }, [voiceEnabled]);

  const handleSubmit = async (text?: string) => {
    const messageText = text || inputText.trim();
    if (!messageText) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');

    // Add thinking indicator
    const thinkingId = `thinking-${Date.now()}`;
    setMessages(prev => [...prev, {
      id: thinkingId,
      role: 'assistant',
      content: 'Thinking...',
      timestamp: new Date(),
      status: 'pending',
    }]);

    try {
      // Ensure a chat session exists before sending the task
      let sid = chatSessionId;
      if (!sid) {
        const created = await chatApi.createSession({ scope_type: 'global' });
        sid = created.id;
        localStorage.setItem('chat_session_id_global', sid);
        setChatSessionId(sid);
      }

      const result = await createTask.mutateAsync({
        task: messageText,
        chat_session_id: sid,
      });

      // Remove thinking message
      setMessages(prev => prev.filter(m => m.id !== thinkingId));

      // Determine status message
      let statusIcon = '✅';
      let statusText = '';
      
      if (result.status === 'awaiting_confirmation') {
        statusIcon = '⏳';
        statusText = '\n\n_This action requires your approval._';
      } else if (result.status === 'completed') {
        statusIcon = '✅';
      } else if (result.status === 'failed') {
        statusIcon = '❌';
      }

      // Build response content
      let responseContent = result.result?.response || 
        (result.status === 'awaiting_confirmation' 
          ? "I've planned this task. It requires your approval before I can execute it."
          : 'Task processed.');
      
      if (result.planned_tool_calls?.length > 0) {
        const toolNames = result.planned_tool_calls.map((t: any) => t.name).join(', ');
        responseContent += `\n\n📋 **Planned actions:** ${toolNames}`;
      }
      
      responseContent += statusText;

      // Add assistant response
      const assistantMessage: Message = {
        id: `response-${Date.now()}`,
        role: 'assistant',
        content: responseContent,
        timestamp: new Date(),
        status: result.status,
        taskId: result.task_id,
        toolCalls: result.planned_tool_calls,
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Speak the response if voice is enabled
      if (voiceEnabled && result.result?.response) {
        speakText(result.result.response);
      }

    } catch (error) {
      // Remove thinking message
      setMessages(prev => prev.filter(m => m.id !== thinkingId));
      
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
        status: 'failed',
      };
      setMessages(prev => [...prev, errorMessage]);
      
      toast.error('Failed to process task');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const clearChat = () => {
    // Start a brand new durable session (do not delete the old one by default)
    (async () => {
      try {
        const created = await chatApi.createSession({ scope_type: 'global' });
        localStorage.setItem('chat_session_id_global', created.id);
        setChatSessionId(created.id);
      } catch (e) {
        console.warn('Failed to create new chat session', e);
      }
    })();

    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: "Chat cleared. How can I help you?",
        timestamp: new Date(),
      },
    ]);
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'awaiting_confirmation':
        return <Clock className="w-4 h-4 text-amber-400" />;
      case 'failed':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'pending':
        return <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />;
      default:
        return null;
    }
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div 
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-purple-900/80 to-indigo-900/80 border border-purple-500/30 rounded-t-xl cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">AI Command Center</h2>
            <p className="text-xs text-purple-200/70">Type or speak your commands</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              setVoiceEnabled(!voiceEnabled);
            }}
            className="text-purple-300 hover:text-white"
            title={voiceEnabled ? 'Disable voice responses' : 'Enable voice responses'}
          >
            {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              clearChat();
            }}
            className="text-purple-300 hover:text-white"
            title="Clear chat"
          >
            <X className="w-4 h-4" />
          </Button>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-purple-300" />
          ) : (
            <ChevronDown className="w-5 h-5 text-purple-300" />
          )}
        </div>
      </div>

      {/* Chat Area */}
      {isExpanded && (
        <div className="border-x border-b border-purple-500/30 rounded-b-xl bg-slate-900/95 backdrop-blur-sm">
          {/* Messages */}
          <div className="h-64 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-purple-500/30 scrollbar-track-transparent">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === 'user' 
                    ? 'bg-gradient-to-br from-blue-500 to-cyan-500' 
                    : 'bg-gradient-to-br from-purple-500 to-pink-500'
                }`}>
                  {message.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>

                {/* Message Content */}
                <div className={`flex-1 max-w-[80%] ${message.role === 'user' ? 'text-right' : ''}`}>
                  <div
                    className={`inline-block px-4 py-2 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white rounded-br-md'
                        : 'bg-slate-800 text-slate-100 rounded-bl-md border border-slate-700'
                    }`}
                  >
                    {message.status === 'pending' ? (
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Thinking...</span>
                      </div>
                    ) : (
                      <div className="whitespace-pre-wrap text-sm">
                        {message.content.split('\n').map((line, i) => {
                          // Simple markdown-like formatting
                          if (line.startsWith('**') && line.endsWith('**')) {
                            return <strong key={i}>{line.slice(2, -2)}</strong>;
                          }
                          if (line.startsWith('_') && line.endsWith('_')) {
                            return <em key={i} className="text-amber-300">{line.slice(1, -1)}</em>;
                          }
                          return <span key={i}>{line}<br /></span>;
                        })}
                      </div>
                    )}
                  </div>
                  
                  {/* Status indicator */}
                  {message.status && message.status !== 'pending' && (
                    <div className={`flex items-center gap-1 mt-1 text-xs ${
                      message.role === 'user' ? 'justify-end' : ''
                    }`}>
                      {getStatusIcon(message.status)}
                      <span className="text-slate-400">
                        {message.status === 'awaiting_confirmation' && 'Needs approval'}
                        {message.status === 'completed' && 'Completed'}
                        {message.status === 'failed' && 'Failed'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-slate-700/50">
            <div className="flex items-end gap-2">
              {/* Voice Button */}
              <Button
                variant={isListening ? 'primary' : 'secondary'}
                size="sm"
                onClick={toggleListening}
                className={`flex-shrink-0 ${
                  isListening 
                    ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                    : 'bg-purple-600 hover:bg-purple-700'
                }`}
                title={isListening ? 'Stop listening' : 'Start voice input'}
              >
                {isListening ? (
                  <MicOff className="w-5 h-5" />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </Button>

              {/* Text Input */}
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isListening ? 'Listening...' : 'Type a command or click the mic...'}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                  rows={1}
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                  disabled={createTask.isPending}
                />
                {isListening && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <div className="flex items-center gap-1">
                      <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                      <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse delay-75" />
                      <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse delay-150" />
                    </div>
                  </div>
                )}
              </div>

              {/* Send Button */}
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleSubmit()}
                disabled={!inputText.trim() || createTask.isPending}
                className="flex-shrink-0 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              >
                {createTask.isPending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </Button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
};

