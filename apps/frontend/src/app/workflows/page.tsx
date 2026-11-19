'use client';

import { useState } from 'react';
import Link from 'next/link';
import { WorkspaceNav, WorkspaceFooter } from '@/components/layout/workspace-nav';
import { useProject } from '@/lib/project-context';

export default function WorkflowsPage() {
  const {
    activeProject,
    isRunning,
    toggleRunning,
    advanceStage,
    restartRun,
    logs,
    tokensPerSec,
  } = useProject();

  const [selectedStage, setSelectedStage] = useState<number>(activeProject.activeStageIndex);

  const stages = [
    { num: '01', title: 'Plan', desc: 'Architecture & requirements mapped', agent: 'Architect', model: 'llama-3.3-70b-versatile' },
    { num: '02', title: 'Build', desc: 'Code generation & persistence layers', agent: 'Developer', model: 'gpt-4o' },
    { num: '03', title: 'Verify', desc: 'Automated test suites & threat audits', agent: 'QA & Security', model: 'llama-3.3-70b-versatile' },
    { num: '04', title: 'Ship', desc: 'Docker images & CI/CD deployment', agent: 'DevOps', model: 'claude-3-5-haiku' },
  ];

  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      <WorkspaceNav />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-8 sm:pt-10 pb-16 space-y-10 sm:space-y-12">
        {/* Top Header Tags */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono gap-1">
          <span>AGENTFORGE / WORKFLOWS</span>
          <span>PERSONAL WORKSPACE</span>
        </div>

        {/* Title & Interactive Controls Bar */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2 sm:space-y-3">
            <h1 className="text-5xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
              WORKFLOWS.
            </h1>
            <p className="text-sm sm:text-base text-[#4f544e] max-w-xl">
              One brief. Every moving part. Follow your autonomous agent team from the first plan to the final release.
            </p>
          </div>

          {/* Controls Bar */}
          <div className="flex flex-wrap items-center gap-2.5 bg-[#dde1d8] p-2 border border-[#cbd1c5]">
            <button
              onClick={toggleRunning}
              className="px-3.5 py-2 text-xs font-bold uppercase tracking-wider bg-black text-white hover:bg-neutral-800 transition-colors"
            >
              {isRunning ? 'Pause Agents' : 'Resume Agents'}
            </button>
            <button
              onClick={advanceStage}
              className="px-3.5 py-2 text-xs font-bold uppercase tracking-wider bg-[#c4ff2e] text-black hover:bg-[#b0eb20] transition-colors border border-black/10"
            >
              Hand Off Now →
            </button>
            <button
              onClick={restartRun}
              className="px-3 py-2 text-xs font-mono uppercase text-[#4f544e] hover:text-black hover:bg-black/5 transition-colors"
            >
              Restart
            </button>
          </div>
        </div>

        {/* 4 Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 pt-2">
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">ACTIVE RUNS</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">04</div>
            <p className="text-xs text-[#6e736d]">Across 3 projects</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">COMPLETED TODAY</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">08</div>
            <p className="text-xs text-[#6e736d]">All checks passed</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">THROUGHPUT</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">
              {isRunning ? `${tokensPerSec} t/s` : '0 t/s'}
            </div>
            <p className="text-xs text-[#6e736d]">{isRunning ? 'Inference streaming' : 'Pipeline paused'}</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">TOKENS USED</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">
              {(activeProject.tokensUsed / 1000).toFixed(1)}k
            </div>
            <p className="text-xs text-[#6e736d]">This active project</p>
          </div>
        </div>

        {/* Black Active Build Card with Interactive Stage Switcher */}
        <div className="bg-[#0a0d0c] text-white p-5 sm:p-8 rounded-none border border-[#1f3447] space-y-6 shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] font-mono tracking-wider text-neutral-400 gap-2">
            <span className="text-[#c4ff2e] flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-[#c4ff2e] animate-ping' : 'bg-neutral-500'}`} />
              ACTIVE BUILD / {activeProject.name.toUpperCase()}
            </span>
            <span className="text-neutral-400 font-mono">
              TARGET: {activeProject.techStack.join(' · ')}
            </span>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase leading-tight">
              {activeProject.activeStageIndex === 0 && 'MAPPING ARCHITECTURE & RFC SPECS.'}
              {activeProject.activeStageIndex === 1 && 'BUILD THE CHECKOUT. SHIP THE EXPERIENCE.'}
              {activeProject.activeStageIndex === 2 && 'VERIFY QUALITY, JUNIT & OWASP CHECKS.'}
              {activeProject.activeStageIndex === 3 && 'CONTAINERIZE AND DEPLOY TO PRODUCTION.'}
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
                <div
                  key={st.num}
                  onClick={() => setSelectedStage(i)}
                  className={`p-4 border cursor-pointer transition-all ${
                    isCurrent
                      ? 'bg-[#c4ff2e] text-black border-[#c4ff2e] shadow-lg ring-2 ring-black'
                      : isDone
                      ? 'bg-[#181b19] text-white border-neutral-700 hover:border-neutral-500'
                      : 'bg-[#121413] text-neutral-400 border-neutral-800'
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono mb-1.5">
                    <span className={isCurrent ? 'text-black/70' : 'text-neutral-400'}>{st.num}</span>
                    <span className={isCurrent ? 'text-black font-bold' : isDone ? 'text-[#0fa37a]' : 'text-neutral-500'}>
                      {isDone ? '✓ 100%' : isCurrent ? `${progress}%` : 'Queued'}
                    </span>
                  </div>

                  <p className={`text-sm tracking-tight ${isCurrent ? 'font-black' : 'font-bold'}`}>
                    {st.title} / {isDone ? 'Complete' : isCurrent ? 'In progress' : 'Queued'}
                  </p>

                  {/* Micro Progress Bar */}
                  <div className="w-full h-1 bg-black/20 mt-3 overflow-hidden">
                    <div
                      style={{ width: `${progress}%` }}
                      className={`h-full transition-all duration-300 ${
                        isCurrent ? 'bg-black' : isDone ? 'bg-[#0fa37a]' : 'bg-neutral-700'
                      }`}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Inspected Stage Details Callout */}
          <div className="p-4 bg-[#141715] border border-neutral-800 flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-3">
            <div>
              <span className="text-neutral-400 uppercase font-mono mr-2">STAGE {stages[selectedStage].num}:</span>
              <span className="font-bold text-white">{stages[selectedStage].title}</span>
              <span className="text-neutral-400 hidden sm:inline"> — {stages[selectedStage].desc}</span>
            </div>
            <div className="flex items-center gap-4 text-neutral-400 font-mono text-[11px]">
              <span>AGENT: <strong className="text-[#c4ff2e]">{stages[selectedStage].agent}</strong></span>
              <span>MODEL: <strong className="text-white">{stages[selectedStage].model}</strong></span>
            </div>
          </div>
        </div>

        {/* Section 01 / RUN REGISTER & LIVE HANDOFF LOG */}
        <section className="space-y-6 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">01 / RUN REGISTER & LOG</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">THE WORK, IN MOTION.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {logs.map((log) => (
              <div key={log.id} className="py-4 grid grid-cols-12 items-center text-sm gap-2 sm:gap-4">
                <span className="col-span-12 sm:col-span-4 font-bold text-base text-[#0a0d0c] flex items-center gap-2">
                  <span className="text-xs font-mono text-[#6e736d]">{log.timestamp}</span>
                  <span>[{log.agent}]</span>
                </span>
                <span className="col-span-8 sm:col-span-6 text-xs text-[#4f544e]">
                  {log.message}
                </span>
                <span className="col-span-4 sm:col-span-2 text-right font-mono text-xs text-black font-semibold">
                  {log.stage.toUpperCase()} / SYNCED
                </span>
              </div>
            ))}
          </div>
        </section>

        <WorkspaceFooter nextLabel="Agents" nextHref="/agents" />
      </main>
    </div>
  );
}
