import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '../common/Input';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { emailSchema } from '../../utils/validation';
import toast from 'react-hot-toast';

const agentSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: emailSchema,
  phone_number: z.string().optional(),
  extension: z.string().optional(),
  skills: z.array(z.string()).default([]),
});

type AgentData = z.infer<typeof agentSchema>;

interface AgentsStepProps {
  formData: any;
  onNext: (data: any) => void;
  onBack: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export const AgentsStep: React.FC<AgentsStepProps> = ({
  formData,
  onNext,
  onBack,
  isFirstStep,
}) => {
  const [agents, setAgents] = useState<AgentData[]>(
    formData.agents || []
  );
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSkill, setNewSkill] = useState('');

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<AgentData>({
    resolver: zodResolver(agentSchema),
  });

  const currentSkills = watch('skills') || [];

  const handleAddAgent = (data: AgentData) => {
    setAgents([...agents, { ...data, skills: currentSkills }]);
    reset();
    setShowAddForm(false);
    setNewSkill('');
    toast.success('Agent added');
  };

  const handleAddSkill = () => {
    if (newSkill && !currentSkills.includes(newSkill)) {
      // This would need to be handled differently with react-hook-form
      // For now, we'll manage it in state
    }
  };

  const handleRemoveAgent = (index: number) => {
    setAgents(agents.filter((_, i) => i !== index));
  };

  const handleNext = () => {
    onNext({ agents });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Human Agents</h2>
        <p className="text-gray-600">
          Add human agents who can handle escalated calls
        </p>
      </div>

      <div className="space-y-4">
        {agents.length > 0 && (
          <Card title="Added Agents">
            <div className="space-y-3">
              {agents.map((agent, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <div className="text-sm text-gray-600">{agent.email}</div>
                    {agent.skills.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {agent.skills.map((skill, i) => (
                          <Badge key={i} variant="info" size="sm">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveAgent(index)}
                  >
                    Remove
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        )}

        {showAddForm ? (
          <Card title="Add Agent">
            <form onSubmit={handleSubmit(handleAddAgent)} className="space-y-4">
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
              <div className="flex space-x-2">
                <Button type="submit" variant="primary">
                  Add Agent
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setShowAddForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </Card>
        ) : (
          <Button variant="secondary" onClick={() => setShowAddForm(true)}>
            + Add Agent
          </Button>
        )}
      </div>

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

