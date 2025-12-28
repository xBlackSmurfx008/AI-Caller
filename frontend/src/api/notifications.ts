import apiClient from './client';
import type { Notification, NotificationResponse } from '../types/notification';

export const notificationsAPI = {
  list: async (params?: {
    unread_only?: boolean;
    type?: string;
    limit?: number;
    offset?: number;
  }): Promise<NotificationResponse> => {
    const response = await apiClient.get<NotificationResponse>('/notifications', { params });
    return response.data;
  },

  getUnreadCount: async (): Promise<number> => {
    const response = await apiClient.get<{ unread_count: number }>('/notifications/unread-count');
    return response.data.unread_count;
  },

  markAsRead: async (notificationId: string): Promise<void> => {
    await apiClient.patch(`/notifications/${notificationId}/read`);
  },

  markAllAsRead: async (): Promise<void> => {
    await apiClient.patch('/notifications/read-all');
  },

  delete: async (notificationId: string): Promise<void> => {
    await apiClient.delete(`/notifications/${notificationId}`);
  },
};

