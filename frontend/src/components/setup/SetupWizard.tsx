import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '../common/Button';
import { APIConfigStep } from './APIConfigStep';
import { BusinessProfileStep } from './BusinessProfileStep';
import { KnowledgeBaseStep } from './KnowledgeBaseStep';
import { AgentsStep } from './AgentsStep';
import { QASettingsStep } from './QASettingsStep';
import { EscalationRulesStep } from './EscalationRulesStep';
import { ReviewStep } from './ReviewStep';

const STEPS = [
  { id: 1, name: 'API Configuration', component: APIConfigStep },
  { id: 2, name: 'Business Profile', component: BusinessProfileStep },
  { id: 3, name: 'Knowledge Base', component: KnowledgeBaseStep },
  { id: 4, name: 'Agents', component: AgentsStep },
  { id: 5, name: 'QA Settings', component: QASettingsStep },
  { id: 6, name: 'Escalation Rules', component: EscalationRulesStep },
  { id: 7, name: 'Review', component: ReviewStep },
];

interface SetupWizardProps {
  onComplete?: () => void;
  onClose?: () => void;
}

export const SetupWizard: React.FC<SetupWizardProps> = ({ onComplete, onClose }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<any>({});

  const handleNext = (stepData: any) => {
    console.log('SetupWizard handleNext called', { currentStep, stepData });
    const updatedData = { ...formData, ...stepData };
    setFormData(updatedData);
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
      console.log('Moving to step', currentStep + 1);
    } else {
      // Last step completed
      console.log('Setup wizard completed');
      if (onComplete) {
        onComplete();
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepClick = (stepId: number) => {
    if (stepId <= currentStep) {
      setCurrentStep(stepId);
    }
  };

  const CurrentStepComponent = STEPS[currentStep - 1].component;

  return (
    <div>
      {/* Progress Indicator */}
      <div style={{ marginBottom: 'var(--ai-spacing-12)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--ai-spacing-4)' }}>
          {STEPS.map((step, index) => (
            <React.Fragment key={step.id}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <button
                  onClick={() => handleStepClick(step.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    fontWeight: 'var(--ai-font-weight-medium)',
                    fontSize: 'var(--ai-font-size-body-small)',
                    border: 'none',
                    cursor: step.id <= currentStep ? 'pointer' : 'default',
                    backgroundColor: step.id < currentStep || step.id === currentStep
                      ? 'var(--ai-color-brand-primary)'
                      : 'var(--ai-color-bg-secondary)',
                    color: step.id < currentStep || step.id === currentStep
                      ? 'var(--ai-color-brand-on-primary)'
                      : 'var(--ai-color-text-secondary)',
                    boxShadow: step.id === currentStep
                      ? '0 0 0 4px rgba(2, 133, 255, 0.2)'
                      : 'none',
                    transition: 'all 0.2s ease',
                  }}
                >
                  {step.id < currentStep ? '✓' : step.id}
                </button>
                <span
                  style={{
                    marginLeft: 'var(--ai-spacing-4)',
                    fontSize: 'var(--ai-font-size-body-small)',
                    fontWeight: 'var(--ai-font-weight-medium)',
                    color: step.id <= currentStep
                      ? 'var(--ai-color-text-primary)'
                      : 'var(--ai-color-text-secondary)',
                  }}
                >
                  {step.name}
                </span>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  style={{
                    flex: 1,
                    height: '2px',
                    margin: '0 var(--ai-spacing-8)',
                    backgroundColor: step.id < currentStep
                      ? 'var(--ai-color-brand-primary)'
                      : 'var(--ai-color-bg-secondary)',
                    minWidth: '20px',
                  }}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div>
        <CurrentStepComponent
          formData={formData}
          onNext={handleNext}
          onBack={handleBack}
          isFirstStep={currentStep === 1}
          isLastStep={currentStep === STEPS.length}
          onComplete={currentStep === STEPS.length ? onComplete : undefined}
        />
      </div>
    </div>
  );
};

