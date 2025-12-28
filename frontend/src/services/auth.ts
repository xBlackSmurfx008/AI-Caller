import apiClient from '../api/client';
import { useAuthStore } from '../store/authStore';

interface LoginCredentials {
  email: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export const authService = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    try {
      const response = await apiClient.post<{ access_token: string; user: LoginResponse['user'] }>('/auth/login', credentials);
      const { access_token, user } = response.data;
      
      useAuthStore.getState().login(access_token, user);
      return { token: access_token, user };
    } catch (error) {
      throw error;
    }
  },

  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
    }
    useAuthStore.getState().logout();
  },

  forgotPassword: async (email: string): Promise<void> => {
    await apiClient.post('/auth/forgot-password', null, {
      params: { email },
    });
  },

  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/reset-password', null, {
      params: { token, new_password: newPassword },
    });
  },

  getCurrentUser: () => {
    return useAuthStore.getState().user;
  },

  isAuthenticated: () => {
    return useAuthStore.getState().isAuthenticated;
  },
};

