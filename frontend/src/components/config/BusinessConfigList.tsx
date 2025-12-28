import React, { useState } from 'react';
import type { BusinessConfig } from '../../types/config';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { ConfirmationModal } from '../common/ConfirmationModal';
import { formatDate } from '../../utils/format';

interface BusinessConfigListProps {
  configs: BusinessConfig[];
  onEdit: (config: BusinessConfig) => void;
  onDelete: (id: string) => void;
  onCreate: () => void;
}

export const BusinessConfigList: React.FC<BusinessConfigListProps> = ({
  configs,
  onEdit,
  onDelete,
  onCreate,
}) => {
  const [deleteConfirm, setDeleteConfirm] = useState<{
    isOpen: boolean;
    config: BusinessConfig | null;
  }>({ isOpen: false, config: null });

  const handleDeleteClick = (config: BusinessConfig) => {
    setDeleteConfirm({ isOpen: true, config });
  };

  const handleDeleteConfirm = async () => {
    if (deleteConfirm.config) {
      await onDelete(deleteConfirm.config.id);
      setDeleteConfirm({ isOpen: false, config: null });
    }
  };

  return (
    <>
      <Card
        title="Business Configurations"
        actions={
          <Button variant="primary" size="sm" onClick={onCreate}>
            + Create Config
          </Button>
        }
      >
      {configs.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">No business configurations found</p>
          <Button variant="primary" size="sm" onClick={onCreate} className="mt-3">
            Create Your First Configuration
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {configs.map((config) => (
            <div
              key={config.id}
              className="p-4 border border-gray-200 rounded-md hover:bg-gray-50 transition-chatkit"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <h3 className="text-sm font-semibold text-gray-800">{config.name}</h3>
                    <Badge variant={config.is_active ? 'success' : 'default'} size="sm">
                      {config.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    <Badge variant="info" size="sm">
                      {config.type}
                    </Badge>
                  </div>
                  <div className="text-xs text-gray-600 space-y-1">
                    <div>
                      <span className="font-medium">AI Model:</span> {config.config_data.ai.model}
                    </div>
                    <div>
                      <span className="font-medium">Voice:</span> {config.config_data.voice.voice}
                    </div>
                    <div>
                      <span className="font-medium">Knowledge Base:</span>{' '}
                      {config.config_data.knowledge_base.enabled ? 'Enabled' : 'Disabled'}
                    </div>
                    <div className="text-xs text-gray-400 mt-1.5">
                      Created: {formatDate(config.created_at)} | Updated:{' '}
                      {formatDate(config.updated_at)}
                    </div>
                  </div>
                </div>
                <div className="flex gap-1.5 ml-4">
                  <Button variant="ghost" size="sm" onClick={() => onEdit(config)}>
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDeleteClick(config)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      </Card>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteConfirm.isOpen}
        onClose={() => setDeleteConfirm({ isOpen: false, config: null })}
        onConfirm={handleDeleteConfirm}
        title="Delete Configuration"
        message={
          deleteConfirm.config
            ? `Are you sure you want to delete "${deleteConfirm.config.name}"? This action cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </>
  );
};

