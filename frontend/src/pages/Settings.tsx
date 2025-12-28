import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { configAPI } from '../api/config';
import { agentsAPI } from '../api/agents';
import { useConfigStore } from '../store/configStore';
import { BusinessConfigList } from '../components/config/BusinessConfigList';
import { BusinessConfigForm } from '../components/config/BusinessConfigForm';
import { KnowledgeBaseManager } from '../components/config/KnowledgeBaseManager';
import { AgentManager } from '../components/config/AgentManager';
import { PhoneNumberManager } from '../components/phone/PhoneNumberManager';
import { SetupWizard } from '../components/setup/SetupWizard';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { cn } from '../utils/helpers';
import type { BusinessConfig } from '../types/config';
import toast from 'react-hot-toast';

const TABS = [
  { id: 'business', label: 'Business Configs' },
  { id: 'knowledge', label: 'Knowledge Base' },
  { id: 'agents', label: 'Agents' },
  { id: 'phone-numbers', label: 'Phone Numbers' },
];

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('business');
  const [isConfigFormOpen, setIsConfigFormOpen] = useState(false);
  const [isSetupWizardOpen, setIsSetupWizardOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<BusinessConfig | null>(null);
  const { setBusinessConfigs, setAgents } = useConfigStore();

  const { data: configs, refetch: refetchConfigs } = useQuery({
    queryKey: ['business-configs'],
    queryFn: () => configAPI.listBusinessConfigs(),
    onSuccess: (data) => {
      setBusinessConfigs(data);
    },
  });

  const { refetch: refetchAgents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsAPI.list(),
    onSuccess: (data) => {
      setAgents(data);
    },
  });

  const handleCreateConfig = () => {
    console.log('handleCreateConfig called');
    // If no configs exist, open setup wizard; otherwise open config form
    if (!configs || configs.length === 0) {
      setIsSetupWizardOpen(true);
    } else {
      setEditingConfig(null);
      setIsConfigFormOpen(true);
    }
  };

  const handleSetupWizardClose = () => {
    setIsSetupWizardOpen(false);
    // Refetch configs after setup wizard closes
    refetchConfigs();
  };

  const handleSetupWizardComplete = () => {
    setIsSetupWizardOpen(false);
    // Refetch configs after setup wizard completes
    refetchConfigs();
    toast.success('Setup completed successfully!');
  };

  const handleEditConfig = (config: BusinessConfig) => {
    setEditingConfig(config);
    setIsConfigFormOpen(true);
  };

  const handleConfigFormSuccess = () => {
    refetchConfigs();
  };

  const handleConfigFormClose = () => {
    setIsConfigFormOpen(false);
    setEditingConfig(null);
  };

  const handleDeleteConfig = async (id: string) => {
    try {
      await configAPI.deleteBusinessConfig(id);
      toast.success('Configuration deleted');
      refetchConfigs();
    } catch (error) {
      toast.error('Failed to delete configuration');
    }
  };

  return (
    <div className="space-y-5 p-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-800">Settings</h1>
        <p className="mt-0.5 text-sm text-gray-500">
          Manage your business configurations, agents, and knowledge base
        </p>
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: '0.5px solid var(--ai-color-border-heavy)' }}>
        <nav style={{ display: 'flex', gap: 'var(--ai-spacing-12)' }}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setActiveTab(tab.id);
              }}
              style={{
                padding: 'var(--ai-spacing-6) var(--ai-spacing-4)',
                borderBottom: `2px solid ${activeTab === tab.id ? 'var(--ai-color-brand-primary)' : 'transparent'}`,
                fontSize: 'var(--ai-font-size-body-small)',
                fontWeight: 'var(--ai-font-weight-medium)',
                color: activeTab === tab.id ? 'var(--ai-color-text-primary)' : 'var(--ai-color-text-secondary)',
                backgroundColor: 'transparent',
                borderTop: 'none',
                borderLeft: 'none',
                borderRight: 'none',
                cursor: 'pointer',
                transition: 'border-color 0.15s ease, color 0.15s ease',
              }}
              onMouseEnter={(e) => {
                if (activeTab !== tab.id) {
                  e.currentTarget.style.color = 'var(--ai-color-text-primary)';
                  e.currentTarget.style.borderBottomColor = 'var(--ai-color-border-default)';
                }
              }}
              onMouseLeave={(e) => {
                if (activeTab !== tab.id) {
                  e.currentTarget.style.color = 'var(--ai-color-text-secondary)';
                  e.currentTarget.style.borderBottomColor = 'transparent';
                }
              }}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'business' && (
          <BusinessConfigList
            configs={configs || []}
            onEdit={handleEditConfig}
            onDelete={handleDeleteConfig}
            onCreate={handleCreateConfig}
          />
        )}

        {activeTab === 'knowledge' && <KnowledgeBaseManager />}

        {activeTab === 'agents' && <AgentManager />}

        {activeTab === 'phone-numbers' && <PhoneNumberManager />}
      </div>

      {/* Business Config Form Modal */}
      <BusinessConfigForm
        isOpen={isConfigFormOpen}
        onClose={handleConfigFormClose}
        editingConfig={editingConfig}
        onSuccess={handleConfigFormSuccess}
      />

      {/* Setup Wizard Modal */}
      <Modal
        isOpen={isSetupWizardOpen}
        onClose={handleSetupWizardClose}
        title="Initial Setup - Configure Your System"
        size="large"
      >
        <SetupWizard 
          onComplete={handleSetupWizardComplete}
          onClose={handleSetupWizardClose}
        />
      </Modal>
    </div>
  );
};
