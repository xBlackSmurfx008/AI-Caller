import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

interface EscalationRulesStepProps {
  formData: any;
  onNext: (data: any) => void;
  onBack: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export const EscalationRulesStep: React.FC<EscalationRulesStepProps> = ({
  formData,
  onNext,
  onBack,
  isFirstStep,
}) => {
  const [escalationRules, setEscalationRules] = useState({
    enabled: formData.escalationRules?.enabled ?? true,
    warmTransfer: formData.escalationRules?.warmTransfer ?? true,
    sentimentThreshold: formData.escalationRules?.sentimentThreshold ?? -0.5,
    keywords: formData.escalationRules?.keywords || ['manager', 'supervisor', 'human'],
    complexityThreshold: formData.escalationRules?.complexityThreshold ?? 0.8,
  });

  const [newKeyword, setNewKeyword] = useState('');

  const handleAddKeyword = () => {
    if (newKeyword && !escalationRules.keywords.includes(newKeyword)) {
      setEscalationRules({
        ...escalationRules,
        keywords: [...escalationRules.keywords, newKeyword],
      });
      setNewKeyword('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    setEscalationRules({
      ...escalationRules,
      keywords: escalationRules.keywords.filter((k) => k !== keyword),
    });
  };

  const handleNext = () => {
    onNext({ escalationRules });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Escalation Rules</h2>
        <p className="text-gray-600">
          Configure when calls should be escalated to human agents
        </p>
      </div>

      <Card>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">
                Enable Escalation
              </label>
              <p className="text-sm text-gray-500">
                Allow calls to be escalated to human agents
              </p>
            </div>
            <input
              type="checkbox"
              checked={escalationRules.enabled}
              onChange={(e) =>
                setEscalationRules({ ...escalationRules, enabled: e.target.checked })
              }
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
          </div>

          {escalationRules.enabled && (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Warm Transfer
                  </label>
                  <p className="text-sm text-gray-500">
                    Transfer call context to agent before connecting
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={escalationRules.warmTransfer}
                  onChange={(e) =>
                    setEscalationRules({
                      ...escalationRules,
                      warmTransfer: e.target.checked,
                    })
                  }
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sentiment Threshold: {escalationRules.sentimentThreshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="-1"
                  max="0"
                  step="0.1"
                  value={escalationRules.sentimentThreshold}
                  onChange={(e) =>
                    setEscalationRules({
                      ...escalationRules,
                      sentimentThreshold: Number(e.target.value),
                    })
                  }
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Escalate when sentiment drops below this threshold
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Escalation Keywords
                </label>
                <div className="flex space-x-2 mb-2">
                  <Input
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    placeholder="Enter keyword..."
                    className="flex-1"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddKeyword();
                      }
                    }}
                  />
                  <Button variant="primary" onClick={handleAddKeyword}>
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {escalationRules.keywords.map((keyword) => (
                    <Badge key={keyword} variant="info" size="sm">
                      {keyword}
                      <button
                        onClick={() => handleRemoveKeyword(keyword)}
                        className="ml-1 hover:text-red-600"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Complexity Threshold: {escalationRules.complexityThreshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={escalationRules.complexityThreshold}
                  onChange={(e) =>
                    setEscalationRules({
                      ...escalationRules,
                      complexityThreshold: Number(e.target.value),
                    })
                  }
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Escalate when query complexity exceeds this threshold
                </p>
              </div>
            </>
          )}
        </div>
      </Card>

      <div className="flex justify-between pt-4">
        <div>
          {!isFirstStep && (
            <Button type="button" variant="ghost" onClick={onBack}>
              Back
            </Button>
          )}
        </div>
        <Button variant="primary" onClick={handleNext}>
          Next
        </Button>
      </div>
    </div>
  );
};

