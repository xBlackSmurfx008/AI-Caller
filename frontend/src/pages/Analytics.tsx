import React, { useState } from 'react';
import { format, subDays } from 'date-fns';
import { useAnalytics } from '../hooks/useAnalytics';
import { useConfigStore } from '../store/configStore';
import { MetricCard } from '../components/analytics/MetricCard';
import { CallVolumeChart } from '../components/analytics/CallVolumeChart';
import { SentimentChart } from '../components/analytics/SentimentChart';
import { QAScoreChart } from '../components/analytics/QAScoreChart';
import { AgentPerformanceTable } from '../components/analytics/AgentPerformanceTable';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { Select } from '../components/common/Select';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatPercentage, formatScore } from '../utils/format';
import { analyticsAPI } from '../api/analytics';
import toast from 'react-hot-toast';

export const Analytics: React.FC = () => {
  const [dateRange, setDateRange] = useState({
    from: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
    to: format(new Date(), 'yyyy-MM-dd'),
  });
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('');
  const { businessConfigs } = useConfigStore();

  const { overview, callVolume, qa, sentiment, escalations, isLoading, error } = useAnalytics({
    from_date: dateRange.from,
    to_date: dateRange.to,
    business_id: selectedBusinessId || undefined,
  });

  const handleExport = async (format: 'csv' | 'pdf') => {
    try {
      const blob = await analyticsAPI.export({
        format,
        report_type: 'full',
        from_date: dateRange.from,
        to_date: dateRange.to,
        business_id: selectedBusinessId || undefined,
        include_charts: format === 'pdf',
      });

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-report-${dateRange.from}-${dateRange.to}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`Report exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to export report');
    }
  };

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        </div>
        <div className="bg-danger-50 border-2 border-danger-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h3 className="font-semibold text-danger-800 mb-1">Error Loading Analytics</h3>
              <p className="text-sm text-danger-700">Please try again later or contact support if the issue persists.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5 p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-gray-800">Analytics Dashboard</h1>
          <p className="mt-0.5 text-sm text-gray-500">
            Comprehensive insights into your call center performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => handleExport('csv')}>
            Export CSV
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport('pdf')}>
            Export PDF
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="chatkit-surface p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Input
            label="From Date"
            type="date"
            value={dateRange.from}
            onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })}
          />
          <Input
            label="To Date"
            type="date"
            value={dateRange.to}
            onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
          />
          <Select
            label="Business"
            options={[
              { value: '', label: 'All Businesses' },
              ...businessConfigs.map((config) => ({
                value: config.id,
                label: config.name,
              })),
            ]}
            value={selectedBusinessId}
            onChange={(e) => setSelectedBusinessId(e.target.value)}
          />
          <div className="flex items-end">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setDateRange({
                  from: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
                  to: format(new Date(), 'yyyy-MM-dd'),
                });
                setSelectedBusinessId('');
              }}
              className="w-full"
            >
              Reset Filters
            </Button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64 chatkit-surface">
          <div className="text-center">
            <LoadingSpinner size="lg" />
            <p className="mt-4 text-sm text-gray-600">Loading analytics data...</p>
          </div>
        </div>
      ) : (
        <>
          {/* Overview Metrics */}
          {overview && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <MetricCard
                title="Total Calls"
                value={overview.total_calls.toLocaleString()}
                subtitle={`${overview.completed_calls} completed`}
                variant="primary"
                icon="📞"
              />
              <MetricCard
                title="Active Calls"
                value={overview.active_calls}
                subtitle="Currently in progress"
                variant="success"
                icon="🟢"
              />
              <MetricCard
                title="Avg QA Score"
                value={formatScore(overview.average_qa_score)}
                subtitle="Quality assurance"
                variant="info"
                icon="⭐"
              />
              <MetricCard
                title="Escalation Rate"
                value={formatPercentage(overview.escalation_rate / 100)}
                subtitle={`${overview.escalated_calls} escalated`}
                variant="warning"
                icon="⚠️"
              />
            </div>
          )}

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {callVolume.length > 0 && (
              <CallVolumeChart data={callVolume} interval="day" />
            )}
            {sentiment && (
              <SentimentChart data={sentiment.distribution} />
            )}
          </div>

          {/* QA Breakdown */}
          {qa && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <QAScoreChart data={qa.score_distribution} />
              <div className="chatkit-surface p-5">
                <h3 className="text-base font-semibold text-gray-800 mb-4">Score Breakdown</h3>
                <div className="space-y-3">
                  {Object.entries(qa.average_scores).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-700 capitalize">
                        {key.replace('_', ' ')}
                      </span>
                      <div className="flex items-center gap-2.5">
                        <div className="w-28 bg-gray-200 rounded-full h-1.5">
                          <div
                            className="bg-primary-500 h-1.5 rounded-full transition-all duration-500"
                            style={{ width: `${(value as number) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold text-gray-800 w-10 text-right">
                          {formatScore(value as number)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Agent Performance */}
          <AgentPerformanceTable agents={[]} />
        </>
      )}
    </div>
  );
};
