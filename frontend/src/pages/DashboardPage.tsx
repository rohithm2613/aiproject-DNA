import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FolderKanban,
  Lightbulb,
  Clock,
  Sparkles,
  ArrowRight,
  PlusCircle,
  CheckCircle2,
  ChevronRight,
} from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { ProjectCard } from '../components/ProjectCard';
import { Modal } from '../components/Modal';
import { projectService } from '../services/projectService';
import { analysisService } from '../services/analysisService';
import { Project } from '../types/project';
import { DashboardAnalytics } from '../types/analysis';
import { useAuth } from '../context/AuthContext';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  useEffect(() => {
    Promise.all([
      projectService.getProjects({ limit: 4 }),
      analysisService.getDashboardStats().catch(() => null),
    ])
      .then(([projRes, statsRes]) => {
        setProjects(projRes.items);
        setStats(statsRes);
      })
      .catch((err) => {
        console.error('Failed to load dashboard data:', err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const totalProjects = stats?.total_projects ?? projects.length;
  const ideasAnalyzed = stats?.ideas_analyzed ?? 0;
  const pendingAnalyses = stats?.pending_analyses ?? 0;
  const completedRuns = stats?.completed_analyses ?? 0;

  return (
    <div className="space-y-8">
      {/* Top Banner & Quick Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#1F293D] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2.5 py-0.5 rounded border border-purple-500/20">
              Personal Workspace &middot; Phase 3 Active
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            {user ? `Welcome back, ${user.full_name}` : 'Innovation Intelligence Dashboard'}
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time overview of your private projects, AI analysis dossiers, and innovation metrics.
          </p>
        </div>

        <Link
          to="/new-project"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium text-sm shadow-glow-purple transition-all duration-200"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Analyze New Idea</span>
        </Link>
      </div>

      {/* Real Database Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Total Projects"
          value={totalProjects}
          subtitle="Saved in your catalog"
          trend="Database synced"
          icon={FolderKanban}
          accentColor="purple"
        />
        <MetricCard
          title="Ideas Analyzed"
          value={ideasAnalyzed}
          subtitle="Projects with AI dossier"
          trend="Google Gemini"
          icon={Sparkles}
          accentColor="cyan"
        />
        <MetricCard
          title="Pending Analyses"
          value={pendingAnalyses}
          subtitle="Awaiting initial scan"
          trend="Ready to run"
          icon={Clock}
          accentColor="blue"
        />
        <MetricCard
          title="Completed Runs"
          value={completedRuns}
          subtitle="Total analysis versions"
          trend="Active history"
          icon={CheckCircle2}
          accentColor="emerald"
        />
      </div>

      {/* Main Split: Recent Projects (2/3) + Analysis History (1/3) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Recent Projects */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Your Recent Projects</h2>
              <span className="text-xs font-mono text-gray-400 bg-[#162032] px-2 py-0.5 rounded border border-gray-700/50">
                {projects.length}
              </span>
            </div>
            <Link
              to="/projects"
              className="text-xs text-purple-400 hover:text-purple-300 font-medium inline-flex items-center gap-1 transition-colors"
            >
              View all
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="dna-card p-12 text-center text-gray-400 animate-pulse">
              Loading projects catalog...
            </div>
          ) : projects.length === 0 ? (
            <div className="dna-card p-8 text-center space-y-4">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center mx-auto">
                <Lightbulb className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-white">No projects registered yet</p>
                <p className="text-xs text-gray-400 max-w-sm mx-auto">
                  Register your first project idea to test the Gemini AI Idea Analyzer.
                </p>
              </div>
              <Link
                to="/new-project"
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-purple-600 hover:bg-purple-500 text-white shadow-glow-purple transition-all"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                Register New Project Idea
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {projects.slice(0, 4).map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onViewDetails={(p) => setSelectedProject(p)}
                  onAnalyzeClick={(p) => navigate(`/projects/${p.id}/analysis`)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Right Column: AI Analysis History Feed */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white tracking-tight">AI Analysis History</h2>
            <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/20">
              Live DB
            </span>
          </div>

          <div className="dna-card p-5 space-y-4">
            {stats?.recent_analyses && stats.recent_analyses.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_analyses.map((item) => (
                  <Link
                    key={item.id}
                    to={`/projects/${item.project_id}/analysis`}
                    className="block p-3 rounded-lg bg-[#0E1424] hover:bg-[#162032] border border-[#1F293D] hover:border-purple-500/40 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-semibold text-white group-hover:text-purple-300 transition-colors line-clamp-1">
                        {item.project_title}
                      </p>
                      <ChevronRight className="w-3.5 h-3.5 text-gray-500 group-hover:text-purple-400 flex-shrink-0 mt-0.5" />
                    </div>
                    <div className="flex items-center gap-2 mt-1.5 text-[11px] text-gray-400 font-mono">
                      <span className="text-cyan-400 truncate">{item.primary_domain}</span>
                      <span>&bull;</span>
                      <span className="text-purple-300">v{item.version}</span>
                      <span>&bull;</span>
                      <span className="text-gray-500">
                        {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent'}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 space-y-2">
                <Sparkles className="w-8 h-8 text-gray-600 mx-auto" />
                <p className="text-xs text-gray-400">No AI analysis runs completed yet.</p>
                <p className="text-[11px] text-gray-500">
                  Select a project and click "Analyze" to generate your first technical dossier.
                </p>
              </div>
            )}

            <div className="pt-3 border-t border-gray-800 text-center">
              <span className="text-[11px] text-gray-400 font-mono">
                Powered by Google Gemini 2.5 Flash
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Project Detail Modal */}
      {selectedProject && (
        <Modal
          isOpen={!!selectedProject}
          onClose={() => setSelectedProject(null)}
          title={selectedProject.title}
          maxWidth="lg"
        >
          <div className="space-y-5 text-sm">
            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-gray-400">
                Domain Category
              </span>
              <p className="text-white font-medium mt-0.5">{selectedProject.domain}</p>
            </div>

            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-gray-400">
                Problem & Idea Description
              </span>
              <p className="text-gray-300 mt-1 leading-relaxed whitespace-pre-line bg-[#0E1424] p-3 rounded-lg border border-[#1F293D]">
                {selectedProject.description}
              </p>
            </div>

            {selectedProject.objectives && (
              <div>
                <span className="text-xs font-mono uppercase tracking-wider text-gray-400">
                  Target Objectives
                </span>
                <p className="text-gray-300 mt-1 leading-relaxed bg-[#0E1424] p-3 rounded-lg border border-[#1F293D]">
                  {selectedProject.objectives}
                </p>
              </div>
            )}

            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-gray-400">
                Technology Preferences
              </span>
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                {selectedProject.technologies.map((t, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 text-xs font-mono rounded bg-[#162032] text-cyan-300 border border-cyan-500/20"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-gray-800 flex justify-end gap-2">
              <button
                onClick={() => setSelectedProject(null)}
                className="px-4 py-2 text-xs font-medium rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => {
                  const id = selectedProject.id;
                  setSelectedProject(null);
                  navigate(`/projects/${id}/analysis`);
                }}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-purple-600 hover:bg-purple-500 text-white flex items-center gap-1.5 shadow-glow-purple transition-all"
              >
                <Sparkles className="w-3.5 h-3.5" />
                View AI Analysis Dossier
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
