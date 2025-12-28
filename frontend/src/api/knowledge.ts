import apiClient from './client';
import type { KnowledgeEntry, CreateKnowledgeEntry } from '../types/knowledge';

export const knowledgeAPI = {
  list: async (params?: {
    business_id?: string;
    page?: number;
    limit?: number;
    search?: string;
  }): Promise<{ entries: KnowledgeEntry[]; pagination: any }> => {
    const response = await apiClient.get<{ entries: KnowledgeEntry[]; pagination: any }>('/knowledge', {
      params,
    });
    return response.data;
  },

  create: async (data: CreateKnowledgeEntry): Promise<KnowledgeEntry> => {
    const response = await apiClient.post<{ entry: KnowledgeEntry }>('/knowledge', data);
    return response.data.entry;
  },

  upload: async (file: File, businessId?: string, title?: string): Promise<KnowledgeEntry> => {
    const formData = new FormData();
    formData.append('file', file);
    if (businessId) formData.append('business_id', businessId);
    if (title) formData.append('title', title);

    const response = await apiClient.post<{ entry: KnowledgeEntry; processing_status: string }>(
      '/knowledge/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.entry;
  },

  delete: async (entryId: number): Promise<void> => {
    await apiClient.delete(`/knowledge/${entryId}`);
  },
};

