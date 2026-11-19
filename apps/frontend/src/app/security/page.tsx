'use client';

import { WorkspaceNav, WorkspaceFooter } from '@/components/layout/workspace-nav';

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      <WorkspaceNav />

      <main className="max-w-6xl mx-auto px-6 pt-10 pb-16 space-y-12">
        {/* Top Header Tags */}
        <div className="flex items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono">
          <span>AGENTFORGE / SECURITY</span>
          <span>PERSONAL WORKSPACE</span>
        </div>

        {/* Title */}
        <div className="space-y-3">
          <h1 className="text-6xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
            SECURITY.
          </h1>
          <p className="text-sm sm:text-base text-[#4f544e]">
            Trust is built in. Review the checks that stand between your code and production.
          </p>
        </div>

        {/* 4 Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-2">
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">CRITICAL ISSUES</span>
            <div className="text-5xl font-black tracking-tight">00</div>
            <p className="text-xs text-[#6e736d]">No critical findings</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">OPEN FINDINGS</span>
            <div className="text-5xl font-black tracking-tight">03</div>
            <p className="text-xs text-[#6e736d]">Awaiting review</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">CHECKS PASSED</span>
            <div className="text-5xl font-black tracking-tight">124</div>
            <p className="text-xs text-[#6e736d]">Latest audit</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">LAST SCAN</span>
            <div className="text-5xl font-black tracking-tight">8m</div>
            <p className="text-xs text-[#6e736d]">Commerce platform</p>
          </div>
        </div>

        {/* Black Security Card */}
        <div className="bg-[#0a0d0c] text-white p-6 sm:p-8 rounded-none border border-[#1f3447] space-y-4">
          <div className="text-[11px] font-mono tracking-wider text-[#c4ff2e]">
            LATEST AUDIT / COMPLETED
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase leading-tight">
              AUTONOMOUS. NOT UNCHECKED.
            </h2>
            <p className="text-xs sm:text-sm text-neutral-400">
              Your latest build cleared critical checks. Three recommendations need your team&apos;s attention before the next release.
            </p>
          </div>
        </div>

        {/* Section 01 / FINDINGS */}
        <section className="space-y-6 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">01 / FINDINGS</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">REVIEW BEFORE RELEASE.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {[
              { title: 'Dependency update', target: 'Commerce - Outdated payment SDK', tag: 'MEDIUM / OPEN' },
              { title: 'Rate limit policy', target: 'Analytics API - Authentication endpoint', tag: 'MEDIUM / OPEN' },
              { title: 'Security headers', target: 'Customer portal - Content security policy', tag: 'LOW / OPEN' },
            ].map((row, idx) => (
              <div key={idx} className="py-4 grid grid-cols-12 items-center text-sm gap-4">
                <span className="col-span-12 sm:col-span-5 font-bold text-base text-[#0a0d0c]">{row.title}</span>
                <span className="col-span-8 sm:col-span-5 text-xs text-[#4f544e]">{row.target}</span>
                <span className="col-span-4 sm:col-span-2 text-right font-mono text-xs text-black font-semibold">{row.tag}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Section 02 / COVERAGE */}
        <section className="space-y-6 pt-8">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">02 / COVERAGE</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">GUARDRAILS, BY DEFAULT.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {[
              { label: 'Code audit', desc: 'Application code checked for common vulnerabilities.', status: 'PASSED' },
              { label: 'Secret detection', desc: 'No exposed credentials in the latest changes.', status: 'PASSED' },
              { label: 'Dependency review', desc: 'Third-party packages checked against known risks.', status: 'REVIEW' },
              { label: 'Release gate', desc: 'Critical checks run before production deployment.', status: 'ENABLED' },
            ].map((row, idx) => (
              <div key={idx} className="py-4 grid grid-cols-12 items-center text-sm gap-4">
                <span className="col-span-12 sm:col-span-4 font-bold text-base text-[#0a0d0c]">{row.label}</span>
                <span className="col-span-8 sm:col-span-6 text-xs text-[#4f544e]">{row.desc}</span>
                <span className="col-span-4 sm:col-span-2 text-right font-mono text-xs text-[#6e736d]">{row.status}</span>
              </div>
            ))}
          </div>
        </section>

        <WorkspaceFooter nextLabel="Monitoring" nextHref="/monitoring" />
      </main>
    </div>
  );
}
