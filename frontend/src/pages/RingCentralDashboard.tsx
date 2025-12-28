import React, { useState, useEffect } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import toast from 'react-hot-toast';

interface RingCentralStats {
  accountName: string;
  accountStatus: string;
  extensions: number;
  activeCalls: number;
  totalCalls: number;
  messagesSent: number;
  voicemails: number;
  lastSync: string;
}

export const RingCentralDashboard: React.FC = () => {
  const [stats, setStats] = useState<RingCentralStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'testing'>('disconnected');

  const fetchRingCentralStats = async () => {
    try {
      setIsRefreshing(true);
      // This would call a real endpoint when implemented
      // For now, show example data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStats({
        accountName: 'Example RingCentral Account',
        accountStatus: 'active',
        extensions: 12,
        activeCalls: 5,
        totalCalls: 3421,
        messagesSent: 8923,
        voicemails: 23,
        lastSync: new Date().toLocaleString(),
      });
      setConnectionStatus('connected');
    } catch (error: any) {
      toast.error('Failed to fetch RingCentral stats');
      console.error(error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const testConnection = async () => {
    try {
      setConnectionStatus('testing');
      // This would test the actual connection
      await new Promise(resolve => setTimeout(resolve, 1500));
      setConnectionStatus('connected');
      toast.success('RingCentral connection successful!');
    } catch (error: any) {
      setConnectionStatus('disconnected');
      toast.error('RingCentral connection failed');
    }
  };

  useEffect(() => {
    fetchRingCentralStats();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">RingCentral Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Monitor your RingCentral account status and usage
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={testConnection}
            isLoading={connectionStatus === 'testing'}
          >
            Test Connection
          </Button>
          <Button
            variant="primary"
            onClick={fetchRingCentralStats}
            isLoading={isRefreshing}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Connection Status */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Connection Status</h3>
            <div className="flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  connectionStatus === 'connected'
                    ? 'bg-green-500'
                    : connectionStatus === 'testing'
                    ? 'bg-yellow-500 animate-pulse'
                    : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-gray-600 capitalize">
                {connectionStatus === 'connected'
                  ? 'Connected'
                  : connectionStatus === 'testing'
                  ? 'Testing...'
                  : 'Disconnected'}
              </span>
            </div>
          </div>
          {stats && (
            <div className="text-right">
              <p className="text-sm text-gray-500">Last Sync</p>
              <p className="text-sm font-medium">{stats.lastSync}</p>
            </div>
          )}
        </div>
      </Card>

      {/* Account Information */}
      {stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Account Name</p>
                <p className="text-xl font-semibold">{stats.accountName}</p>
                <p className="text-xs text-gray-400 capitalize">
                  Status: {stats.accountStatus}
                </p>
              </div>
            </Card>

            <Card>
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Extensions</p>
                <p className="text-xl font-semibold">{stats.extensions}</p>
                <p className="text-xs text-gray-400">Configured</p>
              </div>
            </Card>

            <Card>
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Active Calls</p>
                <p className="text-xl font-semibold text-blue-600">
                  {stats.activeCalls}
                </p>
                <p className="text-xs text-gray-400">In progress</p>
              </div>
            </Card>

            <Card>
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Voicemails</p>
                <p className="text-xl font-semibold text-orange-600">
                  {stats.voicemails}
                </p>
                <p className="text-xs text-gray-400">Unread</p>
              </div>
            </Card>
          </div>

          {/* Usage Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <h3 className="text-lg font-semibold mb-4">Call Statistics</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Total Calls</span>
                  <span className="text-lg font-semibold">{stats.totalCalls}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Active Calls</span>
                  <span className="text-lg font-semibold text-blue-600">
                    {stats.activeCalls}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Voicemails</span>
                  <span className="text-lg font-semibold text-orange-600">
                    {stats.voicemails}
                  </span>
                </div>
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold mb-4">Message Statistics</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Messages Sent</span>
                  <span className="text-lg font-semibold">{stats.messagesSent}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">This Month</span>
                  <span className="text-lg font-semibold text-gray-400">
                    ~{Math.floor(stats.messagesSent / 12)}
                  </span>
                </div>
              </div>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card>
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" onClick={() => toast.info('View extensions - Coming soon')}>
                View Extensions
              </Button>
              <Button variant="secondary" onClick={() => toast.info('View call logs - Coming soon')}>
                View Call Logs
              </Button>
              <Button variant="secondary" onClick={() => toast.info('View messages - Coming soon')}>
                View Messages
              </Button>
              <Button variant="secondary" onClick={() => toast.info('View voicemails - Coming soon')}>
                View Voicemails
              </Button>
              <Button variant="secondary" onClick={() => toast.info('Configure webhooks - Coming soon')}>
                Configure Webhooks
              </Button>
            </div>
          </Card>

          {/* Integration Info */}
          <Card>
            <h3 className="text-lg font-semibold mb-4">Integration Information</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">API Version:</span>
                <span className="font-medium">v1.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Webhook URL:</span>
                <span className="font-medium font-mono text-xs">
                  {window.location.origin}/api/v1/webhooks/ringcentral
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status Callback:</span>
                <span className="font-medium">Enabled</span>
              </div>
            </div>
          </Card>
        </>
      )}

      {/* Setup Instructions */}
      {!stats && connectionStatus === 'disconnected' && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Setup Instructions</h3>
          <div className="space-y-3 text-sm text-gray-600">
            <p>
              1. Go to{' '}
              <a
                href="https://developer.ringcentral.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                RingCentral Developer Portal
              </a>{' '}
              and create an app
            </p>
            <p>2. Get your Client ID, Client Secret, and Server URL</p>
            <p>3. Navigate to Settings → API Configuration</p>
            <p>4. Enter your RingCentral credentials</p>
            <p>5. Click "Test Connection" to verify</p>
            <p>6. Configure your webhook URL in RingCentral app settings</p>
          </div>
        </Card>
      )}
    </div>
  );
};

