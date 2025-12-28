import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { agentsAPI } from '../../api/agents';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { ConfirmationModal } from '../common/ConfirmationModal';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { emailSchema } from '../../utils/validation';
import { formatDate } from '../../utils/format';
import { useUnsavedChanges } from '../../hooks/useUnsavedChanges';
import toast from 'react-hot-toast';

const agentSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: emailSchema,
  phone_number: z.string().optional(),
  extension: z.string().optional(),
  skills: z.string().optional(),
  departments: z.string().optional(),
});

type AgentFormData = z.infer<typeof agentSchema>;

export const AgentManager: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<any>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    isOpen: boolean;
    agentId: string | null;
  }>({ isOpen: false, agentId: null });
  const [showCloseConfirm, setShowCloseConfirm] = useState(false);

  const { data: agents, isLoading, refetch } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsAPI.list(),
  });

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
  });

  // Track unsaved changes
  const formValues = watch();
  const defaultValues = {
    name: '',
    email: '',
    phone_number: '',
    extension: '',
    skills: '',
    departments: '',
  };
  const hasUnsavedChanges = isModalOpen && JSON.stringify(formValues) !== JSON.stringify(defaultValues);
  
  useUnsavedChanges({
    hasUnsavedChanges: hasUnsavedChanges,
    message: 'You have unsaved changes. Are you sure you want to leave?',
  });

  const handleCreate = () => {
    setEditingAgent(null);
    reset();
    setIsModalOpen(true);
  };

  const handleEdit = (agent: any) => {
    setEditingAgent(agent);
    reset({
      name: agent.name,
      email: agent.email,
      phone_number: agent.phone_number || '',
      extension: agent.extension || '',
      skills: agent.skills.join(', ') || '',
      departments: agent.departments.join(', ') || '',
    });
    setIsModalOpen(true);
  };

  const onSubmit = async (data: AgentFormData) => {
    try {
      const agentData = {
        ...data,
        skills: data.skills ? data.skills.split(',').map((s) => s.trim()) : [],
        departments: data.departments
          ? data.departments.split(',').map((d) => d.trim())
          : [],
      };

      if (editingAgent) {
        await agentsAPI.update(editingAgent.id, agentData);
        toast.success('Agent updated successfully');
      } else {
        await agentsAPI.create(agentData);
        toast.success('Agent created successfully');
      }

      setIsModalOpen(false);
      reset();
      refetch();
    } catch (error) {
      toast.error('Failed to save agent');
    }
  };

  const handleToggleAvailability = async (agent: any) => {
    try {
      await agentsAPI.updateAvailability(agent.id, !agent.is_available);
      toast.success('Availability updated');
      refetch();
    } catch (error) {
      toast.error('Failed to update availability');
    }
  };

  const handleDeleteClick = (id: string) => {
    setDeleteConfirm({ isOpen: true, agentId: id });
  };

  const handleDeleteConfirm = async () => {
    if (deleteConfirm.agentId === null) return;

    try {
      await agentsAPI.delete(deleteConfirm.agentId);
      toast.success('Agent deleted');
      refetch();
      setDeleteConfirm({ isOpen: false, agentId: null });
    } catch (error) {
      toast.error('Failed to delete agent');
    }
  };

  return (
    <>
      <Card
        title="Human Agents"
        actions={
          <Button variant="primary" size="sm" onClick={handleCreate}>
            + Add Agent
          </Button>
        }
      >
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : !agents?.length ? (
          <div className="text-center py-8 text-gray-500">
            <p>No agents found</p>
            <Button variant="primary" size="sm" onClick={handleCreate} className="mt-4">
              Add Your First Agent
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                      <Badge
                        variant={agent.is_available ? 'success' : 'default'}
                        size="sm"
                      >
                        {agent.is_available ? 'Available' : 'Unavailable'}
                      </Badge>
                      {!agent.is_active && (
                        <Badge variant="default" size="sm">
                          Inactive
                        </Badge>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 space-y-1">
                      <div>{agent.email}</div>
                      {agent.phone_number && <div>Phone: {agent.phone_number}</div>}
                      {agent.extension && <div>Extension: {agent.extension}</div>}
                      <div>
                        Calls Handled: {agent.total_calls_handled} | Rating:{' '}
                        {agent.average_rating ? agent.average_rating.toFixed(1) : 'N/A'}⭐
                      </div>
                      {agent.skills.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {agent.skills.map((skill, i) => (
                            <Badge key={i} variant="info" size="sm">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      )}
                      <div className="text-xs text-gray-500 mt-2">
                        Created: {formatDate(agent.created_at)}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col space-y-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleAvailability(agent)}
                    >
                      {agent.is_available ? 'Set Unavailable' : 'Set Available'}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(agent)}>
                      Edit
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDeleteClick(agent.id)}
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

      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          if (hasUnsavedChanges) {
            setShowCloseConfirm(true);
            return;
          }
          setIsModalOpen(false);
          reset();
        }}
        title={editingAgent ? 'Edit Agent' : 'Add Agent'}
        size="md"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Name"
            {...register('name')}
            error={errors.name?.message}
          />
          <Input
            label="Email"
            type="email"
            {...register('email')}
            error={errors.email?.message}
          />
          <Input
            label="Phone Number (optional)"
            {...register('phone_number')}
            error={errors.phone_number?.message}
          />
          <Input
            label="Extension (optional)"
            {...register('extension')}
            error={errors.extension?.message}
          />
          <Input
            label="Skills (comma-separated)"
            {...register('skills')}
            error={errors.skills?.message}
            placeholder="Customer Service, Technical Support"
          />
          <Input
            label="Departments (comma-separated)"
            {...register('departments')}
            error={errors.departments?.message}
            placeholder="Sales, Support"
          />
          <div className="flex justify-end space-x-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                if (hasUnsavedChanges) {
                  setShowCloseConfirm(true);
                  return;
                }
                setIsModalOpen(false);
                reset();
              }}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              {editingAgent ? 'Update' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteConfirm.isOpen}
        onClose={() => setDeleteConfirm({ isOpen: false, agentId: null })}
        onConfirm={handleDeleteConfirm}
        title="Delete Agent"
        message="Are you sure you want to delete this agent? This action cannot be undone. If the agent has active calls, they will need to be reassigned."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />

      {/* Close Confirmation Modal */}
      <ConfirmationModal
        isOpen={showCloseConfirm}
        onClose={() => setShowCloseConfirm(false)}
        onConfirm={() => {
          setIsModalOpen(false);
          reset();
          setShowCloseConfirm(false);
        }}
        title="Unsaved Changes"
        message="You have unsaved changes. Are you sure you want to close? All changes will be lost."
        confirmLabel="Close"
        cancelLabel="Cancel"
        variant="warning"
      />
    </>
  );
};

