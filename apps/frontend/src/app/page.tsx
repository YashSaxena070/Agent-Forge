'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useProject } from '@/lib/project-context';

export default function HomePage() {
  const router = useRouter();
  const { createNewProject } = useProject();
  const [prompt, setPrompt] = useState('Build a subscription platform.');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLaunch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    setIsSubmitting(true);
    const newId = createNewProject(
      prompt.length > 30 ? prompt.slice(0, 30) + '...' : prompt,
      prompt,
      'fullstack'
    );
    setTimeout(() => {
      router.push('/workflows');
    }, 400);
  };
  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      {/* Top Header */}
      <header className="border-b border-[#d0d5cc] bg-[#eaede6]/90 sticky top-0 z-50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 text-xl font-bold tracking-tight text-[#0a0d0c]">
            <svg className="w-5 h-5 text-[#0a0d0c]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="4" />
              <circle cx="12" cy="12" r="3" />
              <path d="M12 3v3M12 18v3M3 12h3M18 12h3" />
            </svg>
            <span>AgentForge</span>
          </Link>

          <div className="flex items-center gap-8 text-xs font-medium">
            <Link href="/workflows" className="text-[#4f544e] hover:text-black transition-colors">
              Workflow
            </Link>
            <Link href="/agents" className="text-[#4f544e] hover:text-black transition-colors">
              Agents
            </Link>
            <Link href="/security" className="text-[#4f544e] hover:text-black transition-colors">
              Security
            </Link>
            <Link
              href="/dashboard"
              className="bg-[#c4ff2e] text-black px-4 py-2 font-semibold text-xs tracking-tight rounded-none hover:bg-[#b0eb20] transition-colors border border-black/10"
            >
              Explore platform
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 pt-12 pb-24 space-y-24">
        {/* Hero Section */}
        <section className="space-y-8">
          <div className="flex items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono">
            <span>AGENTFORGE / AUTONOMOUS DEVELOPMENT</span>
            <span>IDEA IN. SOFTWARE OUT.</span>
          </div>

          <h1 className="text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-black tracking-tighter leading-[0.88] text-[#0a0d0c] uppercase">
            LESS TALK.<br />MORE SHIP.
          </h1>

          <div className="grid md:grid-cols-2 gap-8 items-end pt-4">
            <p className="text-base sm:text-lg text-[#4f544e] max-w-md leading-relaxed">
              Your idea doesn&apos;t need another chatbot. It needs an engineering team. AgentForge coordinates AI agents to build, test, secure, and deploy real software.
            </p>
            <div className="md:text-right">
              <Link
                href="/workflows"
                className="inline-block bg-[#c4ff2e] text-black px-6 py-3 font-bold text-sm tracking-tight rounded-none hover:bg-[#b0eb20] transition-colors border border-black/15 shadow-sm"
              >
                Explore the workflow
              </Link>
            </div>
          </div>

          <div className="text-xs text-[#6e736d] font-mono tracking-wider pt-6">
            [ 01 — THE NEXT WAY TO BUILD ]
          </div>

          {/* Interactive Illustrative Build Session Card */}
          <div className="bg-[#0a0d0c] text-white p-6 sm:p-8 rounded-none border border-[#1f3447] shadow-xl space-y-8">
            <div className="flex items-center justify-between text-[11px] font-mono tracking-wider text-neutral-400">
              <span>FROM A SINGLE PROMPT</span>
              <span>ILLUSTRATIVE BUILD SESSION / 001</span>
            </div>

            <form onSubmit={handleLaunch} className="py-2 space-y-4">
              <div className="flex flex-col sm:flex-row items-stretch gap-3">
                <div className="relative flex-1">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500 font-mono text-sm sm:text-base">&ldquo;</span>
                  <input
                    type="text"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Enter what you want to build (e.g. Build an AI-powered CRM)..."
                    className="w-full bg-[#141816] text-white pl-8 pr-4 py-3.5 text-base sm:text-xl font-bold tracking-tight border border-neutral-700 focus:border-[#c4ff2e] focus:outline-none placeholder:text-neutral-500 font-sans"
                  />
                  <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-neutral-500 font-mono text-sm sm:text-base">&rdquo;</span>
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-[#c4ff2e] hover:bg-[#b0eb20] text-black font-black text-xs sm:text-sm px-6 py-3.5 tracking-tight uppercase whitespace-nowrap transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <span className="w-2.5 h-2.5 rounded-full border-2 border-black border-t-transparent animate-spin" />
                      <span>Assembling Team...</span>
                    </>
                  ) : (
                    <>
                      <span>Launch Autonomous Build</span>
                      <span>→</span>
                    </>
                  )}
                </button>
              </div>

              {/* Quick preset ambitions */}
              <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
                <span className="text-neutral-400">PROMPT PRESETS:</span>
                {[
                  'Build a subscription platform.',
                  'Create real-time IoT telemetry API with ClickHouse.',
                  'Develop multi-tenant SaaS billing with Stripe webhook.',
                ].map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setPrompt(preset)}
                    className="bg-[#181d1a] hover:bg-[#222a25] text-neutral-300 hover:text-[#c4ff2e] px-2.5 py-1 border border-neutral-800 transition-colors cursor-pointer"
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </form>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-4 border-t border-neutral-800">
              <div className="space-y-1.5">
                <span className="text-[11px] font-mono text-[#c4ff2e]">01</span>
                <h3 className="text-lg font-black tracking-tight uppercase">PLAN</h3>
                <p className="text-xs text-neutral-400 font-mono">Architecture mapped</p>
              </div>
              <div className="space-y-1.5">
                <span className="text-[11px] font-mono text-[#c4ff2e]">02</span>
                <h3 className="text-lg font-black tracking-tight uppercase">BUILD</h3>
                <p className="text-xs text-neutral-400 font-mono">Code generated</p>
              </div>
              <div className="space-y-1.5">
                <span className="text-[11px] font-mono text-[#c4ff2e]">03</span>
                <h3 className="text-lg font-black tracking-tight uppercase">VERIFY</h3>
                <p className="text-xs text-neutral-400 font-mono">Tests + security</p>
              </div>
              <div className="space-y-1.5">
                <span className="text-[11px] font-mono text-[#c4ff2e]">04</span>
                <h3 className="text-lg font-black tracking-tight uppercase">SHIP</h3>
                <p className="text-xs text-neutral-400 font-mono">Docker + CI/CD</p>
              </div>
            </div>

            <div className="bg-[#c4ff2e] text-black px-4 py-2.5 text-xs font-bold font-mono tracking-wider uppercase text-center">
              SIX SPECIALISTS. SHARED CONTEXT. ONE OUTCOME.
            </div>
          </div>
        </section>

        {/* Section 01 / THE PROCESS */}
        <section className="pt-8 space-y-12 border-t border-[#d0d5cc]">
          <div className="flex items-start justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">01 / THE PROCESS</span>
            <h2 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tighter uppercase text-right leading-none max-w-2xl">
              ONE BRIEF. THE ENTIRE BUILD.
            </h2>
          </div>

          <div className="space-y-6 pt-4">
            <div className="grid md:grid-cols-3 gap-6 py-5 border-b border-[#d0d5cc]">
              <span className="text-xs font-mono text-[#6e736d]">01</span>
              <h3 className="text-xl font-bold tracking-tight">Describe the ambition.</h3>
              <p className="text-sm text-[#4f544e] leading-relaxed">
                Tell AgentForge what you want to build. Define the goals, your preferred stack, and what success looks like.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6 py-5 border-b border-[#d0d5cc]">
              <span className="text-xs font-mono text-[#6e736d]">02</span>
              <h3 className="text-xl font-bold tracking-tight">Put the team to work.</h3>
              <p className="text-sm text-[#4f544e] leading-relaxed">
                Specialist agents break down the brief, share context, and coordinate code, schemas, tests, and infrastructure.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6 py-5 border-b border-[#d0d5cc]">
              <span className="text-xs font-mono text-[#6e736d]">03</span>
              <h3 className="text-xl font-bold tracking-tight">Review it. Then release it.</h3>
              <p className="text-sm text-[#4f544e] leading-relaxed">
                Inspect the work, follow the decisions, and move your app through a repeatable deployment pipeline.
              </p>
            </div>
          </div>
        </section>

        {/* Section 02 / THE COLLECTIVE */}
        <section className="pt-8 space-y-12 border-t border-[#d0d5cc]">
          <div className="flex items-start justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">02 / THE COLLECTIVE</span>
            <h2 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tighter uppercase text-right leading-none max-w-2xl">
              NOT ONE AI. A WHOLE TEAM.
            </h2>
          </div>

          <div className="space-y-4 pt-4">
            {[
              { num: '01', title: 'Architecture', desc: 'From product intent to a technical blueprint.' },
              { num: '02', title: 'Development', desc: 'Application logic, interfaces, and APIs.' },
              { num: '03', title: 'Database', desc: 'Schemas, relationships, and migrations.' },
              { num: '04', title: 'Testing', desc: 'Automated coverage for the paths that matter.' },
              { num: '05', title: 'Security', desc: 'Code audits before production.' },
              { num: '06', title: 'Deployment', desc: 'Docker containers and CI/CD workflows.' },
            ].map((item) => (
              <div key={item.num} className="grid grid-cols-12 items-baseline py-4 border-b border-[#d0d5cc]">
                <span className="col-span-1 text-xs font-mono text-[#6e736d]">{item.num}</span>
                <span className="col-span-6 sm:col-span-5 text-2xl sm:text-4xl font-black tracking-tight text-[#0a0d0c]">
                  {item.title}
                </span>
                <span className="col-span-5 sm:col-span-6 text-sm text-[#4f544e] text-right sm:text-left">
                  {item.desc}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Section 03 / YOUR CALL */}
        <section className="pt-8 space-y-12 border-t border-[#d0d5cc]">
          <div className="flex items-start justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">03 / YOUR CALL</span>
            <h2 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tighter uppercase text-right leading-none max-w-2xl">
              AUTONOMOUS. NOT UNACCOUNTABLE.
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8 pt-4">
            <div className="space-y-3">
              <h3 className="text-xl font-bold tracking-tight">See the work.</h3>
              <p className="text-sm text-[#4f544e] leading-relaxed">
                Follow agent activity, task progress, token usage, and estimated cost in one workspace.
              </p>
            </div>
            <div className="space-y-3">
              <h3 className="text-xl font-bold tracking-tight">Trust the process.</h3>
              <p className="text-sm text-[#4f544e] leading-relaxed">
                Testing and security checks are part of the build, not tasks left until the end.
              </p>
            </div>
            <div className="space-y-3">
              <h3 className="text-xl font-bold tracking-tight">Own the outcome.</h3>
              <p className="text-sm text-[#4f544e] leading-relaxed">
                Real source code. Real containers. A deployment workflow you can inspect.
              </p>
            </div>
          </div>
        </section>

        {/* Full-Width Acid Lime CTA Banner */}
        <section className="bg-[#c4ff2e] text-black p-8 sm:p-12 md:p-16 space-y-8 rounded-none">
          <span className="text-xs font-mono tracking-wider uppercase text-black/70">YOUR NEXT IDEA</span>
          <h2 className="text-5xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
            GIVE IT A TEAM.
          </h2>
          <div>
            <Link
              href="/agents"
              className="inline-block border border-black bg-transparent hover:bg-black hover:text-[#c4ff2e] text-black px-6 py-3 font-semibold text-sm tracking-tight transition-colors"
            >
              Meet your AI team
            </Link>
          </div>
        </section>

        {/* Public Footer */}
        <footer className="pt-8 border-t border-[#d0d5cc] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#6e736d]">
          <div className="flex items-center gap-2 font-bold text-black text-sm">
            <svg className="w-4 h-4 text-black" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="4" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <span>AgentForge</span>
          </div>
          <span>Built by agents. Directed by you. © 2026 AgentForge</span>
        </footer>
      </main>
    </div>
  );
}
