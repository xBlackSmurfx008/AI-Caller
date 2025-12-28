import { create } from 'zustand';
import { storage } from '../services/storage';

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthStore>((set) => {
  // Auth disabled for development - auto-login mock user
  const mockUser: User = {
    id: 'dev-user',
    email: 'dev@example.com',
    name: 'Developer',
  };
  const mockToken = 'dev-token';

  // Auto-login for development
  if (typeof window !== 'undefined') {
    localStorage.setItem('auth_token', mockToken);
    storage.set('user', mockUser);
  }

  return {
    user: mockUser,
    token: mockToken,
    isAuthenticated: true, // Always authenticated in dev mode

    login: (token, user) => {
      localStorage.setItem('auth_token', token);
      storage.set('user', user);
      set({ token, user, isAuthenticated: true });
    },

    logout: () => {
      // In dev mode, logout just clears but doesn't redirect
      localStorage.removeItem('auth_token');
      storage.remove('user');
      // Auto-login again for dev
      setTimeout(() => {
        localStorage.setItem('auth_token', mockToken);
        storage.set('user', mockUser);
        set({ token: mockToken, user: mockUser, isAuthenticated: true });
      }, 100);
    },

    setUser: (user) => {
      storage.set('user', user);
      set({ user });
    },
  };
});

