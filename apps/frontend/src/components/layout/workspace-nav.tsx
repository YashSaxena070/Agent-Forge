'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useProject } from '@/lib/project-context';

export function WorkspaceNav({
  currentSection,
  nextLink,
  nextLabel,
}: {
  currentSection?: string;
  nextLink?: string;
  nextLabel?: string;
}) {
  const pathname = usePathname();
  const { projects, activeProjectId, setActiveProjectId, isRunning } = useProject();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { name: 'Workflows', href: '/workflows' },
    { name: 'Agents', href: '/agents' },
    { name: 'Deployments', href: '/deployments' },
    { name: 'Security', href: '/security' },
    { name: 'Monitoring', href: '/monitoring' },
    { name: 'Settings', href: '/settings' },
  ];

  return (
    <header className="border-b border-[#d0d5cc] bg-[#eaede6] text-[#0a0d0c] sticky top-0 z-40 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 pt-4 pb-0">
        {/* Top Row */}
        <div className="flex items-center justify-between pb-3 sm:pb-4 gap-4">
          <div className="flex items-center gap-3 sm:gap-6">
            <Link
              href="/"
              className="flex items-center gap-2 text-lg sm:text-xl font-bold tracking-tight text-[#0a0d0c] hover:opacity-80 transition-opacity shrink-0"
            >
              <svg
                className="w-5 h-5 text-[#0a0d0c]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="3" y="3" width="18" height="18" rx="4" />
                <circle cx="12" cy="12" r="3" />
                <path d="M12 3v3M12 18v3M3 12h3M18 12h3" />
              </svg>
              <span>AgentForge</span>
            </Link>

            {/* Project Quick Switcher */}
            <div className="hidden md:flex items-center gap-2 bg-[#dde1d8] px-2.5 py-1 border border-[#cbd1c5] text-xs font-mono">
              <span className="text-[#6e736d]">PROJECT:</span>
              <select
                value={activeProjectId}
                onChange={(e) => setActiveProjectId(e.target.value)}
                className="bg-transparent font-bold text-black outline-none cursor-pointer text-xs"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              <span
                className={`w-2 h-2 rounded-full ml-1 ${
                  isRunning ? 'bg-[#0fa37a] animate-pulse' : 'bg-neutral-400'
                }`}
              />
            </div>
          </div>

          {/* Desktop Right Links */}
          <nav className="hidden sm:flex items-center gap-5 text-xs font-medium text-[#4f544e]">
            <Link
              href="/dashboard"
              className={`transition-colors hover:text-black ${
                pathname === '/dashboard' ? 'text-black font-semibold' : ''
              }`}
            >
              Dashboard
            </Link>
            <Link
              href="/projects"
              className={`transition-colors hover:text-black ${
                pathname.startsWith('/projects') ? 'text-black font-semibold' : ''
              }`}
            >
              Projects
            </Link>
            <Link href="/" className="transition-colors hover:text-black">
              Website
            </Link>

            {/* Authenticated Workspace User Profile Badge */}
            <div className="flex items-center gap-2 pl-3 border-l border-[#cbd1c5]">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" title="Session Authenticated: JWT Active" />
              <Link href="/settings" className="flex items-center gap-1.5 hover:opacity-80 transition-opacity">
                <span className="font-mono text-[11px] font-bold text-[#0a0d0c]">Yash S.</span>
                <span className="text-[10px] bg-black text-[#c4ff2e] px-1.5 py-0.5 font-mono uppercase font-bold tracking-tight">
                  DEVELOPER
                </span>
              </Link>
            </div>
          </nav>

          {/* Mobile Hamburger Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="sm:hidden p-1.5 text-black hover:bg-black/5"
            aria-label="Toggle navigation"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {mobileMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden py-3 border-t border-[#d0d5cc] space-y-3 text-xs font-mono">
            <div className="flex items-center justify-between bg-[#dde1d8] p-2 border border-[#cbd1c5]">
              <span className="text-[#6e736d]">SWITCH PROJECT:</span>
              <select
                value={activeProjectId}
                onChange={(e) => {
                  setActiveProjectId(e.target.value);
                  setMobileMenuOpen(false);
                }}
                className="bg-transparent font-bold text-black outline-none"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-4">
              <Link
                href="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="font-bold underline"
              >
                Dashboard
              </Link>
              <Link
                href="/projects"
                onClick={() => setMobileMenuOpen(false)}
                className="font-bold underline"
              >
                Projects
              </Link>
              <Link
                href="/"
                onClick={() => setMobileMenuOpen(false)}
                className="font-bold underline"
              >
                Website
              </Link>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-[#cbd1c5]">
              <span className="text-[#6e736d]">USER SESSION:</span>
              <span className="font-bold text-black flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#10b981]" />
                Yash Saxena (Developer)
              </span>
            </div>
          </div>
        )}

        {/* Sub-Nav Tabs - Fully horizontally scrollable on mobile */}
        <div className="flex items-center gap-6 sm:gap-8 text-xs overflow-x-auto no-scrollbar whitespace-nowrap scroll-smooth">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`pb-2.5 transition-all uppercase tracking-wider text-[11px] sm:text-xs shrink-0 ${
                  isActive
                    ? 'border-b-2 border-black font-black text-black'
                    : 'text-[#6e736d] hover:text-black border-b-2 border-transparent'
                }`}
              >
                {item.name}
              </Link>
            );
          })}
        </div>
      </div>
    </header>
  );
}

export function WorkspaceFooter({
  nextLabel,
  nextHref,
}: {
  nextLabel?: string;
  nextHref?: string;
}) {
  return (
    <div className="mt-14 sm:mt-16 space-y-6 sm:space-y-8">
      {/* Lime Next Step Banner */}
      {nextLabel && nextHref && (
        <div className="bg-[#c4ff2e] text-black px-4 sm:px-6 py-3.5 rounded-none flex flex-col sm:flex-row sm:items-center justify-between text-xs font-bold tracking-wider uppercase gap-2">
          <div className="flex flex-wrap items-center gap-3 sm:gap-4">
            <span className="text-[#3b4e09]">NEXT IN YOUR WORKSPACE</span>
            <Link
              href={nextHref}
              className="underline hover:opacity-75 transition-opacity"
            >
              {nextLabel}
            </Link>
            <span className="text-[#3b4e09] hidden sm:inline">·</span>
            <Link
              href="/projects"
              className="underline hover:opacity-75 transition-opacity"
            >
              All projects
            </Link>
          </div>
        </div>
      )}

      {/* Bottom Footer */}
      <footer className="border-t border-[#d0d5cc] pt-6 pb-12 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-[#6e736d] text-center sm:text-left">
        <span>Built by agents. Directed by you.</span>
        <span className="tracking-widest uppercase">
          ILLUSTRATIVE WORKSPACE / 2026
        </span>
      </footer>
    </div>
  );
}
