import React, { useEffect, useRef, useState } from 'react';
import type { CallInteraction } from '../../types/call';
import { TranscriptMessage } from './TranscriptMessage';
import { Input } from '../common/Input';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { cn } from '../../utils/helpers';

interface TranscriptProps {
  interactions: CallInteraction[];
  isLoading?: boolean;
}

export const Transcript: React.FC<TranscriptProps> = ({ interactions, isLoading }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [interactions, autoScroll]);

  const filteredInteractions = searchQuery
    ? interactions.filter((interaction) =>
        interaction.text.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : interactions;

  const handleScroll = () => {
    if (transcriptRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = transcriptRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setAutoScroll(isNearBottom);
    }
  };

  return (
    <div className="flex flex-col h-full chatkit-surface">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-800">Live Transcript</h3>
          <span className="chatkit-badge text-xs">
            {interactions.length} messages
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
              <svg className="h-3.5 w-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Search transcript..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="chatkit-input pl-7 pr-2.5 py-1.5 text-xs w-40"
            />
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setAutoScroll(!autoScroll)}
            className="text-xs px-2"
          >
            {autoScroll ? '🔒' : '🔓'}
          </Button>
        </div>
      </div>

      {/* Transcript Content */}
      <div
        ref={transcriptRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 chatkit-scrollbar bg-gray-50"
      >
        {isLoading && interactions.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <LoadingSpinner />
              <p className="text-gray-500 text-xs mt-2">Loading transcript...</p>
            </div>
          </div>
        ) : filteredInteractions.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <div className="text-2xl mb-2">💬</div>
              <p className="text-gray-500 text-xs font-medium mb-1">
                {searchQuery ? 'No matches found' : 'No transcript available'}
              </p>
              {searchQuery && (
                <p className="text-xs text-gray-400">Try a different search term</p>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredInteractions.map((interaction) => (
              <TranscriptMessage key={interaction.id} interaction={interaction} />
            ))}
            <div ref={transcriptEndRef} />
          </div>
        )}
      </div>
    </div>
  );
};
