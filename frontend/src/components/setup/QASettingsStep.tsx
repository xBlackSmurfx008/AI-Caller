import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';

interface QASettingsStepProps {
  formData: any;
  onNext: (data: any) => void;
  onBack: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export const QASettingsStep: React.FC<QASettingsStepProps> = ({
  formData,
  onNext,
  onBack,
  isFirstStep,
}) => {
  const [qaSettings, setQaSettings] = useState({
    enabled: formData.qaSettings?.enabled ?? true,
    sentimentAnalysis: formData.qaSettings?.sentimentAnalysis ?? true,
    complianceCheck: formData.qaSettings?.complianceCheck ?? true,
    minScoreThreshold: formData.qaSettings?.minScoreThreshold ?? 0.6,
    sentimentAlertThreshold: formData.qaSettings?.sentimentAlertThreshold ?? -0.5,
  });

  const handleNext = () => {
    onNext({ qaSettings });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">QA Settings</h2>
        <p className="text-gray-600">
          Configure quality assurance monitoring and thresholds
        </p>
      </div>

      <Card>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">
                Enable QA Monitoring
              </label>
              <p className="text-sm text-gray-500">
                Automatically monitor and score call quality
              </p>
            </div>
            <input
              type="checkbox"
              checked={qaSettings.enabled}
              onChange={(e) =>
                setQaSettings({ ...qaSettings, enabled: e.target.checked })
              }
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
          </div>

          {qaSettings.enabled && (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Sentiment Analysis
                  </label>
                  <p className="text-sm text-gray-500">
                    Analyze customer sentiment in real-time
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={qaSettings.sentimentAnalysis}
                  onChange={(e) =>
                    setQaSettings({
                      ...qaSettings,
                      sentimentAnalysis: e.target.checked,
                    })
                  }
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Compliance Check
                  </label>
                  <p className="text-sm text-gray-500">
                    Check for compliance violations
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={qaSettings.complianceCheck}
                  onChange={(e) =>
                    setQaSettings({
                      ...qaSettings,
                      complianceCheck: e.target.checked,
                    })
                  }
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Minimum QA Score Threshold: {qaSettings.minScoreThreshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={qaSettings.minScoreThreshold}
                  onChange={(e) =>
                    setQaSettings({
                      ...qaSettings,
                      minScoreThreshold: Number(e.target.value),
                    })
                  }
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sentiment Alert Threshold: {qaSettings.sentimentAlertThreshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="-1"
                  max="0"
                  step="0.1"
                  value={qaSettings.sentimentAlertThreshold}
                  onChange={(e) =>
                    setQaSettings({
                      ...qaSettings,
                      sentimentAlertThreshold: Number(e.target.value),
                    })
                  }
                  className="w-full"
                />
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

