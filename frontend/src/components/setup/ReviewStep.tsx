import React from 'react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { setupAPI } from '../../api/setup';

interface ReviewStepProps {
  formData: any;
  onNext: (data: any) => void;
  onBack: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
  onComplete?: () => void;
}

export const ReviewStep: React.FC<ReviewStepProps> = ({
  formData,
  onBack,
  onComplete,
}) => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleComplete = async () => {
    setIsSubmitting(true);
    try {
      // Prepare setup data from formData
      const setupData: any = {};
      
      // Business config
      if (formData.businessProfile) {
        setupData.business_config = {
          name: formData.businessProfile.name || 'Default Business',
          type: formData.businessProfile.type || 'customer_support',
          config_data: {
            ai: {
              model: formData.businessProfile.ai_model || 'gpt-4o',
              temperature: formData.businessProfile.temperature || 0.8,
              system_prompt: formData.businessProfile.system_prompt || '',
            },
            voice: {
              language: formData.businessProfile.language || 'en',
              voice: formData.businessProfile.voice || 'alloy',
            },
            knowledge_base: {
              enabled: formData.knowledgeBase ? true : false,
              retrieval_top_k: 5,
              similarity_threshold: 0.7,
            },
            quality_assurance: {
              enabled: formData.qaSettings?.enabled || false,
              sentiment_analysis: formData.qaSettings?.sentimentAnalysis || false,
              compliance_check: formData.qaSettings?.complianceCheck || false,
              min_score_threshold: 0.6,
            },
            escalation: {
              enabled: formData.escalationRules?.enabled || false,
              triggers: formData.escalationRules?.triggers || [],
              warm_transfer: formData.escalationRules?.warmTransfer || false,
            },
          },
        };
      }
      
      // Agents
      if (formData.agents && Array.isArray(formData.agents)) {
        setupData.agents = formData.agents.map((agent: any) => ({
          name: agent.name || '',
          email: agent.email || '',
          phone_number: agent.phone_number,
          extension: agent.extension,
          skills: agent.skills || [],
          departments: agent.departments || [],
          is_available: agent.is_available !== undefined ? agent.is_available : true,
          is_active: agent.is_active !== undefined ? agent.is_active : true,
        }));
      }
      
      // Knowledge base entries
      if (formData.knowledgeBase) {
        const kbEntries: any[] = [];
        
        // Documents
        if (formData.knowledgeBase.documents && Array.isArray(formData.knowledgeBase.documents)) {
          formData.knowledgeBase.documents.forEach((doc: any) => {
            kbEntries.push({
              title: doc.title || doc.name || 'Untitled Document',
              content: doc.content || '',
              source: doc.source || doc.url,
              source_type: doc.source_type || 'text',
            });
          });
        }
        
        // URLs
        if (formData.knowledgeBase.urls && Array.isArray(formData.knowledgeBase.urls)) {
          formData.knowledgeBase.urls.forEach((url: string) => {
            kbEntries.push({
              title: `URL: ${url}`,
              content: `Content from ${url}`,
              source: url,
              source_type: 'url',
            });
          });
        }
        
        if (kbEntries.length > 0) {
          setupData.knowledge_base = kbEntries;
        }
      }
      
      // API config (optional, for reference)
      if (formData.apiConfig) {
        setupData.api_config = formData.apiConfig;
      }
      
      // Call the setup completion API
      const result = await setupAPI.complete(setupData);
      
      if (result.success) {
        toast.success(result.message || 'Setup completed successfully!');
        
        // Call onNext with final data to trigger onComplete in SetupWizard
        onNext({ completed: true, result });
        
        // If onComplete is provided (from modal), use it; otherwise navigate
        if (onComplete) {
          onComplete();
        } else {
          navigate('/');
        }
      } else {
        toast.error('Setup completed with warnings');
      }
    } catch (error: any) {
      const errorMessage = error?.error?.message || error?.message || 'Failed to complete setup';
      toast.error(errorMessage);
      console.error('Setup completion error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Review & Complete</h2>
        <p className="text-gray-600">
          Review your configuration before completing setup
        </p>
      </div>

      <div className="space-y-4">
        <Card title="API Configuration">
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium">OpenAI:</span> Configured
            </div>
            <div>
              <span className="font-medium">Twilio:</span> Configured
            </div>
          </div>
        </Card>

        {formData.businessProfile && (
          <Card title="Business Profile">
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">Name:</span> {formData.businessProfile.name}
              </div>
              <div>
                <span className="font-medium">Type:</span> {formData.businessProfile.type}
              </div>
              <div>
                <span className="font-medium">AI Model:</span> {formData.businessProfile.ai_model}
              </div>
            </div>
          </Card>
        )}

        {formData.knowledgeBase && (
          <Card title="Knowledge Base">
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">Documents:</span>{' '}
                {formData.knowledgeBase.documents?.length || 0}
              </div>
              <div>
                <span className="font-medium">URLs:</span>{' '}
                {formData.knowledgeBase.urls?.length || 0}
              </div>
            </div>
          </Card>
        )}

        {formData.agents && (
          <Card title="Agents">
            <div className="text-sm">
              <span className="font-medium">Total Agents:</span>{' '}
              {formData.agents.length}
            </div>
          </Card>
        )}

        {formData.qaSettings && (
          <Card title="QA Settings">
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">QA Monitoring:</span>{' '}
                {formData.qaSettings.enabled ? 'Enabled' : 'Disabled'}
              </div>
              {formData.qaSettings.enabled && (
                <>
                  <div>
                    <span className="font-medium">Sentiment Analysis:</span>{' '}
                    {formData.qaSettings.sentimentAnalysis ? 'Enabled' : 'Disabled'}
                  </div>
                  <div>
                    <span className="font-medium">Compliance Check:</span>{' '}
                    {formData.qaSettings.complianceCheck ? 'Enabled' : 'Disabled'}
                  </div>
                </>
              )}
            </div>
          </Card>
        )}

        {formData.escalationRules && (
          <Card title="Escalation Rules">
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">Escalation:</span>{' '}
                {formData.escalationRules.enabled ? 'Enabled' : 'Disabled'}
              </div>
              {formData.escalationRules.enabled && (
                <>
                  <div>
                    <span className="font-medium">Warm Transfer:</span>{' '}
                    {formData.escalationRules.warmTransfer ? 'Enabled' : 'Disabled'}
                  </div>
                  <div>
                    <span className="font-medium">Keywords:</span>{' '}
                    {formData.escalationRules.keywords?.length || 0}
                  </div>
                </>
              )}
            </div>
          </Card>
        )}
      </div>

      <div className="flex justify-between pt-4">
        <Button type="button" variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button
          variant="primary"
          onClick={handleComplete}
          isLoading={isSubmitting}
        >
          Complete Setup
        </Button>
      </div>
    </div>
  );
};

