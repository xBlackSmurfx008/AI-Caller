import React from 'react';
import { Card } from '../common/Card';
import { formatPercentage, formatScore } from '../../utils/format';
import { cn } from '../../utils/helpers';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  icon?: React.ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon,
  variant = 'default',
  onClick,
}) => {
  const variants = {
    default: 'border-gray-200',
    primary: 'border-primary-200 bg-primary-50/50',
    success: 'border-green-200 bg-green-50/50',
    warning: 'border-yellow-200 bg-yellow-50/50',
    danger: 'border-red-200 bg-red-50/50',
  };

  return (
    <Card
      className={cn(
        'transition-chatkit',
        variants[variant],
        onClick && 'cursor-pointer hover:shadow-chatkit-md'
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            {icon && <div className="text-lg">{icon}</div>}
            <p className="text-xs font-medium text-gray-600">{title}</p>
          </div>
          <p className="mt-1.5 text-2xl font-semibold text-gray-800">{value}</p>
          {subtitle && (
            <p className="mt-1 text-xs text-gray-500">{subtitle}</p>
          )}
          {trend && (
            <div className="mt-2.5 flex items-center gap-1.5">
              <div
                className={cn(
                  'flex items-center gap-1 text-xs font-semibold',
                  trend.isPositive ? 'text-green-600' : 'text-red-600'
                )}
              >
                <span>{trend.isPositive ? '↑' : '↓'}</span>
                <span>{Math.abs(trend.value).toFixed(1)}%</span>
              </div>
              <span className="text-xs text-gray-400">vs last period</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
