import React from 'react';
import type { Call } from '../../types/call';
import { formatDateTime, formatCallDuration } from '../../utils/format';
import { Badge } from '../common/Badge';
import { cn } from '../../utils/helpers';

interface CallHeaderProps {
  call: Call;
}

export const CallHeader: React.FC<CallHeaderProps> = ({ call }) => {
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

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-bold text-gray-900">
                Call {call.id.slice(0, 8).toUpperCase()}
              </h2>
              <Badge 
                variant={call.status === 'escalated' ? 'danger' : call.status === 'in_progress' ? 'success' : 'default'} 
                size="sm"
              >
                {call.status.replace('_', ' ')}
              </Badge>
              <Badge variant={call.direction === 'inbound' ? 'info' : 'default'} size="sm">
                {call.direction}
              </Badge>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <div className="flex items-start gap-2">
              <span className="text-gray-500 min-w-[60px]">From:</span>
              <span className="text-gray-800 font-mono">{call.from_number}</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-gray-500 min-w-[60px]">To:</span>
              <span className="text-gray-800 font-mono">{call.to_number}</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-gray-500 min-w-[60px]">Duration:</span>
              <span className="text-gray-800 font-mono">{getDuration()}</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-gray-500 min-w-[60px]">Started:</span>
              <span className="text-gray-800">{formatDateTime(call.started_at)}</span>
            </div>
            {call.ended_at && (
              <div className="flex items-start gap-2">
                <span className="text-gray-500 min-w-[60px]">Ended:</span>
                <span className="text-gray-800">{formatDateTime(call.ended_at)}</span>
              </div>
            )}
            {call.assigned_agent && (
              <div className="flex items-center gap-2">
                <span className="text-gray-500 min-w-[60px]">Agent:</span>
                <div className="flex items-center gap-1.5">
                  <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="text-xs font-medium text-gray-700">
                      {call.assigned_agent.name.charAt(0)}
                    </span>
                  </div>
                  <span className="text-gray-800 text-xs">{call.assigned_agent.name}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
