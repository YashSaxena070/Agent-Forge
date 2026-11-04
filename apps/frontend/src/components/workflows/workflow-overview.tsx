'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { GitBranch, Play, Pause, CheckCircle, AlertCircle, Loader2, Clock } from 'lucide-react';
import { formatRelativeTime, formatDuration, statusColor } from '@/lib/utils';

const mockWorkflows = [
  {
    id: '1',
    name: 'Build User Auth System',
    project: 'E-Commerce Platform',
    status: 'running',
    phase: 'implementation',
    progress: 65,
    startedAt: '2 hours ago',
    duration: 7200,
  },
  {
    id: '2',
    name: 'Design Database Schema',
    project: 'Task Management App',
    status: 'completed',
    phase: 'design',
    progress: 100,
    startedAt: '1 day ago',
    duration: 18000,
  },
  {
    id: '3',
    name: 'Setup CI/CD Pipeline',
    project: 'E-Commerce Platform',
    status: 'pending',
    phase: 'deployment',
    progress: 0,
    startedAt: 'Just now',
    duration: 0,
  },
  {
    id: '4',
    name: 'Implement Payment Integration',
    project: 'E-Commerce Platform',
    status: 'failed',
    phase: 'implementation',
    progress: 40,
    startedAt: '3 hours ago',
    duration: 10800,
  },
];

export function WorkflowOverview() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Workflows</CardTitle>
        <Badge variant="secondary">4 active</Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {mockWorkflows.map((workflow) => (
            <div
              key={workflow.id}
              className="p-4 rounded-lg border hover:bg-accent/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium truncate">{workflow.name}</h4>
                    <Badge variant="outline" className="text-xs">
                      {workflow.project}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Phase: {workflow.phase}
                  </p>
                  <div className="mt-2 h-2 w-full bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${workflow.progress}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                    <span>{workflow.progress}% complete</span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {workflow.duration > 0 ? formatDuration(workflow.duration) : 'Not started'}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2 shrink-0">
                  <Badge className={statusColor(workflow.status)}>
                    {workflow.status === 'running' && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                    {workflow.status === 'completed' && <CheckCircle className="mr-1 h-3 w-3" />}
                    {workflow.status === 'failed' && <AlertCircle className="mr-1 h-3 w-3" />}
                    {workflow.status === 'pending' && <Clock className="mr-1 h-3 w-3" />}
                    {workflow.status.charAt(0).toUpperCase() + workflow.status.slice(1)}
                  </Badge>
                  <div className="flex items-center gap-1">
                    {workflow.status === 'running' && (
                      <Button variant="ghost" size="icon" className="h-7 w-7">
                        <Pause className="h-4 w-4" />
                      </Button>
                    )}
                    {workflow.status === 'pending' && (
                      <Button variant="ghost" size="icon" className="h-7 w-7">
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}