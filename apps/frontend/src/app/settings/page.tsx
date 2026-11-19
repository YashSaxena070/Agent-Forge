'use client';

import { WorkspaceNav, WorkspaceFooter } from '@/components/layout/workspace-nav';

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      <WorkspaceNav />

      <main className="max-w-6xl mx-auto px-6 pt-10 pb-16 space-y-12">
        {/* Top Header Tags */}
        <div className="flex items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono">
          <span>AGENTFORGE / SETTINGS</span>
          <span>PERSONAL WORKSPACE</span>
        </div>

        {/* Title */}
        <div className="space-y-3">
          <h1 className="text-6xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
            SETTINGS.
          </h1>
          <p className="text-sm sm:text-base text-[#4f544e]">
            Your workspace. Your rules. Review the preferences that shape how your agents work.
          </p>
        </div>

        {/* Grey Callout Box */}
        <div className="bg-[#dde1d8] p-6 sm:p-8 space-y-2 border border-[#cbd1c5]">
          <span className="text-[10px] font-mono tracking-wider text-[#6e736d] uppercase block">
            WORKSPACE CONFIGURATION / DESIGN PREVIEW
          </span>
          <h2 className="text-lg font-bold tracking-tight text-[#0a0d0c]">
            Your defaults, made explicit.
          </h2>
          <p className="text-xs sm:text-sm text-[#4f544e]">
            This screen illustrates workspace preferences. Account changes, billing, and integrations are not connected in this prototype.
          </p>
        </div>

        {/* Section 01 / GENERAL */}
        <section className="space-y-6 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">01 / GENERAL</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">THE WORKSPACE.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {[
              { field: 'Workspace name', desc: 'Personal workspace', val: 'PERSONAL' },
              { field: 'Workspace owner', desc: 'Yash Saxena', val: 'OWNER' },
              { field: 'Default environment', desc: 'Require a staging build before production.', val: 'STAGING' },
              { field: 'Region', desc: 'Choose infrastructure close to your users.', val: 'ASIA PACIFIC' },
            ].map((row, idx) => (
              <div key={idx} className="py-4 grid grid-cols-12 items-center text-sm gap-4">
                <span className="col-span-12 sm:col-span-4 font-bold text-base text-[#0a0d0c]">{row.field}</span>
                <span className="col-span-8 sm:col-span-5 text-xs text-[#4f544e]">{row.desc}</span>
                <span className="col-span-4 sm:col-span-3 text-right font-mono text-xs text-[#6e736d]">{row.val}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Section 02 / AGENT POLICIES */}
        <section className="space-y-6 pt-8">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">02 / AGENT POLICIES</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">AUTONOMY, WITH BOUNDARIES.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {[
              { policy: 'Production approval', desc: 'Review releases before agents deploy.', val: 'REQUIRED' },
              { policy: 'Security checks', desc: 'Block releases with critical findings.', val: 'ENABLED' },
              { policy: 'Monthly budget', desc: 'Estimated usage ceiling for this workspace.', val: '$100.00' },
              { policy: 'Activity notifications', desc: 'Build completions and review requests.', val: 'EMAIL' },
            ].map((row, idx) => (
              <div key={idx} className="py-4 grid grid-cols-12 items-center text-sm gap-4">
                <span className="col-span-12 sm:col-span-4 font-bold text-base text-[#0a0d0c]">{row.policy}</span>
                <span className="col-span-8 sm:col-span-5 text-xs text-[#4f544e]">{row.desc}</span>
                <span className="col-span-4 sm:col-span-3 text-right font-mono text-xs text-black font-semibold">{row.val}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Section 03 / CONNECTIONS */}
        <section className="space-y-6 pt-8">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">03 / CONNECTIONS</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">YOUR DELIVERY STACK.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {[
              { name: 'Source control', desc: 'Repository connection and branch access.', status: 'NOT CONNECTED' },
              { name: 'Container registry', desc: 'Destination for generated Docker images.', status: 'NOT CONNECTED' },
              { name: 'Deployment provider', desc: 'Production credentials and environments.', status: 'NOT CONNECTED' },
            ].map((row, idx) => (
              <div key={idx} className="py-4 grid grid-cols-12 items-center text-sm gap-4">
                <span className="col-span-12 sm:col-span-4 font-bold text-base text-[#0a0d0c]">{row.name}</span>
                <span className="col-span-8 sm:col-span-5 text-xs text-[#4f544e]">{row.desc}</span>
                <span className="col-span-4 sm:col-span-3 text-right font-mono text-xs text-[#6e736d]">{row.status}</span>
              </div>
            ))}
          </div>
        </section>

        <WorkspaceFooter nextLabel="Workflows" nextHref="/workflows" />
      </main>
    </div>
  );
}
