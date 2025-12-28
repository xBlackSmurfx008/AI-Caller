import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { phoneNumbersApi } from '../../api/phoneNumbers';
import { agentsAPI } from '../../api/agents';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import toast from 'react-hot-toast';
import type { PhoneNumber } from '../../types/phoneNumber';

interface PhoneNumberAssignmentProps {
  isOpen: boolean;
  onClose: () => void;
  phoneNumber: PhoneNumber;
}

export const PhoneNumberAssignment: React.FC<PhoneNumberAssignmentProps> = ({
  isOpen,
  onClose,
  phoneNumber,
}) => {
  const [activeTab, setActiveTab] = useState<'agents' | 'businesses'>('agents');
  const queryClient = useQueryClient();

  const { data: assignments, isLoading: isLoadingAssignments } = useQuery({
    queryKey: ['phone-assignments', phoneNumber.id],
    queryFn: () => phoneNumbersApi.getAssignments(phoneNumber.id),
    enabled: isOpen,
  });

  const { data: agents, isLoading: isLoadingAgents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsAPI.list(),
    enabled: isOpen && activeTab === 'agents',
  });

  const assignToAgentMutation = useMutation({
    mutationFn: ({ agentId, isPrimary }: { agentId: string; isPrimary: boolean }) =>
      phoneNumbersApi.assignToAgent(phoneNumber.id, agentId, { is_primary: isPrimary }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phone-assignments', phoneNumber.id] });
      queryClient.invalidateQueries({ queryKey: ['phone-numbers'] });
      toast.success('Phone number assigned to agent');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to assign phone number');
    },
  });

  const unassignFromAgentMutation = useMutation({
    mutationFn: (agentId: string) =>
      phoneNumbersApi.unassignFromAgent(phoneNumber.id, agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phone-assignments', phoneNumber.id] });
      queryClient.invalidateQueries({ queryKey: ['phone-numbers'] });
      toast.success('Phone number unassigned from agent');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to unassign phone number');
    },
  });

  const handleAssignAgent = (agentId: string, isPrimary: boolean) => {
    assignToAgentMutation.mutate({ agentId, isPrimary });
  };

  const handleUnassignAgent = (agentId: string) => {
    unassignFromAgentMutation.mutate(agentId);
  };

  const assignedAgentIds = assignments?.agents.map((a) => a.agent_id) || [];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Assign: ${phoneNumber.phone_number}`} size="large">
      <div className="space-y-6">
        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('agents')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'agents'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Agents
            </button>
            <button
              onClick={() => setActiveTab('businesses')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'businesses'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Businesses
            </button>
          </nav>
        </div>

        {/* Agents Tab */}
        {activeTab === 'agents' && (
          <div className="space-y-4">
            {isLoadingAgents || isLoadingAssignments ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : (
              <>
                {/* Current Assignments */}
                {assignments && assignments.agents.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Current Assignments
                    </h3>
                    <div className="space-y-2">
                      {assignments.agents.map((assignment) => (
                        <div
                          key={assignment.assignment_id}
                          className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900 dark:text-white">
                              {assignment.agent_name}
                            </span>
                            {assignment.is_primary && (
                              <Badge variant="success">Primary</Badge>
                            )}
                          </div>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleUnassignAgent(assignment.agent_id)}
                            disabled={unassignFromAgentMutation.isPending}
                          >
                            Unassign
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Available Agents */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Available Agents
                  </h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {agents
                      ?.filter((agent) => !assignedAgentIds.includes(agent.id))
                      .map((agent) => (
                        <div
                          key={agent.id}
                          className="flex justify-between items-center p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
                        >
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">
                              {agent.name}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {agent.email}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => handleAssignAgent(agent.id, false)}
                              disabled={assignToAgentMutation.isPending}
                            >
                              Assign
                            </Button>
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleAssignAgent(agent.id, true)}
                              disabled={assignToAgentMutation.isPending}
                            >
                              Set as Primary
                            </Button>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* Businesses Tab */}
        {activeTab === 'businesses' && (
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            Business assignment feature coming soon
          </div>
        )}

        <div className="flex justify-end pt-4 border-t">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};

