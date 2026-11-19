'use client';

import { WorkspaceNav, WorkspaceFooter } from '@/components/layout/workspace-nav';

export default function AgentsPage() {
  const agents = [
    {
      title: 'Architect',
      desc: 'Maps your brief into a buildable technical plan.',
      status: 'ARCHITECTURE MAPPED',
      icon: (
        <svg className="w-5 h-5 text-black" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
        </svg>
      ),
    },
    {
      title: 'Developer',
      desc: 'Builds interfaces, business logic, and APIs.',
      status: 'IMPLEMENTING CHECKOUT',
      icon: (
        <svg className="w-5 h-5 text-black" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="16 18 22 12 16 6" />
          <polyline points="8 6 2 12 8 18" />
        </svg>
      ),
    },
    {
      title: 'Database',
      desc: 'Designs schemas, relationships, and migrations.',
      status: 'SCHEMA UP TO DATE',
      icon: (
        <svg className="w-5 h-5 text-black" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
        </svg>
      ),
    },
    {
      title: 'QA engineer',
      desc: 'Generates and runs automated tests.',
      status: 'PREPARING 24 CHECKS',
      icon: (
        <svg className="w-5 h-5 text-black" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      ),
    },
    {
      title: 'Security',
      desc: 'Audits code and dependencies before release.',
      status: 'REVIEW PENDING',
      icon: (
        <svg className="w-5 h-5 text-black" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="4 17 10 11 4 5" />
          <line x1="12" y1="19" x2="20" y2="19" />
        </svg>
      ),
    },
    {
      title: 'DevOps',
      desc: 'Packages containers and prepares CI/CD.',
      status: 'PIPELINE READY',
      icon: (
        <svg className="w-5 h-5 text-black" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
          <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" />
          <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
          <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
        </svg>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      <WorkspaceNav />

      <main className="max-w-6xl mx-auto px-6 pt-10 pb-16 space-y-12">
        {/* Top Header Tags */}
        <div className="flex items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono">
          <span>AGENTFORGE / AGENTS</span>
          <span>PERSONAL WORKSPACE</span>
        </div>

        {/* Title */}
        <div className="space-y-3">
          <h1 className="text-6xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
            AGENTS.
          </h1>
          <p className="text-sm sm:text-base text-[#4f544e]">
            Specialist minds. Shared context. Meet the engineering team behind your next release.
          </p>
        </div>

        {/* 4 Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-2">
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">SPECIALISTS</span>
            <div className="text-5xl font-black tracking-tight">06</div>
            <p className="text-xs text-[#6e736d]">One coordinated team</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">WORKING NOW</span>
            <div className="text-5xl font-black tracking-tight">04</div>
            <p className="text-xs text-[#6e736d]">Across active workflows</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">TASKS RESOLVED</span>
            <div className="text-5xl font-black tracking-tight border-b-2 border-black pb-1 inline-block">128</div>
            <p className="text-xs text-[#6e736d]">This workspace</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">CONTEXT</span>
            <div className="text-5xl font-black tracking-tight">01</div>
            <p className="text-xs text-[#6e736d]">Shared project memory</p>
          </div>
        </div>

        {/* Section 01 / THE COLLECTIVE */}
        <section className="space-y-6 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">01 / THE COLLECTIVE</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">SIX ROLES. ONE OUTCOME.</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border-t border-l border-[#d0d5cc]">
            {agents.map((agent, idx) => (
              <div key={idx} className="p-6 border-r border-b border-[#d0d5cc] space-y-8 flex flex-col justify-between min-h-[220px]">
                <div className="space-y-3">
                  <div className="w-8 h-8 flex items-center justify-start text-black">
                    {agent.icon}
                  </div>
                  <h3 className="text-xl font-bold tracking-tight text-[#0a0d0c]">{agent.title}</h3>
                  <p className="text-xs text-[#4f544e] leading-relaxed">{agent.desc}</p>
                </div>
                <div className="text-[10px] font-mono tracking-wider text-[#6e736d] uppercase pt-4">
                  {agent.status}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 02 / SHARED CONTEXT */}
        <section className="space-y-6 pt-8">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">02 / SHARED CONTEXT</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">LESS HANDOFF. MORE ALIGNMENT.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {[
              { label: 'Project brief', desc: 'The same intent guides every specialist.', tag: 'SOURCE OF TRUTH' },
              { label: 'Build artifacts', desc: 'Code, schemas, and tests stay connected.', tag: 'SHARED OUTPUT' },
              { label: 'Decision history', desc: 'Every handoff carries the reasoning forward.', tag: 'TRACEABLE' },
            ].map((row, idx) => (
              <div key={idx} className="py-4 grid grid-cols-12 items-center text-sm gap-4">
                <span className="col-span-12 sm:col-span-4 font-bold text-base text-[#0a0d0c]">{row.label}</span>
                <span className="col-span-8 sm:col-span-5 text-xs text-[#4f544e]">{row.desc}</span>
                <span className="col-span-4 sm:col-span-3 text-right font-mono text-xs text-[#6e736d]">{row.tag}</span>
              </div>
            ))}
          </div>
        </section>

        <WorkspaceFooter nextLabel="Deployments" nextHref="/deployments" />
      </main>
    </div>
  );
}
