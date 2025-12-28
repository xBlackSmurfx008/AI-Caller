export type PhoneNumber = {
  id: string;
  phone_number: string;
  twilio_phone_sid?: string;
  friendly_name?: string;
  country_code: string;
  region?: string;
  capabilities: {
    voice?: boolean;
    SMS?: boolean;
    MMS?: boolean;
  };
  status: 'active' | 'pending' | 'released';
  webhook_url?: string;
  webhook_method: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
};

export type PhoneNumberCreate = {
  phone_number: string;
  twilio_phone_sid?: string;
  friendly_name?: string;
  country_code: string;
  region?: string;
  capabilities?: Record<string, any>;
  status?: string;
  webhook_url?: string;
  webhook_method?: string;
  is_active?: boolean;
  metadata?: Record<string, any>;
};

export type PhoneNumberUpdate = {
  friendly_name?: string;
  webhook_url?: string;
  webhook_method?: string;
  is_active?: boolean;
  metadata?: Record<string, any>;
};

export type PhoneNumberSearchRequest = {
  country_code?: string;
  area_code?: string;
  capabilities?: string[];
  limit?: number;
};

export type PhoneNumberPurchaseRequest = {
  phone_number: string;
};

export type PhoneNumberAssignmentRequest = {
  is_primary?: boolean;
};

