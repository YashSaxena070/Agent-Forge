'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { WorkspaceNav, WorkspaceFooter } from '@/components/layout/workspace-nav';
import { useProject } from '@/lib/project-context';

export default function NewProjectPage() {
  const router = useRouter();
  const { createNewProject } = useProject();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [framework, setFramework] = useState('fullstack');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      createNewProject(name, description, framework);
      router.push('/workflows');
    } catch {
      router.push('/workflows');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      <WorkspaceNav />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-8 sm:pt-10 pb-16 space-y-10 sm:space-y-12">
        {/* Top Header Tags */}
        <div className="flex items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono">
          <span>AGENTFORGE / NEW PROJECT</span>
          <Link href="/projects" className="underline hover:text-black">
            CANCEL & RETURN
          </Link>
        </div>

        {/* Title */}
        <div className="space-y-2 sm:space-y-3">
          <h1 className="text-5xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
            NEW PROJECT.
          </h1>
          <p className="text-sm sm:text-base text-[#4f544e]">
            One brief. The entire build. Define your software requirements and let the specialist agent team scaffold, test, and deploy.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 sm:space-y-8 pt-2 sm:pt-4">
          <div className="space-y-2.5">
            <label htmlFor="p-name" className="text-xs font-mono uppercase tracking-wider text-[#6e736d] block">
              01 / PROJECT NAME <span className="text-black">*</span>
            </label>
            <input
              id="p-name"
              type="text"
              required
              placeholder="e.g. Distributed Subscription Platform"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-[#dde1d8] border border-[#cbd1c5] p-3 sm:p-4 text-base font-medium text-[#0a0d0c] outline-none focus:border-black rounded-none transition-colors"
            />
          </div>

          <div className="space-y-2.5">
            <label htmlFor="p-desc" className="text-xs font-mono uppercase tracking-wider text-[#6e736d] block">
              02 / REQUIREMENTS BRIEF & FUNCTIONAL SCOPE <span className="text-black">*</span>
            </label>
            <textarea
              id="p-desc"
              required
              rows={4}
              placeholder="Describe the software you need. Specify users, data models, APIs, authentication, external integrations, and business logic..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-[#dde1d8] border border-[#cbd1c5] p-3 sm:p-4 text-sm font-medium text-[#0a0d0c] outline-none focus:border-black rounded-none resize-y transition-colors"
            />
          </div>

          <div className="space-y-2.5">
            <label className="text-xs font-mono uppercase tracking-wider text-[#6e736d] block">
              03 / TARGET ARCHITECTURE STACK
            </label>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { id: 'fullstack', title: 'Fullstack Platform', desc: 'Spring Boot 3 + Next.js 14 + PostgreSQL' },
                { id: 'microservice', title: 'AI Microservice', desc: 'FastAPI + LangGraph + Qdrant Vector DB' },
                { id: 'backend', title: 'Enterprise Backend', desc: 'Java 21 + REST + OAuth2 + Redis' },
              ].map((stack) => (
                <div
                  key={stack.id}
                  onClick={() => setFramework(stack.id)}
                  className={`cursor-pointer p-4 sm:p-5 border transition-all ${
                    framework === stack.id
                      ? 'bg-[#0a0d0c] text-white border-[#0a0d0c] ring-2 ring-black'
                      : 'bg-[#dde1d8] text-black border-[#cbd1c5] hover:border-black'
                  }`}
                >
                  <p className="font-bold text-sm tracking-tight uppercase mb-1">{stack.title}</p>
                  <p className={`text-xs ${framework === stack.id ? 'text-neutral-400' : 'text-[#6e736d]'}`}>
                    {stack.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 sm:pt-6 border-t border-[#d0d5cc] flex flex-col sm:flex-row items-center justify-between gap-4">
            <Link href="/projects" className="text-xs font-mono text-[#6e736d] hover:text-black">
              ← Return to all projects
            </Link>

            <button
              type="submit"
              disabled={loading}
              className="bg-[#c4ff2e] text-black px-6 sm:px-8 py-3.5 sm:py-4 font-bold text-xs sm:text-sm uppercase tracking-wider hover:bg-[#b0eb20] transition-colors border border-black/15 shadow-sm w-full sm:w-auto text-center"
            >
              {loading ? 'Assembling Agent Team...' : 'Assemble Team & Start Build'}
            </button>
          </div>
        </form>

        <WorkspaceFooter nextLabel="Workflows" nextHref="/workflows" />
      </main>
    </div>
  );
}
