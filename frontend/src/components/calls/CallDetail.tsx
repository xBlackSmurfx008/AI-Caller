import React, { useEffect } from 'react';
import { useCallDetail } from '../../hooks/useCallDetail';
import { useCallsStore } from '../../store/callsStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { CallHeader } from './CallHeader';
import { Transcript } from './Transcript';
import { QAMetrics } from './QAMetrics';
import { CallActions } from './CallActions';
import { CallNotes } from './CallNotes';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Button } from '../common/Button';
import { callsAPI } from '../../api/calls';

interface CallDetailProps {
  callId: string | null;
}

export const CallDetail: React.FC<CallDetailProps> = ({ callId }) => {
  const { call, interactions, isLoading } = useCallDetail(callId);
  const { subscribeToCall, unsubscribeFromCall } = useWebSocket();

  useEffect(() => {
    if (callId) {
      subscribeToCall(callId);
      return () => {
        unsubscribeFromCall(callId);
      };
    }
  }, [callId, subscribeToCall, unsubscribeFromCall]);

  if (!callId) {
    return null; // Empty state is handled in Dashboard
  }

  if (isLoading && !call) {
    return (
      <div 
        style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'var(--ai-color-bg-primary)',
        }}
      >
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!call) {
    return (
      <div 
        style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'var(--ai-color-bg-primary)',
        }}
      >
        <div style={{ textAlign: 'center', color: 'var(--ai-color-text-tertiary)' }}>
          <p style={{ fontSize: 'var(--ai-font-size-body)' }}>Call not found</p>
        </div>
      </div>
    );
  }

  // Fetch QA score
  const [qaScore, setQaScore] = React.useState<any>(null);
  React.useEffect(() => {
    if (callId) {
      callsAPI.getQA(callId).then(setQaScore).catch(() => setQaScore(null));
    }
  }, [callId]);

  return (
    <div 
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--ai-color-bg-primary)',
        overflow: 'hidden',
      }}
    >
      <CallHeader call={call} />
      
      <div 
        style={{
          flex: 1,
          overflow: 'hidden',
          display: 'grid',
          gridTemplateColumns: '2fr 1fr',
          gap: 'var(--ai-spacing-6)',
          padding: 'var(--ai-spacing-8)',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <Transcript interactions={interactions} isLoading={isLoading} />
        </div>
        
        <div 
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ai-spacing-6)',
            minHeight: 0,
          }}
        >
          <div 
            style={{
              flex: 1,
              minHeight: 0,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ai-spacing-6)',
            }}
            className="chatkit-scrollbar"
          >
            <QAMetrics qaScore={qaScore} />
            <CallNotes callId={callId} />
          </div>
        </div>
      </div>

      <CallActions call={call} />
    </div>
  );
};

