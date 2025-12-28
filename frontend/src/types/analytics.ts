export type OverviewMetrics = {
  total_calls: number;
  active_calls: number;
  completed_calls: number;
  failed_calls: number;
  escalated_calls: number;
  average_qa_score: number;
  average_call_duration: number;
  escalation_rate: number;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  qa_score_distribution: {
    excellent: number;
    good: number;
    fair: number;
    poor: number;
  };
};

export type CallVolumeData = {
  period: string;
  total_calls: number;
  inbound_calls: number;
  outbound_calls: number;
  completed_calls: number;
  escalated_calls: number;
};

export type QAScoreDistribution = {
  range: string;
  count: number;
  percentage: number;
};

export type QATrend = {
  period: string;
  average_score: number;
};

export type TopIssue = {
  issue: string;
  count: number;
  percentage: number;
};

export type QAStatistics = {
  average_scores: {
    overall: number;
    sentiment: number;
    compliance: number;
    accuracy: number;
    professionalism: number;
  };
  score_distribution: QAScoreDistribution[];
  trends: QATrend[];
  top_issues: TopIssue[];
};

export type SentimentTrend = {
  period: string;
  positive: number;
  neutral: number;
  negative: number;
  average_score: number;
};

export type SentimentStatistics = {
  distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  average_sentiment_score: number;
  trends: SentimentTrend[];
  correlation: {
    sentiment_vs_qa: number;
    sentiment_vs_escalation: number;
  };
};

export type EscalationByType = {
  trigger_type: string;
  count: number;
  percentage: number;
};

export type EscalationByStatus = {
  pending: number;
  in_progress: number;
  completed: number;
  cancelled: number;
};

export type EscalationTrend = {
  period: string;
  escalation_count: number;
  escalation_rate: number;
};

export type EscalationStatistics = {
  total_escalations: number;
  escalation_rate: number;
  by_trigger_type: EscalationByType[];
  by_status: EscalationByStatus;
  average_resolution_time: number;
  trends: EscalationTrend[];
};

