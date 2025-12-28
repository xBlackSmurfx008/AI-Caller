import React from 'react';
import { useAuthStore } from '../../store/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  // Auth disabled for development - auto-login mock user
  const { isAuthenticated, login } = useAuthStore();
  
  React.useEffect(() => {
    if (!isAuthenticated) {
      // Auto-login with mock user for development
      login('dev-token', {
        id: 'dev-user',
        email: 'dev@example.com',
        name: 'Developer',
      });
    }
  }, [isAuthenticated, login]);

  return <>{children}</>;
};

