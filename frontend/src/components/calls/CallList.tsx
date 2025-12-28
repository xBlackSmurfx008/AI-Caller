import React, { useState, useMemo } from 'react';
import { useCalls } from '../../hooks/useCalls';
import { useCallsStore } from '../../store/callsStore';
import { CallListItem } from './CallListItem';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { LoadingSpinner } from '../common/LoadingSpinner';
import type { CallStatus, SentimentLabel } from '../../types/call';
import { cn } from '../../utils/helpers';

export const CallList: React.FC = () => {
  const { calls, activeCalls, selectedCallId, filters, setFilters, selectCall } = useCallsStore();
  const [searchQuery, setSearchQuery] = useState('');
  const { isLoading } = useCalls(filters);

  const filteredCalls = useMemo(() => {
    let filtered = activeCalls;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (call) =>
          call.from_number.toLowerCase().includes(query) ||
          call.to_number.toLowerCase().includes(query) ||
          call.id.toLowerCase().includes(query)
      );
    }

    if (filters.status) {
      filtered = filtered.filter((call) => call.status === filters.status);
    }

    if (filters.sentiment) {
      filtered = filtered.filter((call) => call.sentiment === filters.sentiment);
    }

    return filtered;
  }, [activeCalls, searchQuery, filters]);

  const handleStatusFilter = (status: string) => {
    setFilters({ ...filters, status: status as CallStatus | undefined });
  };

  const handleSentimentFilter = (sentiment: string) => {
    setFilters({ ...filters, sentiment: sentiment as SentimentLabel | undefined });
  };

  return (
    <div className="h-full flex flex-col chatkit-scrollbar" style={{ backgroundColor: 'var(--ai-color-bg-primary)' }}>
      {/* Header */}
      <div 
        style={{
          padding: 'var(--ai-spacing-8)',
          borderBottom: '0.5px solid var(--ai-color-border-heavy)',
          backgroundColor: 'var(--ai-color-bg-primary)',
          position: 'sticky',
          top: 0,
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--ai-spacing-6)' }}>
          <h2 style={{
            fontSize: 'var(--ai-font-size-body-emph)',
            fontWeight: 'var(--ai-font-weight-body-emph)',
            lineHeight: 'var(--ai-line-height-body-emph)',
            letterSpacing: 'var(--ai-letter-spacing-body-emph)',
            color: 'var(--ai-color-text-primary)',
            margin: 0,
          }}>
            Active Calls
          </h2>
          <div style={{
            fontSize: 'var(--ai-font-size-caption)',
            color: 'var(--ai-color-text-tertiary)',
          }}>
            {filteredCalls.length} {filteredCalls.length === 1 ? 'call' : 'calls'}
          </div>
        </div>
        
        {/* Search */}
        <div style={{ marginBottom: 'var(--ai-spacing-6)' }}>
          <div style={{ position: 'relative' }}>
            <div style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: 0,
              paddingLeft: 'var(--ai-spacing-6)',
              display: 'flex',
              alignItems: 'center',
              pointerEvents: 'none',
            }}>
              <svg style={{ width: '16px', height: '16px', color: 'var(--ai-color-icon-tertiary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Search calls..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="chatkit-input"
              style={{
                width: '100%',
                paddingLeft: 'var(--ai-spacing-16)',
                paddingRight: 'var(--ai-spacing-6)',
                paddingTop: 'var(--ai-spacing-4)',
                paddingBottom: 'var(--ai-spacing-4)',
              }}
            />
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-2 gap-2">
          <Select
            options={[
              { value: '', label: 'All Status' },
              { value: 'in_progress', label: 'In Progress' },
              { value: 'ringing', label: 'Ringing' },
              { value: 'escalated', label: 'Escalated' },
            ]}
            value={filters.status || ''}
            onChange={(e) => handleStatusFilter(e.target.value)}
            className="text-sm"
          />

          <Select
            options={[
              { value: '', label: 'All Sentiment' },
              { value: 'positive', label: '😊 Positive' },
              { value: 'neutral', label: '😐 Neutral' },
              { value: 'negative', label: '😞 Negative' },
            ]}
            value={filters.sentiment || ''}
            onChange={(e) => handleSentimentFilter(e.target.value)}
            className="text-sm"
          />
        </div>
      </div>

      {/* Call List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {isLoading && filteredCalls.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <LoadingSpinner />
          </div>
        ) : filteredCalls.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-gray-300 text-3xl mb-3">📞</div>
            <p className="text-sm font-medium text-gray-600 mb-1">No active calls</p>
            <p className="text-xs text-gray-500">
              {searchQuery ? 'Try adjusting your search or filters' : 'Calls will appear here when they start'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredCalls.map((call) => (
              <CallListItem
                key={call.id}
                call={call}
                isSelected={call.id === selectedCallId}
                onClick={() => selectCall(call.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
