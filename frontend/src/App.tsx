import React from 'react';
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { Navbar } from '@/components/layout/Navbar';
import { BottomNav } from '@/components/layout/BottomNav';
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
import { useCalendarStatus, useGodfatherSettings } from '@/lib/hooks';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function OnboardingGuard({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const onboardingCompleted = localStorage.getItem('onboarding_completed') === 'true';
  
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
    <div className="min-h-screen pb-16 md:pb-0">
      <OnboardingGuard>
        <Navbar />
        <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/command-center" element={<CommandCenter />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/daily-plan" element={<DailyPlan />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/contacts" element={<Contacts />} />
        <Route path="/contacts/:id" element={<ContactDetail />} />
        <Route path="/messages" element={<Messages />} />
        <Route path="/messaging" element={<Messaging />} />
        <Route path="/trusted-list" element={<TrustedList />} />
        <Route path="/cost" element={<CostMonitoring />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/audit-log" element={<AuditLog />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/oauth/callback" element={<OAuthCallback />} />
        <Route path="/relationship-ops/runs" element={<RelationshipOpsRunsList />} />
        <Route path="/relationship-ops/runs/:runId" element={<RelationshipOpsRun />} />
        </Routes>
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

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
