import apiClient from './client';

export interface SetupCompleteRequest {
  business_config?: {
    name: string;
    type: string;
    config_data: any;
  };
  agents?: Array<{
    name: string;
    email: string;
    phone_number?: string;
    extension?: string;
    skills?: string[];
    departments?: string[];
    is_available?: boolean;
    is_active?: boolean;
    metadata?: any;
  }>;
  knowledge_base?: Array<{
    title: string;
    content: string;
    source?: string;
    source_type?: string;
  }>;
  api_config?: {
    openai_api_key?: string;
    twilio_account_sid?: string;
    twilio_auth_token?: string;
    twilio_phone_number?: string;
  };
}

export interface SetupCompleteResponse {
  success: boolean;
  business_config_id?: string;
  agents_created: number;
  knowledge_entries_created: number;
  message: string;
}

export const setupAPI = {
  complete: async (data: SetupCompleteRequest): Promise<SetupCompleteResponse> => {
    const response = await apiClient.post<SetupCompleteResponse>('/setup/complete', data);
    return response.data;
  },
};

