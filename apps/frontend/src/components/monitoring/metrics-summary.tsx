'use client';

import { Card, CardContent } from '@/components/ui/card';
import { BarChart3, GitBranch, CheckCircle, AlertCircle, DollarSign, Zap } from 'lucide-react';
import { formatNumber } from '@/lib/utils';

const metrics = [
  {
    name: 'Active Workflows',
    value: '12',
    change: '+2',
    changeType: 'increase',
    icon: GitBranch,
    color: 'text-blue-500',
  },
  {
    name: 'Completed Today',
    value: '8',
    change: '+3',
    changeType: 'increase',
    icon: CheckCircle,
    color: 'text-green-500',
  },
  {
    name: 'Failed Tasks',
    value: '2',
    change: '-1',
    changeType: 'decrease',
    icon: AlertCircle,
    color: 'text-red-500',
  },
  {
    name: 'Tokens Used',
    value: '1.2M',
    change: '+15%',
    changeType: 'increase',
    icon: Zap,
    color: 'text-purple-500',
  },
  {
    name: 'Estimated Cost',
    value: '$42.50',
    change: '+$5.20',
    changeType: 'increase',
    icon: DollarSign,
    color: 'text-orange-500',
  },
  {
    name: 'Avg Duration',
    value: '12m 34s',
    change: '-2m',
    changeType: 'decrease',
    icon: BarChart3,
    color: 'text-cyan-500',
  },
];

export function MetricsSummary() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {metrics.map((metric) => (
        <Card key={metric.name}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">{metric.name}</p>
                <p className="text-2xl font-bold mt-1">{metric.value}</p>
              </div>
              <div className={`p-3 rounded-lg bg-primary/10 ${metric.color}`}>
                <metric.icon className="h-6 w-6" />
              </div>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <span
                className={`text-xs font-medium ${
                  metric.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {metric.change} vs last week
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}