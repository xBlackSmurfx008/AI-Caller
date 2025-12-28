import React from 'react';
import {
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
import type { QAScoreDistribution } from '../../types/analytics';

interface QAScoreChartProps {
  data: QAScoreDistribution[];
}

export const QAScoreChart: React.FC<QAScoreChartProps> = ({ data }) => {
  return (
    <Card title="QA Score Distribution">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="range" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="count" fill="#2563eb" name="Number of Calls" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

