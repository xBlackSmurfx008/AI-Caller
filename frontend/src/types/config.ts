export type AIConfig = {
  model: string;
  temperature: number;
  system_prompt: string;
};

export type VoiceConfig = {
  language: string;
  voice: string;
  response_delay: number;
};

export type KnowledgeBaseConfig = {
  enabled: boolean;
  retrieval_top_k: number;
  similarity_threshold: number;
};

export type QAConfig = {
  enabled: boolean;
  sentiment_analysis: boolean;
  compliance_check: boolean;
  min_score_threshold: number;
};

export type EscalationTrigger = {
  type: 'sentiment' | 'keyword' | 'complexity';
  threshold?: number;
  keywords?: string[];
};

export type EscalationConfig = {
  enabled: boolean;
  triggers: EscalationTrigger[];
  warm_transfer: boolean;
};

export type BusinessConfigData = {
  ai: AIConfig;
  voice: VoiceConfig;
  knowledge_base: KnowledgeBaseConfig;
  quality_assurance: QAConfig;
  escalation: EscalationConfig;
};

export type BusinessConfig = {
  id: string;
  name: string;
  type: string;
  config_data: BusinessConfigData;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

