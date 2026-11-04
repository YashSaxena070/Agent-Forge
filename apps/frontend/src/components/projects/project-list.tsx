'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, FolderKanban, GitBranch, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { formatRelativeTime, statusColor } from '@/lib/utils';

const mockProjects = [
  {
    id: '1',
    name: 'E-Commerce Platform',
    description: 'Full-stack e-commerce solution with payment integration',
    status: 'active',
    workflows: 3,
    lastActivity: '2 hours ago',
    techStack: ['React', 'Node.js', 'PostgreSQL', 'Docker'],
  },
  {
    id: '2',
    name: 'Task Management App',
    description: 'Collaborative task management with real-time updates',
    status: 'active',
    workflows: 1,
    lastActivity: '5 hours ago',
    techStack: ['Next.js', 'TypeScript', 'Prisma', 'PostgreSQL'],
  },
  {
    id: '3',
    name: 'Analytics Dashboard',
    description: 'Real-time analytics dashboard for business metrics',
    status: 'archived',
    workflows: 0,
    lastActivity: '3 days ago',
    techStack: ['Vue.js', 'Python', 'FastAPI', 'ClickHouse'],
  },
];

export function ProjectList() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Projects</CardTitle>
        <Button size="sm" asChild>
          <a href="/projects/new">
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </a>
        </Button>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockProjects.map((project) => (
            <div
              key={project.id}
              className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <FolderKanban className="h-10 w-10 text-primary" />
                <div>
                  <h3 className="font-medium">{project.name}</h3>
                  <p className="text-sm text-muted-foreground">{project.description}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <GitBranch className="h-3 w-3" />
                      {project.workflows} workflows
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {project.lastActivity}
                    </span>
                  </div>
                  <div className="flex gap-1 mt-2">
                    {project.techStack.slice(0, 3).map((tech) => (
                      <span
                        key={tech}
                        className="px-2 py-0.5 text-xs rounded bg-secondary text-secondary-foreground"
                      >
                        {tech}
                      </span>
                    ))}
                    {project.techStack.length > 3 && (
                      <span className="px-2 py-0.5 text-xs rounded bg-secondary text-secondary-foreground">
                        +{project.techStack.length - 3}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded-full text-xs ${statusColor(project.status)}`}>
                  {project.status}
                </span>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <GitBranch className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}