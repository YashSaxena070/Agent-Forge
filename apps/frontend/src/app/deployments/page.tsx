'use client';

import { WorkspaceNav, WorkspaceFooter } from '@/components/layout/workspace-nav';

export default function DeploymentsPage() {
  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      <WorkspaceNav />

      <main className="max-w-6xl mx-auto px-6 pt-10 pb-16 space-y-12">
        {/* Top Header Tags */}
        <div className="flex items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono">
          <span>AGENTFORGE / DEPLOYMENTS</span>
          <span>PERSONAL WORKSPACE</span>
        </div>

        {/* Title */}
        <div className="space-y-3">
          <h1 className="text-6xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
            DEPLOYMENTS.
          </h1>
          <p className="text-sm sm:text-base text-[#4f544e]">
            From a passing build to a running product. Every release, every environment, in one place.
          </p>
        </div>

        {/* 4 Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-2">
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">ENVIRONMENTS</span>
            <div className="text-5xl font-black tracking-tight">03</div>
            <p className="text-xs text-[#6e736d]">Production + staging</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">LATEST RELEASE</span>
            <div className="text-5xl font-black tracking-tight">v1.8.2</div>
            <p className="text-xs text-[#6e736d]">Commerce platform</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">BUILD DURATION</span>
            <div className="text-5xl font-black tracking-tight">2m 34s</div>
            <p className="text-xs text-[#6e736d]">Latest successful build</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">RELEASE HEALTH</span>
            <div className="text-5xl font-black tracking-tight">PASS</div>
            <p className="text-xs text-[#6e736d]">All checks clear</p>
          </div>
        </div>

        {/* Black Active Build Card */}
        <div className="bg-[#0a0d0c] text-white p-6 sm:p-8 rounded-none border border-[#1f3447] space-y-6">
          <div className="text-[11px] font-mono tracking-wider text-[#c4ff2e]">
            PRODUCTION / COMMERCE PLATFORM
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase leading-tight">
              READY FOR THE REAL WORLD.
            </h2>
            <p className="text-xs sm:text-sm text-neutral-400">
              Release v1.8.2 - main - 8c42df - Deployed 24 minutes ago
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
            <div className="bg-[#181b19] p-4 border border-neutral-800">
              <span className="text-[10px] font-mono text-neutral-400 block mb-1">01</span>
              <p className="text-sm font-bold">Source / Synced</p>
            </div>
            <div className="bg-[#c4ff2e] text-black p-4 border border-[#c4ff2e]">
              <span className="text-[10px] font-mono text-black/70 block mb-1">02</span>
              <p className="text-sm font-black">Build / Passed</p>
            </div>
            <div className="bg-[#181b19] p-4 border border-neutral-800">
              <span className="text-[10px] font-mono text-neutral-400 block mb-1">03</span>
              <p className="text-sm font-bold">Checks / Passed</p>
            </div>
            <div className="bg-[#181b19] p-4 border border-neutral-800">
              <span className="text-[10px] font-mono text-neutral-400 block mb-1">04</span>
              <p className="text-sm font-bold">Release / Live</p>
            </div>
          </div>
        </div>

        {/* Section 01 / RELEASE HISTORY */}
        <section className="space-y-6 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">01 / RELEASE HISTORY</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">EVERY RELEASE. ACCOUNTED FOR.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {[
              { rel: 'v1.8.2 / Commerce', env: 'Production - main - 24 minutes ago', status: 'SUCCESS', statusClass: 'text-black font-semibold' },
              { rel: 'v1.8.1 / Commerce', env: 'Staging - main - 2 hours ago', status: 'SUCCESS', statusClass: 'text-black font-semibold' },
              { rel: 'v0.9.4 / Taskflow', env: 'Production - main - 5 hours ago', status: 'SUCCESS', statusClass: 'text-black font-semibold' },
              { rel: 'v0.4.0 / Analytics API', env: 'Staging - feature/auth - Yesterday', status: 'BUILD FAILED', statusClass: 'text-[#6e736d]' },
            ].map((row, idx) => (
              <div key={idx} className="py-4 grid grid-cols-12 items-center text-sm gap-4">
                <span className="col-span-12 sm:col-span-5 font-bold text-base text-[#0a0d0c]">{row.rel}</span>
                <span className="col-span-8 sm:col-span-5 text-xs text-[#4f544e]">{row.env}</span>
                <span className={`col-span-4 sm:col-span-2 text-right font-mono text-xs ${row.statusClass}`}>{row.status}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Real Containers Grey Callout Box */}
        <div className="bg-[#dde1d8] p-6 sm:p-8 space-y-2 border border-[#cbd1c5]">
          <h3 className="font-bold text-base tracking-tight text-[#0a0d0c] uppercase">
            REAL CONTAINERS. YOUR INFRASTRUCTURE.
          </h3>
          <p className="text-xs sm:text-sm text-[#4f544e]">
            Docker images and CI/CD configurations remain part of your project. Review the pipeline before approving your next release.
          </p>
        </div>

        <WorkspaceFooter nextLabel="Security" nextHref="/security" />
      </main>
    </div>
  );
}
