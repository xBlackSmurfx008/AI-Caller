import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card } from '../common/Card';
import type { CallVolumeData } from '../../types/analytics';

interface CallVolumeChartProps {
  data: CallVolumeData[];
  interval: 'hour' | 'day' | 'week' | 'month';
}

export const CallVolumeChart: React.FC<CallVolumeChartProps> = ({ data, interval }) => {
  return (
    <Card title="Call Volume Over Time">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="total_calls"
            stroke="#2563eb"
            strokeWidth={2}
            name="Total Calls"
          />
          <Line
            type="monotone"
            dataKey="inbound_calls"
            stroke="#10b981"
            strokeWidth={2}
            name="Inbound"
          />
          <Line
            type="monotone"
            dataKey="outbound_calls"
            stroke="#f59e0b"
            strokeWidth={2}
            name="Outbound"
          />
          <Line
            type="monotone"
            dataKey="escalated_calls"
            stroke="#ef4444"
            strokeWidth={2}
            name="Escalated"
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};

