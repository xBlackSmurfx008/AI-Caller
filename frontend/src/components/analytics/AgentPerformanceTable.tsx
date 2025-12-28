import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { formatCallDuration } from '../../utils/format';
import type { HumanAgent } from '../../types/agent';

interface AgentPerformanceTableProps {
  agents: HumanAgent[];
}

export const AgentPerformanceTable: React.FC<AgentPerformanceTableProps> = ({ agents }) => {
  return (
    <Card title="Agent Performance">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agent
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Calls Handled
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Average Rating
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Skills
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {agents.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No agents found
                </td>
              </tr>
            ) : (
              agents.map((agent) => (
                <tr key={agent.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                      <div className="text-sm text-gray-500">{agent.email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge
                      variant={agent.is_available ? 'success' : 'default'}
                      size="sm"
                    >
                      {agent.is_available ? 'Available' : 'Unavailable'}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {agent.total_calls_handled}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {agent.average_rating ? (
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-gray-900">
                          {agent.average_rating.toFixed(1)}
                        </span>
                        <span className="ml-1 text-yellow-400">⭐</span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-500">N/A</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {agent.skills.slice(0, 3).map((skill, index) => (
                        <Badge key={index} variant="info" size="sm">
                          {skill}
                        </Badge>
                      ))}
                      {agent.skills.length > 3 && (
                        <Badge variant="default" size="sm">
                          +{agent.skills.length - 3}
                        </Badge>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

