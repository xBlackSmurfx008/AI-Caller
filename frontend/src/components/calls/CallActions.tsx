import React, { useState } from 'react';
import type { Call } from '../../types/call';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { callsAPI } from '../../api/calls';
import { agentsAPI } from '../../api/agents';
import { useConfigStore } from '../../store/configStore';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';

interface CallActionsProps {
  call: Call;
  onActionComplete?: () => void;
}

export const CallActions: React.FC<CallActionsProps> = ({ call, onActionComplete }) => {
  const [escalateModalOpen, setEscalateModalOpen] = useState(false);
  const [interveneModalOpen, setInterveneModalOpen] = useState(false);
  const [noteModalOpen, setNoteModalOpen] = useState(false);
  const [endCallModalOpen, setEndCallModalOpen] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [escalationReason, setEscalationReason] = useState('');
  const [interventionAction, setInterventionAction] = useState<'send_message' | 'pause' | 'resume' | 'override_instructions'>('send_message');
  const [interventionMessage, setInterventionMessage] = useState('');
  const [note, setNote] = useState('');
  const [endCallReason, setEndCallReason] = useState('');

  const { agents } = useConfigStore();
  const { data: agentsData } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsAPI.list(true, true),
    enabled: escalateModalOpen,
  });

  const availableAgents = agentsData || agents.filter(a => a.is_available && a.is_active);

  const handleEscalate = async () => {
    try {
      await callsAPI.escalate(call.id, {
        agent_id: selectedAgentId || undefined,
        reason: escalationReason,
      });
      toast.success('Call escalated successfully');
      setEscalateModalOpen(false);
      onActionComplete?.();
    } catch (error) {
      toast.error('Failed to escalate call');
    }
  };

  const handleIntervene = async () => {
    try {
      await callsAPI.intervene(call.id, {
        action: interventionAction,
        message: interventionAction === 'send_message' ? interventionMessage : undefined,
        instructions: interventionAction === 'override_instructions' ? interventionMessage : undefined,
      });
      toast.success('Intervention applied successfully');
      setInterveneModalOpen(false);
      onActionComplete?.();
    } catch (error) {
      toast.error('Failed to intervene');
    }
  };

  const handleAddNote = async () => {
    try {
      await callsAPI.addNote(call.id, { note });
      toast.success('Note added successfully');
      setNoteModalOpen(false);
      setNote('');
      onActionComplete?.();
    } catch (error) {
      toast.error('Failed to add note');
    }
  };

  const handleEndCall = async () => {
    try {
      await callsAPI.end(call.id, { reason: endCallReason });
      toast.success('Call ended');
      setEndCallModalOpen(false);
      onActionComplete?.();
    } catch (error) {
      toast.error('Failed to end call');
    }
  };

  return (
    <div className="px-4 py-3 bg-white border-t border-gray-200">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="primary"
            size="sm"
            onClick={() => setEscalateModalOpen(true)}
            disabled={call.status === 'escalated' || call.status === 'completed'}
          >
            Escalate
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setInterveneModalOpen(true)}
            disabled={call.status === 'completed'}
          >
            Intervene
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setNoteModalOpen(true)}
          >
            Add Note
          </Button>
        </div>
        <Button
          variant="danger"
          size="sm"
          onClick={() => setEndCallModalOpen(true)}
          disabled={call.status === 'completed'}
        >
          End Call
        </Button>
      </div>

      {/* Escalate Modal */}
      <Modal
        isOpen={escalateModalOpen}
        onClose={() => setEscalateModalOpen(false)}
        title="Escalate Call to Human Agent"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Transfer this call to a human agent. The agent will receive full context about the conversation.
          </p>
          <Select
            label="Select Agent"
            options={[
              { value: '', label: 'Auto-assign (recommended)' },
              ...availableAgents.map(agent => ({
                value: agent.id,
                label: `${agent.name} (${agent.email})`,
              })),
            ]}
            value={selectedAgentId}
            onChange={(e) => setSelectedAgentId(e.target.value)}
          />
          <Input
            label="Reason (optional)"
            value={escalationReason}
            onChange={(e) => setEscalationReason(e.target.value)}
            placeholder="Why is this call being escalated?"
            multiline
            rows={3}
          />
          <div className="flex justify-end space-x-2 pt-2">
            <Button variant="ghost" onClick={() => setEscalateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleEscalate}>
              Escalate Call
            </Button>
          </div>
        </div>
      </Modal>

      {/* Intervene Modal */}
      <Modal
        isOpen={interveneModalOpen}
        onClose={() => setInterveneModalOpen(false)}
        title="Intervene in Call"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Take control of the AI assistant's behavior during this call.
          </p>
          <Select
            label="Action Type"
            options={[
              { value: 'send_message', label: 'Send Message to AI' },
              { value: 'pause', label: 'Pause AI Responses' },
              { value: 'resume', label: 'Resume AI Responses' },
              { value: 'override_instructions', label: 'Override Instructions' },
            ]}
            value={interventionAction}
            onChange={(e) => setInterventionAction(e.target.value as any)}
          />
          {(interventionAction === 'send_message' || interventionAction === 'override_instructions') && (
            <Input
              label={interventionAction === 'send_message' ? 'Message to AI' : 'New Instructions'}
              value={interventionMessage}
              onChange={(e) => setInterventionMessage(e.target.value)}
              placeholder={interventionAction === 'send_message' ? 'Enter message for AI...' : 'Enter new instructions...'}
              multiline
              rows={4}
            />
          )}
          <div className="flex justify-end space-x-2 pt-2">
            <Button variant="ghost" onClick={() => setInterveneModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleIntervene}>
              Apply Intervention
            </Button>
          </div>
        </div>
      </Modal>

      {/* Add Note Modal */}
      <Modal
        isOpen={noteModalOpen}
        onClose={() => setNoteModalOpen(false)}
        title="Add Note to Call"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Add a note that will be saved with this call record for future reference.
          </p>
          <Input
            label="Note"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Enter your note..."
            multiline
            rows={5}
          />
          <div className="flex justify-end space-x-2 pt-2">
            <Button variant="ghost" onClick={() => setNoteModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleAddNote}>
              Save Note
            </Button>
          </div>
        </div>
      </Modal>

      {/* End Call Modal */}
      <Modal
        isOpen={endCallModalOpen}
        onClose={() => setEndCallModalOpen(false)}
        title="End Call"
        size="md"
      >
        <div className="space-y-4">
          <div className="p-4 bg-danger-50 border-2 border-danger-200 rounded-lg">
            <p className="text-sm font-medium text-danger-800">
              ⚠️ Are you sure you want to end this call?
            </p>
            <p className="text-xs text-danger-700 mt-1">
              This action cannot be undone. The call will be terminated immediately.
            </p>
          </div>
          <Input
            label="Reason (optional)"
            value={endCallReason}
            onChange={(e) => setEndCallReason(e.target.value)}
            placeholder="Why is this call being ended?"
            multiline
            rows={3}
          />
          <div className="flex justify-end space-x-2 pt-2">
            <Button variant="ghost" onClick={() => setEndCallModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleEndCall}>
              End Call
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
