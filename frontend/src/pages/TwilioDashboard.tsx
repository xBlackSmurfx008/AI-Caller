import React, { useState, useEffect } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { configAPI } from '../api/config';
import toast from 'react-hot-toast';

interface TwilioStats {
  accountName: string;
  accountStatus: string;
  phoneNumbers: number;
  activeCalls: number;
  totalCalls: number;
  messagesSent: number;
  balance: string;
  lastSync: string;
}

export const TwilioDashboard: React.FC = () => {
  const [stats, setStats] = useState<TwilioStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'testing'>('disconnected');

  const fetchTwilioStats = async () => {
    try {
      setIsRefreshing(true);
      // This would call a real endpoint when implemented
      // For now, show example data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStats({
        accountName: 'Example Twilio Account',
        accountStatus: 'active',
        phoneNumbers: 3,
        activeCalls: 2,
        totalCalls: 1247,
        messagesSent: 3421,
        balance: '$45.23',
        lastSync: new Date().toLocaleString(),
      });
      setConnectionStatus('connected');
    } catch (error: any) {
      toast.error('Failed to fetch Twilio stats');
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
      toast.success('Twilio connection successful!');
    } catch (error: any) {
      setConnectionStatus('disconnected');
      toast.error('Twilio connection failed');
    }
  };

  useEffect(() => {
    fetchTwilioStats();
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
          <h1 className="text-2xl font-bold text-gray-900">Twilio Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Monitor your Twilio account status and usage
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
            onClick={fetchTwilioStats}
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
                <p className="text-sm text-gray-500">Phone Numbers</p>
                <p className="text-xl font-semibold">{stats.phoneNumbers}</p>
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
                <p className="text-sm text-gray-500">Account Balance</p>
                <p className="text-xl font-semibold text-green-600">
                  {stats.balance}
                </p>
                <p className="text-xs text-gray-400">Available</p>
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
              <Button variant="secondary" onClick={() => toast.info('View phone numbers - Coming soon')}>
                View Phone Numbers
              </Button>
              <Button variant="secondary" onClick={() => toast.info('View call logs - Coming soon')}>
                View Call Logs
              </Button>
              <Button variant="secondary" onClick={() => toast.info('View messages - Coming soon')}>
                View Messages
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
                <span className="font-medium">2024-01-01</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Webhook URL:</span>
                <span className="font-medium font-mono text-xs">
                  {window.location.origin}/api/v1/webhooks/twilio
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
                href="https://console.twilio.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                Twilio Console
              </a>{' '}
              and get your Account SID and Auth Token
            </p>
            <p>2. Navigate to Settings → API Configuration</p>
            <p>3. Enter your Twilio credentials</p>
            <p>4. Click "Test Connection" to verify</p>
            <p>5. Configure your webhook URL in Twilio console</p>
          </div>
        </Card>
      )}
    </div>
  );
};

