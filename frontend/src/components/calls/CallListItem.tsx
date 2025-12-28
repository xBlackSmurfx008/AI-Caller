import React from 'react';
import type { Call } from '../../types/call';
import { formatCallDuration, formatRelativeTime } from '../../utils/format';
import { SENTIMENT_EMOJIS } from '../../utils/constants';
import { cn } from '../../utils/helpers';
import { Badge } from '../common/Badge';

interface CallListItemProps {
  call: Call;
  isSelected: boolean;
  onClick: () => void;
}

export const CallListItem: React.FC<CallListItemProps> = ({
  call,
  isSelected,
  onClick,
}) => {
  const getStatusVariant = (status: Call['status']) => {
    switch (status) {
      case 'in_progress':
        return 'success';
      case 'escalated':
        return 'danger';
      case 'ringing':
        return 'info';
      case 'completed':
        return 'default';
      default:
        return 'default';
    }
  };

  const getSentimentEmoji = () => {
    return call.sentiment ? SENTIMENT_EMOJIS[call.sentiment] : '😐';
  };

  const getDuration = () => {
    if (call.duration_seconds) {
      return formatCallDuration(call.duration_seconds);
    }
    if (call.started_at) {
      const now = new Date();
      const started = new Date(call.started_at);
      const diff = Math.floor((now.getTime() - started.getTime()) / 1000);
      return formatCallDuration(diff);
    }
    return '0s';
  };

  const getQAScoreColor = (score?: number) => {
    if (!score) return 'text-gray-400';
    if (score >= 0.8) return 'text-success-600';
    if (score >= 0.6) return 'text-warning-600';
    return 'text-danger-600';
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        'p-3 border-b border-gray-200 cursor-pointer transition-chatkit',
        'hover:bg-gray-50',
        isSelected && 'bg-primary-50 border-l-2 border-l-primary-500'
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Header Row */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <Badge variant={getStatusVariant(call.status) as any} size="sm">
              {call.status.replace('_', ' ')}
            </Badge>
            {call.direction === 'inbound' && (
              <Badge variant="info" size="sm">Inbound</Badge>
            )}
            {call.escalation_status && (
              <Badge variant="danger" size="sm">Escalated</Badge>
            )}
          </div>

          {/* Phone Numbers */}
          <div className="mb-2">
            <div className="flex items-center gap-2 text-sm">
              <span className="font-medium text-gray-900">{call.from_number}</span>
              <span className="text-gray-400">→</span>
              <span className="text-gray-700">{call.to_number}</span>
            </div>
          </div>

          {/* Metrics Row */}
          <div className="flex items-center gap-4 text-sm text-gray-600 flex-wrap">
            <div className="flex items-center gap-1">
              <span className="text-base">{getSentimentEmoji()}</span>
              <span className="capitalize">{call.sentiment || 'neutral'}</span>
            </div>
            
            {call.qa_score !== undefined && (
              <div className={cn('flex items-center gap-1 font-medium', getQAScoreColor(call.qa_score))}>
                <span>⭐</span>
                <span>{call.qa_score.toFixed(2)}</span>
              </div>
            )}
            
            <div className="flex items-center gap-1">
              <span>⏱️</span>
              <span className="font-mono">{getDuration()}</span>
            </div>
          </div>

          {/* Agent Info */}
          {call.assigned_agent && (
            <div className="mt-2 flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center">
                <span className="text-xs font-medium text-primary-700">
                  {call.assigned_agent.name.charAt(0)}
                </span>
              </div>
              <span className="text-xs text-gray-600">{call.assigned_agent.name}</span>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div className="flex-shrink-0 text-right">
          <div className="text-xs text-gray-500 whitespace-nowrap">
            {formatRelativeTime(call.started_at)}
          </div>
        </div>
      </div>
    </div>
  );
};
