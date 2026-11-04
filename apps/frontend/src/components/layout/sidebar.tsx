'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  FolderKanban,
  GitBranch,
  Bot,
  Box,
  Shield,
  Settings,
  BarChart3,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Workflows', href: '/workflows', icon: GitBranch },
  { name: 'Agents', href: '/agents', icon: Bot },
  { name: 'Deployments', href: '/deployments', icon: Box },
  { name: 'Security', href: '/security', icon: Shield },
  { name: 'Monitoring', href: '/monitoring', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  
  return (
    <aside className="fixed left-0 top-0 z-40 w-64 h-screen border-r bg-card transition-all duration-200">
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center px-6 border-b">
          <Link href="/dashboard" className="flex items-center gap-2 font-bold text-xl">
            <Bot className="h-8 w-8 text-primary" />
            <span>AgentForge</span>
          </Link>
        </div>
        
        <nav className="flex-1 space-y-1 p-4" aria-label="Main navigation">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                {item.name}
              </Link>
            );
          })}
        </nav>
        
        <div className="border-t p-4">
          <div className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm">
            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
              <span className="text-primary font-medium">JD</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">John Doe</p>
              <p className="text-xs text-muted-foreground truncate">john@agentforge.dev</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}