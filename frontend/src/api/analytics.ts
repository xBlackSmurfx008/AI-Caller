import apiClient from './client';
import type {
  OverviewMetrics,
  CallVolumeData,
  QAStatistics,
  SentimentStatistics,
  EscalationStatistics,
} from '../types/analytics';

export const analyticsAPI = {
  getOverview: async (params?: {
    from_date?: string;
    to_date?: string;
    business_id?: string;
  }): Promise<OverviewMetrics> => {
    const response = await apiClient.get<OverviewMetrics>('/analytics/overview', { params });
    return response.data;
  },

  getCallVolume: async (params: {
    from_date: string;
    to_date: string;
    interval?: 'hour' | 'day' | 'week' | 'month';
    business_id?: string;
    direction?: 'inbound' | 'outbound';
  }): Promise<{ data: CallVolumeData[] }> => {
    const response = await apiClient.get<{ data: CallVolumeData[] }>('/analytics/call-volume', { params });
    return response.data;
  },

  getQA: async (params?: {
    from_date?: string;
    to_date?: string;
    business_id?: string;
  }): Promise<QAStatistics> => {
    const response = await apiClient.get<QAStatistics>('/analytics/qa', { params });
    return response.data;
  },

  getSentiment: async (params?: {
    from_date?: string;
    to_date?: string;
    business_id?: string;
  }): Promise<SentimentStatistics> => {
    const response = await apiClient.get<SentimentStatistics>('/analytics/sentiment', { params });
    return response.data;
  },

  getEscalations: async (params?: {
    from_date?: string;
    to_date?: string;
    business_id?: string;
  }): Promise<EscalationStatistics> => {
    const response = await apiClient.get<EscalationStatistics>('/analytics/escalations', { params });
    return response.data;
  },

  export: async (data: {
    format: 'csv' | 'pdf';
    report_type: 'overview' | 'calls' | 'qa' | 'sentiment' | 'escalations' | 'full';
    from_date?: string;
    to_date?: string;
    business_id?: string;
    include_charts?: boolean;
  }): Promise<Blob> => {
    const response = await apiClient.post('/analytics/export', data, {
      responseType: 'blob',
    });
    return response.data;
  },
};

