'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface Project {
  id: string;
  name: string;
  description: string;
  framework: string;
  status: 'ACTIVE' | 'BUILD IN PROGRESS' | 'STABLE' | 'ARCHIVED';
  lastActivity: string;
  techStack: string[];
  activeStageIndex: number; // 0: Plan, 1: Build, 2: Verify, 3: Ship
  stageProgress: number[];  // 0 to 100 for each stage
  tokensUsed: number;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  agent: string;
  message: string;
  stage: string;
}

interface ProjectContextType {
  projects: Project[];
  activeProjectId: string;
  activeProject: Project;
  setActiveProjectId: (id: string) => void;
  isRunning: boolean;
  toggleRunning: () => void;
  advanceStage: () => void;
  restartRun: () => void;
  createNewProject: (name: string, description: string, framework: string) => string;
  logs: LogEntry[];
  tokensPerSec: number;
  recentThroughput: number[];
  toastMessage: string | null;
  showToast: (msg: string) => void;
}

const initialProjects: Project[] = [
  {
    id: 'p-1',
    name: 'Commerce Platform',
    description: 'Full-stack subscription & checkout platform with Stripe and PostgreSQL',
    framework: 'fullstack',
    status: 'BUILD IN PROGRESS',
    lastActivity: 'Just now',
    techStack: ['Spring Boot 3', 'Next.js 14', 'PostgreSQL', 'Docker'],
    activeStageIndex: 1, // Currently on "Build"
    stageProgress: [100, 68, 0, 0],
    tokensUsed: 324500,
  },
  {
    id: 'p-2',
    name: 'Taskflow Work Management',
    description: 'Collaborative task management with real-time WebSocket sync',
    framework: 'microservice',
    status: 'STABLE',
    lastActivity: '3 hours ago',
    techStack: ['Next.js 14', 'TypeScript', 'FastAPI', 'Qdrant'],
    activeStageIndex: 3, // Complete / Live
    stageProgress: [100, 100, 100, 100],
    tokensUsed: 612800,
  },
  {
    id: 'p-3',
    name: 'Analytics API Engine',
    description: 'High-throughput telemetry ingestion and real-time aggregation',
    framework: 'backend',
    status: 'ACTIVE',
    lastActivity: '1 day ago',
    techStack: ['Python', 'FastAPI', 'ClickHouse', 'Redis'],
    activeStageIndex: 2,
    stageProgress: [100, 100, 45, 0],
    tokensUsed: 198400,
  },
];

