export type NotificationType = 'call_escalated' | 'qa_alert' | 'system_update' | 'agent_status' | 'call_ended' | 'compliance_alert';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  metadata?: {
    call_id?: string;
    agent_id?: string;
    score?: number;
    [key: string]: any;
  };
  action_url?: string;
}

export interface NotificationResponse {
  notifications: Notification[];
  unread_count: number;
}

