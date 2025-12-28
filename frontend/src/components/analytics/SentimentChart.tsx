import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import { Card } from '../common/Card';

interface SentimentChartProps {
  data: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

const COLORS = {
  positive: '#10b981',
  neutral: '#f59e0b',
  negative: '#ef4444',
};

export const SentimentChart: React.FC<SentimentChartProps> = ({ data }) => {
  const chartData = [
    { name: 'Positive', value: data.positive, color: COLORS.positive },
    { name: 'Neutral', value: data.neutral, color: COLORS.neutral },
    { name: 'Negative', value: data.negative, color: COLORS.negative },
  ];

  const total = data.positive + data.neutral + data.negative;

  return (
    <Card title="Sentiment Distribution">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-green-600">{data.positive}</div>
          <div className="text-sm text-gray-600">Positive</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-yellow-600">{data.neutral}</div>
          <div className="text-sm text-gray-600">Neutral</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-red-600">{data.negative}</div>
          <div className="text-sm text-gray-600">Negative</div>
        </div>
      </div>
    </Card>
  );
};