const initialLogs: LogEntry[] = [
  {
    id: 'l-1',
    timestamp: '14:28:12',
    agent: 'Architect',
    message: 'Locked OpenAPI 3.1 specification and RFC data contracts.',
    stage: 'Plan',
  },
  {
    id: 'l-2',
    timestamp: '14:29:45',
    agent: 'Database',
    message: 'Generated PostgreSQL schema migrations with composite indexes.',
    stage: 'Plan',
  },
  {
    id: 'l-3',
    timestamp: '14:31:02',
    agent: 'Developer',
    message: 'Implementing OAuth2 PKCE routes and Stripe webhook handlers.',
    stage: 'Build',
  },
];

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>(initialProjects);
  const [activeProjectId, setActiveProjectId] = useState<string>('p-1');
  const [isRunning, setIsRunning] = useState<boolean>(true);
  const [logs, setLogs] = useState<LogEntry[]>(initialLogs);
  const [tokensPerSec, setTokensPerSec] = useState<number>(418);
  const [recentThroughput, setRecentThroughput] = useState<number[]>([
    380, 395, 410, 405, 422, 430, 415, 428, 440, 418, 435, 420
  ]);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const activeProject = projects.find((p) => p.id === activeProjectId) || projects[0];

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((cur) => (cur === msg ? null : cur));
    }, 3000);
  };

  const toggleRunning = () => {
    setIsRunning((prev) => {
      const next = !prev;
      showToast(next ? 'Agents resumed' : 'Pipeline paused');
      return next;
    });
  };

  const advanceStage = () => {
    setProjects((prev) =>
      prev.map((proj) => {
        if (proj.id !== activeProjectId) return proj;

        const curIndex = proj.activeStageIndex;
        if (curIndex >= 3 && proj.stageProgress[3] >= 100) {
          showToast('All 4 stages completed for this project');
          return proj;
        }

        const newProgress = [...proj.stageProgress];
        newProgress[curIndex] = 100;
        const nextIndex = Math.min(3, curIndex + 1);
        if (nextIndex > curIndex) {
          newProgress[nextIndex] = Math.max(15, newProgress[nextIndex]);
        }

        const stages = ['Plan', 'Build', 'Verify', 'Ship'];
        const agentMap = ['Architect', 'Developer', 'QA & Security', 'DevOps'];
        const now = new Date().toTimeString().slice(0, 8);

        setLogs((prevLogs) => [
          {
            id: `l-${Date.now()}`,
            timestamp: now,
            agent: agentMap[curIndex],
            message: `Completed ${stages[curIndex]} stage, handed off artifacts to ${agentMap[nextIndex]}.`,
            stage: stages[curIndex],
          },
          ...prevLogs.slice(0, 8),
        ]);

        showToast(`Advanced to ${stages[nextIndex]} stage`);

        return {
          ...proj,
          activeStageIndex: nextIndex,
          stageProgress: newProgress,
          tokensUsed: proj.tokensUsed + 48000,
          status: nextIndex === 3 && newProgress[3] === 100 ? 'STABLE' : 'BUILD IN PROGRESS',
        };
      })
    );
  };

  const restartRun = () => {
    setProjects((prev) =>
      prev.map((proj) => {
        if (proj.id !== activeProjectId) return proj;
        return {
          ...proj,
          activeStageIndex: 0,
          stageProgress: [25, 0, 0, 0],
          status: 'BUILD IN PROGRESS',
        };
      })
    );
    const now = new Date().toTimeString().slice(0, 8);
    setLogs((prev) => [
      {
        id: `l-${Date.now()}`,
        timestamp: now,
        agent: 'Planner',
        message: 'Restarted project run. Architect is mapping technical blueprint.',
        stage: 'Plan',
      },
      ...prev.slice(0, 8),
    ]);
    setIsRunning(true);
    showToast('New pipeline run started');
  };

  const createNewProject = (name: string, description: string, framework: string): string => {
    const newId = `p-${Date.now()}`;
    const stackMap: Record<string, string[]> = {
      fullstack: ['Spring Boot 3', 'Next.js 14', 'PostgreSQL', 'Docker'],
      microservice: ['FastAPI', 'LangGraph', 'Qdrant', 'Docker'],
      backend: ['Java 21', 'Spring Boot 3', 'Redis', 'OAuth2'],
    };

    const newProj: Project = {
      id: newId,
      name: name || 'Untitled Project',
      description: description || 'Autonomous project generated from prompt',
      framework,
      status: 'BUILD IN PROGRESS',
      lastActivity: 'Just now',
      techStack: stackMap[framework] || ['Next.js 14', 'FastAPI', 'Docker'],
      activeStageIndex: 0,
      stageProgress: [30, 0, 0, 0],
      tokensUsed: 24000,
    };

    setProjects((prev) => [newProj, ...prev]);
    setActiveProjectId(newId);
    setIsRunning(true);

    const now = new Date().toTimeString().slice(0, 8);
    setLogs((prev) => [
      {
        id: `l-${Date.now()}`,
        timestamp: now,
        agent: 'Architect',
        message: `Assembled team for "${newProj.name}". Requirements decomposed into architecture.`,
        stage: 'Plan',
      },
      ...prev.slice(0, 8),
    ]);

    showToast(`Project "${newProj.name}" created! Agents started.`);
    return newId;
  };

  // Continuous real-time execution loop when isRunning is true
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setProjects((prev) =>
        prev.map((proj) => {
          if (proj.id !== activeProjectId) return proj;

          const curIdx = proj.activeStageIndex;
          const currentProg = proj.stageProgress[curIdx];

          // If stage is finished and not on last stage, auto advance
          if (currentProg >= 100) {
            if (curIdx < 3) {
              const nextIdx = curIdx + 1;
              const nextProgress = [...proj.stageProgress];
              nextProgress[nextIdx] = Math.min(100, nextProgress[nextIdx] + 5);

              const stages = ['Plan', 'Build', 'Verify', 'Ship'];
              const agentMap = ['Architect', 'Developer', 'QA & Security', 'DevOps'];
              const now = new Date().toTimeString().slice(0, 8);

              setLogs((prevLogs) => [
                {
                  id: `l-${Date.now()}`,
                  timestamp: now,
                  agent: agentMap[curIdx],
                  message: `Stage ${stages[curIdx]} hit 100%. Handing off artifacts to ${agentMap[nextIdx]}.`,
                  stage: stages[curIdx],
                },
                ...prevLogs.slice(0, 8),
              ]);

              return {
                ...proj,
                activeStageIndex: nextIdx,
                stageProgress: nextProgress,
                tokensUsed: proj.tokensUsed + 1200,
              };
            }
            return proj;
          }

          // Increment current stage progress
          const increment = Math.floor(Math.random() * 4) + 2; // 2% - 5%
          const updatedProgress = [...proj.stageProgress];
          updatedProgress[curIdx] = Math.min(100, currentProg + increment);

          return {
            ...proj,
            stageProgress: updatedProgress,
            tokensUsed: proj.tokensUsed + 850,
          };
        })
      );

      // Fluctuate token throughput slightly
      setTokensPerSec(() => {
        const speed = Math.round(410 + Math.random() * 45);
        setRecentThroughput((prev) => [...prev.slice(1), speed]);
        return speed;
      });
    }, 1200);

    return () => clearInterval(interval);
  }, [isRunning, activeProjectId]);

  return (
    <ProjectContext.Provider
      value={{
        projects,
        activeProjectId,
        activeProject,
        setActiveProjectId,
        isRunning,
        toggleRunning,
        advanceStage,
        restartRun,
        createNewProject,
        logs,
        tokensPerSec,
        recentThroughput,
        toastMessage,
        showToast,
      }}
    >
      {children}
      {/* Universal Floating Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-[#0a0d0c] text-white px-5 py-3 border border-[#c4ff2e] shadow-2xl flex items-center gap-3 text-xs font-mono tracking-wider uppercase animate-fade-in">
          <span className="w-2 h-2 rounded-full bg-[#c4ff2e] animate-pulse" />
          <span>{toastMessage}</span>
        </div>
      )}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}

