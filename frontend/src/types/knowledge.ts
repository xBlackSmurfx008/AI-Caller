export type KnowledgeEntry = {
  id: number;
  business_id?: string;
  title: string;
  content: string;
  source?: string;
  source_type?: string;
  vector_id?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
};

export type CreateKnowledgeEntry = {
  business_id?: string;
  title: string;
  content: string;
  source?: string;
  source_type?: string;
  metadata?: Record<string, any>;
};

