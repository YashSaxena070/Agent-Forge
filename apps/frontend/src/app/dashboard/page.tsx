'use client';

import Link from 'next/link';
import { WorkspaceNav, WorkspaceFooter } from '@/components/layout/workspace-nav';
import { useProject } from '@/lib/project-context';

export default function DashboardPage() {
  const { projects, activeProject, isRunning, toggleRunning, advanceStage, tokensPerSec } = useProject();

  const stages = [
    { num: '01', title: 'Plan', desc: 'Architecture mapped' },
    { num: '02', title: 'Build', desc: 'Code generated' },
    { num: '03', title: 'Verify', desc: 'Tests + security' },
    { num: '04', title: 'Ship', desc: 'Docker + CI/CD' },
  ];

  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      <WorkspaceNav />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-8 sm:pt-10 pb-16 space-y-10 sm:space-y-12">
        {/* Top Header Tags */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono gap-1">
          <span>AGENTFORGE / DASHBOARD</span>
          <span>PERSONAL WORKSPACE</span>
        </div>

        {/* Title */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2 sm:space-y-3">
            <h1 className="text-5xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
              DASHBOARD.
            </h1>
            <p className="text-sm sm:text-base text-[#4f544e] max-w-xl">
              Continuous engineering intelligence. Coordinate specialist agents to design, build, test, and ship.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <Link
              href="/projects/new"
              className="bg-[#c4ff2e] text-black px-5 py-2.5 text-xs font-bold uppercase tracking-wider hover:bg-[#b0eb20] transition-colors border border-black/15 shadow-sm"
            >
              + New Project
            </Link>
            <Link
              href="/workflows"
              className="bg-black text-white px-5 py-2.5 text-xs font-bold uppercase tracking-wider hover:bg-neutral-800 transition-colors"
            >
              Open Workflows →
            </Link>
          </div>
        </div>

        {/* 4 Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 pt-2">
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">ACTIVE PROJECTS</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">{String(projects.length).padStart(2, '0')}</div>
            <p className="text-xs text-[#6e736d]">Ready in workspace</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">AUTONOMOUS AGENTS</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">10</div>
            <p className="text-xs text-[#6e736d]">Specialist collective</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">CURRENT SPEED</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">
              {isRunning ? `${tokensPerSec}` : 'PAUSED'}
            </div>
            <p className="text-xs text-[#6e736d]">{isRunning ? 'Tokens per second' : 'Standby mode'}</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">PIPELINE HEALTH</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight text-black">99.8%</div>
            <p className="text-xs text-[#6e736d]">Zero critical flaws</p>
          </div>
        </div>

        {/* Black Active Session Card */}
        <div className="bg-[#0a0d0c] text-white p-5 sm:p-8 rounded-none border border-[#1f3447] space-y-6 shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] font-mono tracking-wider text-neutral-400 gap-2">
            <span className="text-[#c4ff2e] flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-[#c4ff2e] animate-ping' : 'bg-neutral-500'}`} />
              LIVE AUTONOMOUS BUILD / {activeProject.name.toUpperCase()}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleRunning}
                className="text-white hover:text-[#c4ff2e] underline font-mono text-xs mr-2"
              >
                {isRunning ? '[PAUSE]' : '[RESUME]'}
              </button>
              <button
                onClick={advanceStage}
                className="bg-[#c4ff2e] text-black px-2.5 py-1 text-[11px] font-bold uppercase font-mono"
              >
                Advance Stage →
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase leading-tight">
              &ldquo;{activeProject.name.toUpperCase()}&rdquo;
            </h2>
            <p className="text-xs sm:text-sm text-neutral-400">
              {activeProject.description}
            </p>
          </div>

          {/* 4 Interactive Stage Blocks */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
            {stages.map((st, i) => {
              const isCurrent = activeProject.activeStageIndex === i;
              const isDone = activeProject.stageProgress[i] >= 100;
              const progress = activeProject.stageProgress[i];

              return (
                <Link
                  key={st.num}
                  href="/workflows"
                  className={`p-4 border transition-all ${
                    isCurrent
                      ? 'bg-[#c4ff2e] text-black border-[#c4ff2e]'
                      : isDone
                      ? 'bg-[#181b19] text-white border-neutral-700 hover:border-neutral-500'
                      : 'bg-[#121413] text-neutral-400 border-neutral-800'
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                    <span className={isCurrent ? 'text-black/70' : 'text-neutral-400'}>{st.num}</span>
                    <span className={isCurrent ? 'text-black font-bold' : isDone ? 'text-[#0fa37a]' : 'text-neutral-500'}>
                      {isDone ? '✓' : isCurrent ? `${progress}%` : 'Queued'}
                    </span>
                  </div>
                  <p className={`text-sm tracking-tight ${isCurrent ? 'font-black' : 'font-bold'}`}>
                    {st.title} / {isDone ? 'Done' : isCurrent ? 'Working' : 'Queued'}
                  </p>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Section 01 / ACTIVE PROJECTS */}
        <section className="space-y-6 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">01 / ACTIVE REPOSITORIES</span>
            <Link href="/projects" className="text-xs font-mono text-[#6e736d] hover:text-black underline uppercase">
              View all ({projects.length})
            </Link>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {projects.map((proj) => (
              <div key={proj.id} className="py-4 grid grid-cols-12 items-center text-sm gap-2 sm:gap-4">
                <span className="col-span-12 sm:col-span-5 font-bold text-base text-[#0a0d0c]">{proj.name}</span>
                <span className="col-span-7 sm:col-span-4 text-xs text-[#4f544e] font-mono truncate">{proj.techStack.join(' · ')}</span>
                <span className="col-span-5 sm:col-span-3 text-right font-mono text-xs font-bold text-black">{proj.status}</span>
              </div>
            ))}
          </div>
        </section>

        <WorkspaceFooter nextLabel="Workflows" nextHref="/workflows" />
      </main>
    </div>
  );
}
