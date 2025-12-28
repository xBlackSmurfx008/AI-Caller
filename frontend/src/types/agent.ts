export type HumanAgent = {
  id: string;
  name: string;
  email: string;
  phone_number?: string;
  extension?: string;
  is_available: boolean;
  is_active: boolean;
  skills: string[];
  departments: string[];
  total_calls_handled: number;
  average_rating?: number;
  created_at: string;
  updated_at: string;
  last_active_at?: string;
  metadata: Record<string, any>;
};

export type CreateAgentData = {
  name: string;
  email: string;
  phone_number?: string;
  extension?: string;
  skills?: string[];
  departments?: string[];
  is_available?: boolean;
  is_active?: boolean;
  metadata?: Record<string, any>;
};

