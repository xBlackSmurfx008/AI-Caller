import { useEffect, useRef } from 'react';
import { websocketService } from '../services/websocket';
import { useCallsStore } from '../store/callsStore';
import { useAuthStore } from '../store/authStore';
import { useQueryClient } from '@tanstack/react-query';
import type { Call, CallInteraction } from '../types/call';
import type { Notification } from '../types/notification';

export const useWebSocket = () => {
  const { token, user } = useAuthStore();
  const queryClient = useQueryClient();
  const {
    addCall,
    updateCall,
    removeCall,
    addInteraction,
  } = useCallsStore();
  const callListenersRef = useRef<Map<string, Set<string>>>(new Map());

  useEffect(() => {
    // Connect WebSocket
    websocketService.connect(token || undefined);

    // Subscribe to all calls
    websocketService.subscribeToAllCalls();

    // Set up event handlers
    const handleCallStarted = (data: { call: Call }) => {
      addCall(data.call);
    };

    const handleCallUpdated = (data: { call: Call }) => {
      updateCall(data.call.id, data.call);
    };

    const handleCallEnded = (data: { call_id: string }) => {
      // Update call status to completed
      updateCall(data.call_id, { status: 'completed' });
    };

    const handleInteractionAdded = (data: { call_id: string; interaction: CallInteraction }) => {
      addInteraction(data.call_id, data.interaction);
    };

    const handleQAScoreUpdated = (data: { call_id: string; qa_score: any }) => {
      updateCall(data.call_id, {
        qa_score: data.qa_score.overall_score,
      });
    };

    const handleSentimentChanged = (data: {
      call_id: string;
      sentiment: { score: number; label: 'positive' | 'neutral' | 'negative' };
    }) => {
      updateCall(data.call_id, {
        sentiment: data.sentiment.label,
      });
    };

    const handleEscalationTriggered = (data: { call_id: string; escalation: any }) => {
      updateCall(data.call_id, {
        status: 'escalated',
        escalation_status: 'pending',
        assigned_agent: data.escalation.agent_name
          ? {
              id: data.escalation.assigned_agent_id || '',
              name: data.escalation.agent_name,
            }
          : undefined,
      });
    };

    const handleEscalationCompleted = (data: { call_id: string; escalation: any }) => {
      updateCall(data.call_id, {
        escalation_status: 'completed',
      });
    };

    const handleNotificationCreated = (data: { notification: Notification }) => {
      // Invalidate notifications query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
    };

    // Register event listeners
    websocketService.subscribe('call.started', handleCallStarted);
    websocketService.subscribe('call.updated', handleCallUpdated);
    websocketService.subscribe('call.ended', handleCallEnded);
    websocketService.subscribe('interaction.added', handleInteractionAdded);
    websocketService.subscribe('qa.score.updated', handleQAScoreUpdated);
    websocketService.subscribe('sentiment.changed', handleSentimentChanged);
    websocketService.subscribe('escalation.triggered', handleEscalationTriggered);
    websocketService.subscribe('escalation.completed', handleEscalationCompleted);
    websocketService.subscribe('notification.created', handleNotificationCreated);

    // Cleanup
    return () => {
      websocketService.unsubscribe('call.started', handleCallStarted);
      websocketService.unsubscribe('call.updated', handleCallUpdated);
      websocketService.unsubscribe('call.ended', handleCallEnded);
      websocketService.unsubscribe('interaction.added', handleInteractionAdded);
      websocketService.unsubscribe('qa.score.updated', handleQAScoreUpdated);
      websocketService.unsubscribe('sentiment.changed', handleSentimentChanged);
      websocketService.unsubscribe('escalation.triggered', handleEscalationTriggered);
      websocketService.unsubscribe('escalation.completed', handleEscalationCompleted);
      websocketService.unsubscribe('notification.created', handleNotificationCreated);
    };
  }, [token, addCall, updateCall, removeCall, addInteraction, queryClient]);

  const subscribeToCall = (callId: string) => {
    if (!callListenersRef.current.has(callId)) {
      websocketService.subscribeToCall(callId);
      callListenersRef.current.set(callId, new Set());
    }
  };

  const unsubscribeFromCall = (callId: string) => {
    if (callListenersRef.current.has(callId)) {
      websocketService.unsubscribeFromCall(callId);
      callListenersRef.current.delete(callId);
    }
  };

  return {
    isConnected: websocketService.isConnected(),
    subscribeToCall,
    unsubscribeFromCall,
  };
};

