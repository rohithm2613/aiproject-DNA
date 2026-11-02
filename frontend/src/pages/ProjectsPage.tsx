import React, { useEffect, useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  PlusCircle,
  FolderGit2,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { ProjectCard } from '../components/ProjectCard';
import { Modal } from '../components/Modal';
import { projectService } from '../services/projectService';
import { Project } from '../types/project';

const DOMAIN_FILTERS = [
  'All',
  'Healthcare & AI',
  'CleanTech & IoT',
  'Cybersecurity & Web3',
  'EdTech',
  'Artificial Intelligence & ML',
  'Enterprise SaaS & Cloud',
];

const STATUS_FILTERS = [
  'All',
  'pending_validation',
  'analysis_completed',
  'ready_for_analysis',
  'validated',
  'draft',
];

export const ProjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');

  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const res = await projectService.getProjects({
        search: searchTerm || undefined,
        domain: selectedDomain !== 'All' ? selectedDomain : undefined,
        status: selectedStatus !== 'All' ? selectedStatus : undefined,
      });
      setProjects(res.items);
    } catch (err) {
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [selectedDomain, selectedStatus]);

  // Client-side instant filter fallback for responsiveness
  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      const matchesSearch =
        !searchTerm.trim() ||
        p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.domain.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesDomain =
        selectedDomain === 'All' ||
        p.domain.toLowerCase().includes(selectedDomain.toLowerCase());

      const matchesStatus =
        selectedStatus === 'All' || p.status.toLowerCase() === selectedStatus.toLowerCase();

      return matchesSearch && matchesDomain && matchesStatus;
    });
  }, [projects, searchTerm, selectedDomain, selectedStatus]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProjects();
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#1F293D] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <FolderGit2 className="w-5 h-5 text-purple-400" />
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Projects Catalog
            </h1>
          </div>
          <p className="text-sm text-gray-400">
            Browse and manage all registered innovation ideas and their validation trajectories.
          </p>
        </div>

        <Link
          to="/new-project"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium text-sm shadow-glow-purple transition-all duration-200"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Project</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="dna-card p-4 space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search projects by title, description, or domain..."
              className="w-full pl-9 dna-input text-xs sm:text-sm"
            />
          </div>

          {/* Domain Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
              className="dna-input text-xs cursor-pointer min-w-[140px]"
            >
              {DOMAIN_FILTERS.map((d) => (
                <option key={d} value={d} className="bg-[#111827]">
                  {d === 'All' ? 'All Domains' : d}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="dna-input text-xs cursor-pointer min-w-[140px]"
            >
              {STATUS_FILTERS.map((s) => (
                <option key={s} value={s} className="bg-[#111827]">
                  {s === 'All'
                    ? 'All Statuses'
                    : s.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>

          {/* Refresh Button */}
          <button
            type="button"
            onClick={fetchProjects}
            className="p-2.5 rounded-lg bg-[#162032] hover:bg-[#1E2B45] text-gray-400 hover:text-white border border-[#232E47] transition-colors"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </form>

        <div className="flex items-center justify-between text-xs text-gray-400 pt-1 font-mono">
          <span>
            Showing <strong className="text-white">{filteredProjects.length}</strong> of{' '}
            {projects.length} recorded projects
          </span>

          {(searchTerm || selectedDomain !== 'All' || selectedStatus !== 'All') && (
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedDomain('All');
                setSelectedStatus('All');
              }}
              className="text-purple-400 hover:underline cursor-pointer"
            >
              Reset filters
            </button>
          )}
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="dna-card p-12 text-center text-gray-400 animate-pulse">
          Loading projects from database...
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="dna-card p-12 text-center space-y-4">
          <FolderGit2 className="w-12 h-12 text-gray-600 mx-auto" />
          <h3 className="text-base font-semibold text-white">No projects found</h3>
          <p className="text-xs text-gray-400 max-w-sm mx-auto">
            No projects matched your active search query or filter settings. Try adjusting your
            criteria or create a new project.
          </p>
          <button
            onClick={() => {
              setSearchTerm('');
              setSelectedDomain('All');
              setSelectedStatus('All');
            }}
            className="px-4 py-2 text-xs rounded-lg bg-[#162032] text-gray-300 hover:text-white border border-[#232E47]"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onViewDetails={(p) => setSelectedProject(p)}
              onAnalyzeClick={(p) => navigate(`/projects/${p.id}/analysis`)}
            />
          ))}
        </div>
      )}

      {/* Project Detail Modal */}
      {selectedProject && (
        <Modal
          isOpen={!!selectedProject}
          onClose={() => setSelectedProject(null)}
          title={selectedProject.title}
          maxWidth="lg"
        >
          <div className="space-y-5 text-sm">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 px-2.5 py-1 rounded border border-cyan-500/20">
                {selectedProject.domain}
              </span>
              <span className="text-xs font-mono text-gray-400">
                ID: {selectedProject.id}
              </span>
            </div>

            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-gray-400">
                Project Overview
              </span>
              <p className="text-gray-300 mt-1 leading-relaxed whitespace-pre-line bg-[#0E1424] p-4 rounded-lg border border-[#1F293D]">
                {selectedProject.description}
              </p>
            </div>

            {selectedProject.objectives && (
              <div>
                <span className="text-xs font-mono uppercase tracking-wider text-gray-400">
                  Target Objectives & Expected Outcomes
                </span>
                <p className="text-gray-300 mt-1 leading-relaxed bg-[#0E1424] p-4 rounded-lg border border-[#1F293D]">
                  {selectedProject.objectives}
                </p>
              </div>
            )}

            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-gray-400">
                Architecture & Stack
              </span>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {selectedProject.technologies.map((t, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 text-xs font-mono rounded bg-[#162032] text-gray-200 border border-gray-700/60"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-gray-800 flex items-center justify-between">
              <span className="text-xs text-gray-400 font-mono">
                Created on {new Date(selectedProject.created_at).toLocaleDateString()}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedProject(null)}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    const id = selectedProject.id;
                    setSelectedProject(null);
                    navigate(`/projects/${id}/analysis`);
                  }}
                  className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-purple-600 hover:bg-purple-500 text-white flex items-center gap-1.5 shadow-glow-purple transition-all"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  View AI Analysis
                </button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

