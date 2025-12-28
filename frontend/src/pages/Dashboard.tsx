import React, { useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { CallList } from '../components/calls/CallList';
import { CallDetail } from '../components/calls/CallDetail';
import { InitiateCallModal } from '../components/calls/InitiateCallModal';
import { useCallsStore } from '../store/callsStore';
import { Button } from '../components/common/Button';
import { cn } from '../utils/helpers';

export const Dashboard: React.FC = () => {
  useWebSocket(); // Initialize WebSocket connection
  const { selectedCallId, selectCall } = useCallsStore();
  const [isInitiateCallOpen, setIsInitiateCallOpen] = useState(false);

  return (
    <div 
      style={{
        height: 'calc(100vh - 80px)',
        display: 'flex',
        flexDirection: 'row',
        overflow: 'hidden',
        backgroundColor: 'var(--ai-color-bg-primary)',
      }}
    >
      {/* Call List - Left Panel */}
      <div 
        style={{
          width: '420px',
          flexShrink: 0,
          borderRight: '0.5px solid var(--ai-color-border-heavy)',
          backgroundColor: 'var(--ai-color-bg-primary)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header with Initiate Call Button */}
        <div
          style={{
            padding: 'var(--ai-spacing-8)',
            borderBottom: '0.5px solid var(--ai-color-border-heavy)',
          }}
        >
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsInitiateCallOpen(true)}
            className="w-full"
          >
            + Initiate Call
          </Button>
        </div>
        <div className="flex-1 overflow-hidden chatkit-scrollbar">
          <CallList />
        </div>
      </div>

      {/* Call Detail - Right Panel */}
      <div 
        style={{
          flex: 1,
          minWidth: 0,
          backgroundColor: 'var(--ai-color-bg-primary)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        className="chatkit-scrollbar"
      >
        <CallDetail callId={selectedCallId} />
      </div>


      {/* Empty State */}
      {!selectedCallId && (
        <div 
          className="flex flex-1 items-center justify-center"
          style={{ backgroundColor: 'var(--ai-color-bg-primary)' }}
        >
          <div className="text-center animate-fade-in" style={{ maxWidth: '28rem', padding: '0 var(--ai-spacing-12)' }}>
            <div 
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '64px',
                height: '64px',
                backgroundColor: 'var(--ai-color-bg-tertiary)',
                borderRadius: 'var(--ai-radius-full)',
                marginBottom: 'var(--ai-spacing-8)',
              }}
            >
              <svg style={{ width: '32px', height: '32px', color: 'var(--ai-color-icon-tertiary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <h3 style={{
              fontSize: 'var(--ai-font-size-h3)',
              fontWeight: 'var(--ai-font-weight-semibold)',
              lineHeight: 'var(--ai-line-height-h3)',
              letterSpacing: 'var(--ai-letter-spacing-h3)',
              color: 'var(--ai-color-text-primary)',
              marginBottom: 'var(--ai-spacing-4)',
            }}>
              Select a call to view details
            </h3>
            <p style={{
              fontSize: 'var(--ai-font-size-body-small)',
              lineHeight: 'var(--ai-line-height-body-small)',
              color: 'var(--ai-color-text-tertiary)',
            }}>
              Choose a call from the list to see the transcript, QA metrics, and take actions
            </p>
          </div>
        </div>
      )}

      {/* Initiate Call Modal */}
      <InitiateCallModal
        isOpen={isInitiateCallOpen}
        onClose={() => setIsInitiateCallOpen(false)}
        onSuccess={() => {
          // Refresh calls list
          window.location.reload();
        }}
      />
    </div>
  );
};
