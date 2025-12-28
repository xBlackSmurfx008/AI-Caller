import apiClient from './client';
import type { BusinessConfig } from '../types/config';

export const configAPI = {
  listBusinessConfigs: async (is_active?: boolean): Promise<BusinessConfig[]> => {
    const response = await apiClient.get<{ configs: BusinessConfig[] }>('/config/business', {
      params: { is_active },
    });
    return response.data.configs;
  },

  getBusinessConfig: async (businessId: string): Promise<BusinessConfig> => {
    const response = await apiClient.get<{ config: BusinessConfig }>(`/config/business/${businessId}`);
    return response.data.config;
  },

  createBusinessConfig: async (data: {
    name: string;
    type: string;
    config_data: BusinessConfig['config_data'];
    is_active?: boolean;
  }): Promise<BusinessConfig> => {
    const response = await apiClient.post<{ config: BusinessConfig }>('/config/business', data);
    return response.data.config;
  },

  updateBusinessConfig: async (businessId: string, data: {
    name?: string;
    type?: string;
    config_data?: BusinessConfig['config_data'];
    is_active?: boolean;
  }): Promise<BusinessConfig> => {
    const response = await apiClient.put<{ config: BusinessConfig }>(`/config/business/${businessId}`, data);
    return response.data.config;
  },

  deleteBusinessConfig: async (businessId: string): Promise<void> => {
    await apiClient.delete(`/config/business/${businessId}`);
  },

  testConnection: async (data: {
    openai_api_key: string;
    twilio_account_sid: string;
    twilio_auth_token: string;
    twilio_phone_number?: string;
  }): Promise<{
    openai: { connected: boolean; error: string | null };
    twilio: { connected: boolean; error: string | null };
    success: boolean;
  }> => {
    const response = await apiClient.post<{
      openai: { connected: boolean; error: string | null };
      twilio: { connected: boolean; error: string | null };
      success: boolean;
    }>('/config/test-connection', data);
    return response.data;
  },

  listPersonalities: async (): Promise<Array<{
    name: string;
    display_name: string;
    traits: string[];
    skills: string[];
    voice_config: Record<string, any>;
  }>> => {
    const response = await apiClient.get<{ personalities: Array<{
      name: string;
      display_name: string;
      traits: string[];
      skills: string[];
      voice_config: Record<string, any>;
    }> }>('/config/personalities');
    return response.data.personalities;
  },
};

