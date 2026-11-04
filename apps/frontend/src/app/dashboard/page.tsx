'use client';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { ProjectList } from '@/components/projects/project-list';
import { WorkflowOverview } from '@/components/workflows/workflow-overview';
import { MetricsSummary } from '@/components/monitoring/metrics-summary';

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">Overview of your projects and workflows</p>
          </div>
        </div>
        
        <MetricsSummary />
        
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
          <div className="col-span-4">
            <ProjectList />
          </div>
          <div className="col-span-3">
            <WorkflowOverview />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}