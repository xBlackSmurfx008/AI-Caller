export type CallStatus = 
  | 'initiated' 
  | 'ringing' 
  | 'in_progress' 
  | 'completed' 
  | 'failed' 
  | 'escalated';

export type CallDirection = 'inbound' | 'outbound';

export type EscalationStatus = 
  | 'pending' 
  | 'in_progress' 
  | 'completed' 
  | 'cancelled';

export type SentimentLabel = 'positive' | 'neutral' | 'negative';

export type Call = {
  id: string;
  twilio_call_sid: string;
  direction: CallDirection;
  status: CallStatus;
  from_number: string;
  to_number: string;
  business_id?: string;
  template_id?: string;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
  // Computed fields
  qa_score?: number;
  sentiment?: SentimentLabel;
  escalation_status?: EscalationStatus;
  assigned_agent?: {
    id: string;
    name: string;
  };
};

export type CallInteraction = {
  id: number;
  call_id: string;
  speaker: 'ai' | 'customer';
  text: string;
  audio_url?: string;
  timestamp: string;
  metadata: Record<string, any>;
  // Computed fields
  sentiment?: {
    score: number;
    label: SentimentLabel;
  };
};

export type QAScore = {
  id: number;
  call_id: string;
  overall_score: number;
  sentiment_score: number;
  compliance_score: number;
  accuracy_score: number;
  professionalism_score: number;
  sentiment_label: SentimentLabel;
  compliance_issues: string[];
  flagged_issues: string[];
  reviewed_by: string;
  review_notes?: string;
  created_at: string;
  updated_at: string;
};

export type Escalation = {
  id: number;
  call_id: string;
  status: EscalationStatus;
  trigger_type: string;
  trigger_details: Record<string, any>;
  assigned_agent_id?: string;
  agent_name?: string;
  conversation_summary?: string;
  context_data: Record<string, any>;
  requested_at: string;
  accepted_at?: string;
  completed_at?: string;
};

export type CallFilters = {
  page?: number;
  limit?: number;
  status?: CallStatus;
  direction?: CallDirection;
  business_id?: string;
  from_date?: string;
  to_date?: string;
  search?: string;
  sort_by?: 'started_at' | 'duration' | 'qa_score';
  sort_order?: 'asc' | 'desc';
  min_qa_score?: number;
  max_qa_score?: number;
  sentiment?: SentimentLabel;
};

export type Pagination = {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
};

export type CallsResponse = {
  calls: Call[];
  pagination: Pagination;
};

