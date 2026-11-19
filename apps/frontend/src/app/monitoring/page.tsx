'use client';

import { WorkspaceNav, WorkspaceFooter } from '@/components/layout/workspace-nav';

export default function MonitoringPage() {
  const chartBars = [
    18, 16, 22, 20, 24, 28, 22, 28, 34, 30, 42, 38,
    44, 32, 36, 48, 62, 54, 76, 70, 68, 80, 72, 88,
  ];

  return (
    <div className="min-h-screen bg-[#eaede6] text-[#0a0d0c] font-sans selection:bg-[#c4ff2e] selection:text-black">
      <WorkspaceNav />

      <main className="max-w-6xl mx-auto px-6 pt-10 pb-16 space-y-12">
        {/* Top Header Tags */}
        <div className="flex items-center justify-between text-xs tracking-wider text-[#6e736d] uppercase font-mono">
          <span>AGENTFORGE / MONITORING</span>
          <span>PERSONAL WORKSPACE</span>
        </div>

        {/* Title */}
        <div className="space-y-3">
          <h1 className="text-6xl sm:text-7xl md:text-8xl font-black tracking-tighter uppercase leading-none">
            MONITORING.
          </h1>
          <p className="text-sm sm:text-base text-[#4f544e]">
            See the work as it happens. Keep an eye on performance, usage, and the health of your builds.
          </p>
        </div>

        {/* 4 Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-2">
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">UPTIME</span>
            <div className="text-5xl font-black tracking-tight">99.98%</div>
            <p className="text-xs text-[#6e736d]">Guaranteed / last 30 days</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">RESPONSE TIME</span>
            <div className="text-5xl font-black tracking-tight">142ms</div>
            <p className="text-xs text-[#6e736d]">Median API latency</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">REQUESTS</span>
            <div className="text-5xl font-black tracking-tight">24.8k</div>
            <p className="text-xs text-[#6e736d]">Last 24 hours</p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-mono tracking-wider text-[#6e736d] uppercase">ERROR RATE</span>
            <div className="text-5xl font-black tracking-tight">0.02%</div>
            <p className="text-xs text-[#6e736d]">Within target range</p>
          </div>
        </div>

        {/* Black Chart Card */}
        <div className="bg-[#0a0d0c] text-white p-6 sm:p-8 rounded-none border border-[#1f3447] space-y-6">
          <div className="flex items-center justify-between text-[11px] font-mono tracking-wider text-neutral-400">
            <span className="text-[#c4ff2e]">REQUEST VOLUME / LAST 24 HOURS</span>
            <span>ILLUSTRATIVE TELEMETRY</span>
          </div>

          <div className="pt-8 pb-4">
            <div className="h-44 flex items-end justify-between gap-1 sm:gap-2">
              {chartBars.map((height, i) => (
                <div key={i} className="flex-1 flex flex-col items-center h-full justify-end group">
                  <div
                    style={{ height: `${height}%` }}
                    className="w-full bg-[#c4ff2e] transition-all hover:bg-white"
                  />
                </div>
              ))}
            </div>

            <div className="flex justify-between text-[11px] font-mono text-neutral-400 pt-3 border-t border-neutral-800 mt-2">
              <span>00:00</span>
              <span>06:00</span>
              <span>12:00</span>
              <span>18:00</span>
              <span>24:00</span>
            </div>
          </div>
        </div>

        {/* Section 01 / SERVICE HEALTH */}
        <section className="space-y-6 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono tracking-wider text-[#6e736d] uppercase">01 / SERVICE HEALTH</span>
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight uppercase">ALL SIGNAL. NO GUESSWORK.</h2>
          </div>

          <div className="divide-y divide-[#d0d5cc] border-t border-b border-[#d0d5cc]">
            {[
              { service: 'Commerce frontend', detail: 'Production - Last checked 20 seconds ago', status: 'OPERATIONAL' },
              { service: 'Application API', detail: 'Production - 142ms median response', status: 'OPERATIONAL' },
              { service: 'PostgreSQL', detail: 'Production - 12 active connections', status: 'OPERATIONAL' },
              { service: 'CI/CD runner', detail: 'Build queue - 1 waiting job', status: 'AVAILABLE' },
            ].map((row, idx) => (
              <div key={idx} className="py-4 grid grid-cols-12 items-center text-sm gap-4">
                <span className="col-span-12 sm:col-span-4 font-bold text-base text-[#0a0d0c]">{row.service}</span>
                <span className="col-span-8 sm:col-span-6 text-xs text-[#4f544e]">{row.detail}</span>
                <span className="col-span-4 sm:col-span-2 text-right font-mono text-xs text-black font-semibold">{row.status}</span>
              </div>
            ))}
          </div>
        </section>

        <WorkspaceFooter nextLabel="Settings" nextHref="/settings" />
      </main>
    </div>
  );
}
