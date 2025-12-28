import React from 'react';
import type { CallInteraction } from '../../types/call';
import { formatTime } from '../../utils/format';
import { cn } from '../../utils/helpers';
import { SENTIMENT_EMOJIS } from '../../utils/constants';

interface TranscriptMessageProps {
  interaction: CallInteraction;
}

export const TranscriptMessage: React.FC<TranscriptMessageProps> = ({ interaction }) => {
  const isAI = interaction.speaker === 'ai';
  const sentimentEmoji = interaction.sentiment
    ? SENTIMENT_EMOJIS[interaction.sentiment.label]
    : null;

  return (
    <div
      className={cn(
        'flex gap-2 animate-fade-in',
        isAI ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-3 py-2',
          isAI
            ? 'chatkit-message-assistant'
            : 'chatkit-message-user'
        )}
      >
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="flex items-center gap-1.5">
            <span className={cn(
              'text-xs font-medium',
              isAI ? 'text-gray-600' : 'text-gray-700'
            )}>
              {isAI ? 'AI' : 'Customer'}
            </span>
            {sentimentEmoji && (
              <span className="text-xs" title={`Sentiment: ${interaction.sentiment?.label}`}>
                {sentimentEmoji}
              </span>
            )}
          </div>
          <span className={cn(
            'text-xs font-mono',
            isAI ? 'text-gray-400' : 'text-gray-500'
          )}>
            {formatTime(interaction.timestamp)}
          </span>
        </div>
        <p className={cn(
          'text-xs leading-relaxed whitespace-pre-wrap',
          isAI ? 'text-gray-700' : 'text-gray-800'
        )}>
          {interaction.text}
        </p>
      </div>
    </div>
  );
};
