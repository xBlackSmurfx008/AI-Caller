import React from 'react';
import type { QAScore } from '../../types/call';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { formatScore } from '../../utils/format';
import { SENTIMENT_EMOJIS } from '../../utils/constants';
import { cn } from '../../utils/helpers';

interface QAMetricsProps {
  qaScore?: QAScore | null;
}

export const QAMetrics: React.FC<QAMetricsProps> = ({ qaScore }) => {
  if (!qaScore) {
    return (
      <Card>
        <div className="text-center py-8">
          <div className="text-3xl mb-3">📊</div>
          <h3 className="text-sm font-semibold text-gray-800 mb-1">QA Metrics</h3>
          <p className="text-xs text-gray-500">
            Quality assurance metrics will appear here once the call is analyzed
          </p>
        </div>
      </Card>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'info';
    if (score >= 0.4) return 'warning';
    return 'danger';
  };

  const getScoreGradient = (score: number) => {
    if (score >= 0.8) return 'from-success-500 to-success-600';
    if (score >= 0.6) return 'from-primary-500 to-primary-600';
    if (score >= 0.4) return 'from-warning-500 to-warning-600';
    return 'from-danger-500 to-danger-600';
  };

  const sentimentEmoji = SENTIMENT_EMOJIS[qaScore.sentiment_label];

  return (
    <Card title="Quality Assurance Metrics">
      <div className="space-y-4">
        {/* Overall Score - Large Display */}
        <div className="text-center p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-xs font-medium text-gray-600 mb-1.5">Overall Score</div>
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className={cn(
              'text-3xl font-bold',
              getScoreColor(qaScore.overall_score) === 'success' ? 'text-green-600' :
              getScoreColor(qaScore.overall_score) === 'info' ? 'text-primary-600' :
              getScoreColor(qaScore.overall_score) === 'warning' ? 'text-yellow-600' : 'text-red-600'
            )}>
              {formatScore(qaScore.overall_score)}
            </div>
            <Badge variant={getScoreColor(qaScore.overall_score) as any} size="sm">
              {getScoreColor(qaScore.overall_score) === 'success' ? 'Excellent' :
               getScoreColor(qaScore.overall_score) === 'info' ? 'Good' :
               getScoreColor(qaScore.overall_score) === 'warning' ? 'Fair' : 'Poor'}
            </Badge>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all duration-500',
                getScoreColor(qaScore.overall_score) === 'success' ? 'bg-green-500' :
                getScoreColor(qaScore.overall_score) === 'info' ? 'bg-primary-500' :
                getScoreColor(qaScore.overall_score) === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              )}
              style={{ width: `${qaScore.overall_score * 100}%` }}
            />
          </div>
        </div>

        {/* Score Breakdown Grid */}
        <div className="grid grid-cols-2 gap-2.5">
          <div className="p-3 bg-gray-50 rounded-md border border-gray-200">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-medium text-gray-700">Sentiment</span>
              <div className="flex items-center gap-1">
                <span className="text-sm">{sentimentEmoji}</span>
                <span className="text-xs text-gray-500 capitalize">{qaScore.sentiment_label}</span>
              </div>
            </div>
            <div className="text-xl font-bold text-gray-800">{formatScore(qaScore.sentiment_score)}</div>
            <div className="mt-1.5 w-full bg-gray-200 rounded-full h-1">
              <div
                className="bg-primary-500 h-1 rounded-full transition-all duration-500"
                style={{ width: `${(qaScore.sentiment_score + 1) * 50}%` }}
              />
            </div>
          </div>

          <div className="p-3 bg-gray-50 rounded-md border border-gray-200">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-medium text-gray-700">Compliance</span>
              <Badge variant={getScoreColor(qaScore.compliance_score) as any} size="sm">
                {formatScore(qaScore.compliance_score)}
              </Badge>
            </div>
            <div className="text-xl font-bold text-gray-800">{formatScore(qaScore.compliance_score)}</div>
            {qaScore.compliance_issues.length > 0 && (
              <div className="mt-1.5 text-xs text-red-600 font-medium">
                {qaScore.compliance_issues.length} issue(s)
              </div>
            )}
            <div className="mt-1.5 w-full bg-gray-200 rounded-full h-1">
              <div
                className={cn(
                  'h-1 rounded-full transition-all duration-500',
                  getScoreColor(qaScore.compliance_score) === 'success' ? 'bg-green-500' :
                  getScoreColor(qaScore.compliance_score) === 'info' ? 'bg-primary-500' :
                  getScoreColor(qaScore.compliance_score) === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                )}
                style={{ width: `${qaScore.compliance_score * 100}%` }}
              />
            </div>
          </div>

          <div className="p-3 bg-gray-50 rounded-md border border-gray-200">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-medium text-gray-700">Accuracy</span>
              <Badge variant={getScoreColor(qaScore.accuracy_score) as any} size="sm">
                {formatScore(qaScore.accuracy_score)}
              </Badge>
            </div>
            <div className="text-xl font-bold text-gray-800">{formatScore(qaScore.accuracy_score)}</div>
            <div className="mt-1.5 w-full bg-gray-200 rounded-full h-1">
              <div
                className={cn(
                  'h-1 rounded-full transition-all duration-500',
                  getScoreColor(qaScore.accuracy_score) === 'success' ? 'bg-green-500' :
                  getScoreColor(qaScore.accuracy_score) === 'info' ? 'bg-primary-500' :
                  getScoreColor(qaScore.accuracy_score) === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                )}
                style={{ width: `${qaScore.accuracy_score * 100}%` }}
              />
            </div>
          </div>

          <div className="p-3 bg-gray-50 rounded-md border border-gray-200">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-medium text-gray-700">Professionalism</span>
              <Badge variant={getScoreColor(qaScore.professionalism_score) as any} size="sm">
                {formatScore(qaScore.professionalism_score)}
              </Badge>
            </div>
            <div className="text-xl font-bold text-gray-800">{formatScore(qaScore.professionalism_score)}</div>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
              <div
                className={cn(
                  'h-1.5 rounded-full transition-all duration-500',
                  `bg-gradient-to-r ${getScoreGradient(qaScore.professionalism_score)}`
                )}
                style={{ width: `${qaScore.professionalism_score * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Issues Section */}
        {qaScore.flagged_issues.length > 0 && (
          <div className="p-4 bg-warning-50 border-2 border-warning-200 rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">⚠️</span>
              <div className="text-sm font-semibold text-warning-800">Flagged Issues</div>
            </div>
            <ul className="space-y-2">
              {qaScore.flagged_issues.map((issue, index) => (
                <li key={index} className="text-sm text-warning-700 flex items-start gap-2">
                  <span className="text-warning-600 mt-0.5">•</span>
                  <span className="capitalize">{issue.replace('_', ' ')}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {qaScore.compliance_issues.length > 0 && (
          <div className="p-4 bg-danger-50 border-2 border-danger-200 rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">❌</span>
              <div className="text-sm font-semibold text-danger-800">Compliance Issues</div>
            </div>
            <ul className="space-y-2">
              {qaScore.compliance_issues.map((issue, index) => (
                <li key={index} className="text-sm text-danger-700 flex items-start gap-2">
                  <span className="text-danger-600 mt-0.5">•</span>
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Card>
  );
};
