import apiClient from './client';
import type { PhoneNumber, PhoneNumberCreate, PhoneNumberUpdate, PhoneNumberSearchRequest, PhoneNumberPurchaseRequest, PhoneNumberAssignmentRequest } from '../types/phoneNumber';

export const phoneNumbersApi = {
  /**
   * List all phone numbers
   */
  list: async (params?: {
    status?: string;
    is_active?: boolean;
    country_code?: string;
  }): Promise<PhoneNumber[]> => {
    const response = await apiClient.get('/phone-numbers', { params });
    return response.data;
  },

  /**
   * Get phone number details
   */
  get: async (id: string): Promise<PhoneNumber> => {
    const response = await apiClient.get(`/phone-numbers/${id}`);
    return response.data;
  },

  /**
   * Create a phone number (manual entry)
   */
  create: async (data: PhoneNumberCreate): Promise<PhoneNumber> => {
    const response = await apiClient.post('/phone-numbers', data);
    return response.data;
  },

  /**
   * Update phone number configuration
   */
  update: async (id: string, data: PhoneNumberUpdate): Promise<PhoneNumber> => {
    const response = await apiClient.put(`/phone-numbers/${id}`, data);
    return response.data;
  },

  /**
   * Delete/release a phone number
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/phone-numbers/${id}`);
  },

  /**
   * Search for available phone numbers
   */
  searchAvailable: async (params: PhoneNumberSearchRequest): Promise<any[]> => {
    const response = await apiClient.get('/phone-numbers/search/available', { params });
    return response.data;
  },

  /**
   * Purchase a phone number from Twilio
   */
  purchase: async (data: PhoneNumberPurchaseRequest): Promise<PhoneNumber> => {
    const response = await apiClient.post('/phone-numbers/purchase', data);
    return response.data;
  },

  /**
   * Assign phone number to an agent
   */
  assignToAgent: async (
    phoneId: string,
    agentId: string,
    data: PhoneNumberAssignmentRequest
  ): Promise<{ message: string; assignment: { id: number; is_primary: boolean } }> => {
    const response = await apiClient.post(`/phone-numbers/${phoneId}/assign-agent/${agentId}`, data);
    return response.data;
  },

  /**
   * Unassign phone number from an agent
   */
  unassignFromAgent: async (phoneId: string, agentId: string): Promise<void> => {
    await apiClient.delete(`/phone-numbers/${phoneId}/assign-agent/${agentId}`);
  },

  /**
   * Assign phone number to a business
   */
  assignToBusiness: async (
    phoneId: string,
    businessId: string,
    data: PhoneNumberAssignmentRequest
  ): Promise<{ message: string; assignment: { id: number; is_primary: boolean } }> => {
    const response = await apiClient.post(`/phone-numbers/${phoneId}/assign-business/${businessId}`, data);
    return response.data;
  },

  /**
   * Unassign phone number from a business
   */
  unassignFromBusiness: async (phoneId: string, businessId: string): Promise<void> => {
    await apiClient.delete(`/phone-numbers/${phoneId}/assign-business/${businessId}`);
  },

  /**
   * Get all assignments for a phone number
   */
  getAssignments: async (phoneId: string): Promise<{
    phone_id: string;
    phone_number: string;
    agents: Array<{
      assignment_id: number;
      agent_id: string;
      agent_name: string | null;
      is_primary: boolean;
    }>;
    businesses: Array<{
      assignment_id: number;
      business_id: string;
      business_name: string | null;
      is_primary: boolean;
    }>;
  }> => {
    const response = await apiClient.get(`/phone-numbers/${phoneId}/assignments`);
    return response.data;
  },
};

