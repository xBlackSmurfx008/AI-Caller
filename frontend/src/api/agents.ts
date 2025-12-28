import apiClient from './client';
import type { HumanAgent, CreateAgentData } from '../types/agent';

export const agentsAPI = {
  list: async (is_active?: boolean, is_available?: boolean): Promise<HumanAgent[]> => {
    const response = await apiClient.get<{ agents: HumanAgent[] }>('/agents', {
      params: { is_active, is_available },
    });
    return response.data.agents;
  },

  get: async (agentId: string): Promise<HumanAgent> => {
    const response = await apiClient.get<{ agent: HumanAgent }>(`/agents/${agentId}`);
    return response.data.agent;
  },

  create: async (data: CreateAgentData): Promise<HumanAgent> => {
    const response = await apiClient.post<{ agent: HumanAgent }>('/agents', data);
    return response.data.agent;
  },

  update: async (agentId: string, data: Partial<CreateAgentData>): Promise<HumanAgent> => {
    const response = await apiClient.put<{ agent: HumanAgent }>(`/agents/${agentId}`, data);
    return response.data.agent;
  },

  delete: async (agentId: string): Promise<void> => {
    await apiClient.delete(`/agents/${agentId}`);
  },

  updateAvailability: async (agentId: string, is_available: boolean): Promise<HumanAgent> => {
    const response = await apiClient.patch<{ agent: HumanAgent }>(`/agents/${agentId}/availability`, {
      is_available,
    });
    return response.data.agent;
  },
};

