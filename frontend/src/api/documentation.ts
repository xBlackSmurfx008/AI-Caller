import apiClient from './client';

export interface DocumentationSearchRequest {
  query: string;
  vendor?: string;
  doc_type?: string;
  top_k?: number;
  business_id?: string;
}

export interface DocumentationSearchResponse {
  query: string;
  results: DocumentationResult[];
  total_results: number;
  vendors: string[];
}

export interface DocumentationResult {
  id: string;
  title: string;
  content: string;
  url: string;
  vendor: string | null;
  doc_type: string | null;
  score: number;
  metadata: Record<string, any>;
}

export interface Vendor {
  name: string;
  display_name: string;
  base_url: string;
  last_synced: string | null;
  document_count: number;
  doc_types: string[];
}

export interface VendorsResponse {
  vendors: Vendor[];
}

export const documentationApi = {
  getVendors: async (): Promise<VendorsResponse> => {
    const response = await apiClient.get('/documentation/vendors');
    return response.data;
  },

  searchDocumentation: async (
    request: DocumentationSearchRequest
  ): Promise<DocumentationSearchResponse> => {
    const response = await apiClient.post('/documentation/search', request);
    return response.data;
  },

  syncVendor: async (vendor: string): Promise<{ status: string; vendor: string; message: string }> => {
    const response = await apiClient.post(`/documentation/sync/${vendor}`);
    return response.data;
  },

  getDocumentationEntry: async (docId: number): Promise<any> => {
    const response = await apiClient.get(`/documentation/${docId}`);
    return response.data;
  },

  submitFeedback: async (feedback: {
    doc_id: string;
    query: string;
    relevant: boolean;
    comment?: string;
  }): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post('/documentation/feedback', feedback);
    return response.data;
  },
};

