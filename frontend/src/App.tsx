import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { MainLayout } from './components/layout/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { Setup } from './pages/Setup';
import DocumentationManagement from './pages/DocumentationManagement';
import { TwilioDashboard } from './pages/TwilioDashboard';
import { RingCentralDashboard } from './pages/RingCentralDashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route
              path="/"
              element={
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              }
            />
            <Route
              path="/analytics"
              element={
                <MainLayout>
                  <Analytics />
                </MainLayout>
              }
            />
            <Route
              path="/settings"
              element={
                <MainLayout>
                  <Settings />
                </MainLayout>
              }
            />
            <Route
              path="/documentation"
              element={
                <MainLayout>
                  <DocumentationManagement />
                </MainLayout>
              }
            />
            <Route
              path="/setup"
              element={
                <MainLayout>
                  <Setup />
                </MainLayout>
              }
            />
            <Route
              path="/twilio"
              element={
                <MainLayout>
                  <TwilioDashboard />
                </MainLayout>
              }
            />
            <Route
              path="/ringcentral"
              element={
                <MainLayout>
                  <RingCentralDashboard />
                </MainLayout>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'var(--ai-color-bg-primary)',
                color: 'var(--ai-color-text-primary)',
                border: '0.5px solid var(--ai-color-border-heavy)',
                borderRadius: 'var(--ai-radius-base)',
                boxShadow: 'var(--ai-elevation-2-shadow)',
                padding: 'var(--ai-spacing-6) var(--ai-spacing-8)',
                fontSize: 'var(--ai-font-size-body-small)',
              },
            }}
          />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
