import React from 'react';
import { HashRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from '@/lib/AuthContext';
import { Navbar } from '@/components/layout/Navbar';
import { BottomNav } from '@/components/layout/BottomNav';
import { Today } from '@/pages/Today';
import { Dashboard } from '@/pages/Dashboard';
import { CommandCenter } from '@/pages/CommandCenter';
import { Tasks } from '@/pages/Tasks';
import { Calendar } from '@/pages/Calendar';
import { Contacts } from '@/pages/Contacts';
import { ContactDetail } from '@/pages/ContactDetail';
import { Messages } from '@/pages/Messages';
import { Messaging } from '@/pages/Messaging';
import { Settings } from '@/pages/Settings';
import { OAuthCallback } from '@/pages/OAuthCallback';
import { TrustedList } from '@/pages/TrustedList';
import { Projects } from '@/pages/Projects';
import { ProjectDetail } from '@/pages/ProjectDetail';
import { DailyPlan } from '@/pages/DailyPlan';
import { CostMonitoring } from '@/pages/CostMonitoring';
import { Approvals } from '@/pages/Approvals';
import { Onboarding } from '@/pages/Onboarding';
import { AuditLog } from '@/pages/AuditLog';
import { RelationshipOpsRunsList } from '@/pages/RelationshipOpsRunsList';
import { RelationshipOpsRun } from '@/pages/RelationshipOpsRun';
import { Login } from '@/pages/Login';
import { useCalendarStatus, useGodfatherSettings } from '@/lib/hooks';
import { Loader2 } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Auth guard - redirects to login if not authenticated
function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-purple-500 mx-auto mb-4" />
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

function OnboardingGuard({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  // Use prefixed storage key for iOS WKWebView compatibility
  const onboardingCompleted = localStorage.getItem('aiadmin_onboarding_completed') === 'true';
  
  if (!onboardingCompleted && location.pathname !== '/onboarding' && location.pathname !== '/oauth/callback') {
    return <Navigate to="/onboarding" replace />;
  }
  
  return <>{children}</>;
}

function AppContent() {
  // Prefetch essential data
  useCalendarStatus();
  useGodfatherSettings();

  return (
    <div className="min-h-screen pb-16 md:pb-0 flex flex-col overflow-hidden">
      <OnboardingGuard>
        <Navbar />
        <div className="flex-1 overflow-y-auto">
          <Routes>
            {/* Core Routes - Consolidated */}
            <Route path="/" element={<Today />} />
            <Route path="/onboarding" element={<Onboarding />} />
            
            {/* People (Contacts) */}
            <Route path="/contacts" element={<Contacts />} />
            <Route path="/contacts/:id" element={<ContactDetail />} />
            
            {/* Messaging */}
            <Route path="/messaging" element={<Messaging />} />
            <Route path="/messages" element={<Messages />} />
            
            {/* Projects & Tasks */}
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            
            {/* Approvals */}
            <Route path="/approvals" element={<Approvals />} />
            
            {/* Settings Hub - includes admin features */}
            <Route path="/settings" element={<Settings />} />
            <Route path="/settings/calendar" element={<Calendar />} />
            <Route path="/settings/tasks" element={<Tasks />} />
            <Route path="/settings/trusted" element={<TrustedList />} />
            <Route path="/settings/costs" element={<CostMonitoring />} />
            <Route path="/settings/audit" element={<AuditLog />} />
            
            {/* Legacy routes - redirect to new structure */}
            <Route path="/dashboard" element={<Navigate to="/" replace />} />
            <Route path="/command-center" element={<Navigate to="/" replace />} />
            <Route path="/daily-plan" element={<Navigate to="/" replace />} />
            <Route path="/calendar" element={<Navigate to="/settings/calendar" replace />} />
            <Route path="/tasks" element={<Navigate to="/settings/tasks" replace />} />
            <Route path="/trusted-list" element={<Navigate to="/settings/trusted" replace />} />
            <Route path="/cost" element={<Navigate to="/settings/costs" replace />} />
            <Route path="/audit-log" element={<Navigate to="/settings/audit" replace />} />
            
            {/* OAuth & Relationship Ops */}
            <Route path="/oauth/callback" element={<OAuthCallback />} />
            <Route path="/relationship-ops/runs" element={<RelationshipOpsRunsList />} />
            <Route path="/relationship-ops/runs/:runId" element={<RelationshipOpsRun />} />
          </Routes>
        </div>
        <BottomNav />
      </OnboardingGuard>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 4000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/oauth/callback" element={<OAuthCallback />} />
      <Route
        path="/*"
        element={
          <AuthGuard>
            <AppContent />
          </AuthGuard>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <HashRouter>
          <AppRoutes />
        </HashRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
