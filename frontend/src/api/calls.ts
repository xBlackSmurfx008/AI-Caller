import apiClient from './client';
import type { Call, CallFilters, CallsResponse, CallInteraction, QAScore, Escalation } from '../types/call';

export const callsAPI = {
  list: async (filters?: CallFilters): Promise<CallsResponse> => {
    const response = await apiClient.get<CallsResponse>('/calls', { params: filters });
    return response.data;
  },

  get: async (callId: string): Promise<Call> => {
    const response = await apiClient.get<{ call: Call }>(`/calls/${callId}`);
    return response.data.call;
  },

  getInteractions: async (callId: string, limit?: number, offset?: number, speaker?: 'ai' | 'customer'): Promise<{ interactions: CallInteraction[]; total: number }> => {
    const response = await apiClient.get<{ interactions: CallInteraction[]; total: number }>(
      `/calls/${callId}/interactions`,
      { params: { limit, offset, speaker } }
    );
    return response.data;
  },

  getQA: async (callId: string): Promise<QAScore | null> => {
    try {
      const response = await apiClient.get<{ qa_scores?: QAScore }>(`/calls/${callId}`);
      return response.data.qa_scores || null;
    } catch {
      return null;
    }
  },

  initiate: async (data: {
    to_number: string;
    from_number?: string;
    business_id?: string;
    template_id?: string;
    agent_personality?: string;
    metadata?: Record<string, any>;
  }): Promise<Call> => {
    const response = await apiClient.post<{ call: Call }>('/calls/initiate', data);
    return response.data.call;
  },

  escalate: async (callId: string, data: {
    agent_id?: string;
    reason?: string;
    context_note?: string;
  }): Promise<Escalation> => {
    const response = await apiClient.post<{ escalation: Escalation }>(`/calls/${callId}/escalate`, data);
    return response.data.escalation;
  },

  intervene: async (callId: string, data: {
    action: 'send_message' | 'pause' | 'resume' | 'override_instructions';
    message?: string;
    instructions?: string;
  }): Promise<void> => {
    await apiClient.post(`/calls/${callId}/intervene`, data);
  },

  end: async (callId: string, data?: { reason?: string; notes?: string }): Promise<Call> => {
    const response = await apiClient.post<{ call: Call }>(`/calls/${callId}/end`, data);
    return response.data.call;
  },

  addNote: async (callId: string, data: {
    note: string;
    tags?: string[];
    category?: string;
  }): Promise<any> => {
    const response = await apiClient.post<{ note: any }>(`/calls/${callId}/notes`, data);
    return response.data.note;
  },

  getNotes: async (callId: string): Promise<any[]> => {
    const response = await apiClient.get<{ notes: any[] }>(`/calls/${callId}/notes`);
    return response.data.notes;
  },

  updateNote: async (callId: string, noteId: number, data: {
    note?: string;
    tags?: string[];
    category?: string;
  }): Promise<any> => {
    const response = await apiClient.put<{ note: any }>(`/calls/${callId}/notes/${noteId}`, data);
    return response.data.note;
  },

  deleteNote: async (callId: string, noteId: number): Promise<void> => {
    await apiClient.delete(`/calls/${callId}/notes/${noteId}`);
  },
};

