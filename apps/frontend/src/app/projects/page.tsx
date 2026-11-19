'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { WorkspaceNav, WorkspaceFooter } from '@/components/layout/workspace-nav';
import { useProject } from '@/lib/project-context';

export default function ProjectsPage() {
  const router = useRouter();
  const { projects, activeProjectId, setActiveProjectId, showToast } = useProject();

  const handleSelectProject = (id: string, name: string) => {
    setActiveProjectId(id);
    showToast(`Switched active project to "${name}"`);
    router.push('/workflows');
  };

  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      <WorkspaceNav />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-8 sm:pt-10 pb-16 space-y-10 sm:space-y-12">
        {/* Top Header Tags */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono gap-1">
          <span>AGENTFORGE / PROJECTS</span>
          <span>PERSONAL WORKSPACE</span>
        </div>

        {/* Title */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
          <div className="space-y-2 sm:space-y-3">
            <h1 className="text-5xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
              PROJECTS.
            </h1>
            <p className="text-sm sm:text-base text-[#4f544e]">
              Manage autonomous code repositories, build pipelines, and generated applications.
            </p>
          </div>
          <Link
            href="/projects/new"
            className="inline-block bg-[#c4ff2e] text-black px-6 py-3 font-bold text-sm tracking-tight uppercase hover:bg-[#b0eb20] transition-colors border border-black/15 shadow-sm self-start sm:self-auto shrink-0"
          >
            + New Project
          </Link>
        </div>

        {/* 4 Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 pt-2">
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">TOTAL PROJECTS</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">{String(projects.length).padStart(2, '0')}</div>
            <p className="text-xs text-[#6e736d]">In your personal workspace</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">ACTIVE BUILDS</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">
              {String(projects.filter((p) => p.status === 'BUILD IN PROGRESS').length).padStart(2, '0')}
            </div>
            <p className="text-xs text-[#6e736d]">Currently compiling</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">REPOSITORIES SYNCED</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">{String(projects.length).padStart(2, '0')}</div>
            <p className="text-xs text-[#6e736d]">Git branch: main</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] sm:text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">CONTAINERS BUILT</span>
            <div className="text-4xl sm:text-5xl font-black tracking-tight">18</div>
            <p className="text-xs text-[#6e736d]">Ready in GHCR registry</p>
          </div>
        </div>

        {/* Section 01 / DIRECTORY */}
        <section className="space-y-6 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">01 / REPOSITORY DIRECTORY</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">THE CODEBASES.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {projects.map((proj) => {
              const isActive = proj.id === activeProjectId;
              return (
                <div key={proj.id} className="py-6 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <h3 className="text-xl font-bold tracking-tight text-[#0a0d0c]">{proj.name}</h3>
                      {isActive && (
                        <span className="bg-[#c4ff2e] text-black text-[10px] font-mono uppercase px-2 py-0.5 font-bold">
                          ACTIVE WORKSPACE
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-xs font-mono">
                      <span className="text-[#6e736d] hidden sm:inline">Updated {proj.lastActivity}</span>
                      <span className="font-bold text-black border border-black/20 px-2.5 py-0.5">{proj.status}</span>
                      <button
                        onClick={() => handleSelectProject(proj.id, proj.name)}
                        className="bg-black text-white hover:bg-neutral-800 px-3 py-1 font-bold text-xs uppercase transition-colors"
                      >
                        {isActive ? 'View Workflow →' : 'Switch & Open'}
                      </button>
                    </div>
                  </div>

                  <p className="text-sm text-[#4f544e] max-w-2xl">{proj.description}</p>

                  <div className="flex flex-wrap items-center gap-2 pt-2">
                    {proj.techStack.map((tech) => (
                      <span key={tech} className="text-[11px] font-mono bg-[#dde1d8] text-black px-2.5 py-1 border border-[#cbd1c5]">
                        {tech}
                      </span>
                    ))}
                    <span className="text-[11px] font-mono text-[#6e736d] ml-auto">
                      Stage {proj.activeStageIndex + 1}/4 ({proj.stageProgress[proj.activeStageIndex]}%)
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <WorkspaceFooter nextLabel="Workflows" nextHref="/workflows" />
      </main>
    </div>
  );
}
