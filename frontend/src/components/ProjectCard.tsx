import React from 'react';
import { Project } from '../types/project';
import { StatusBadge } from './StatusBadge';
import { DomainBadge } from './DomainBadge';
import { Calendar, Cpu, ArrowUpRight, Sparkles } from 'lucide-react';

interface ProjectCardProps {
  project: Project;
  onViewDetails?: (project: Project) => void;
  onAnalyzeClick?: (project: Project) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onViewDetails,
  onAnalyzeClick,
}) => {
  const formattedDate = new Date(project.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="dna-card p-6 flex flex-col justify-between hover:border-indigo-500/40 hover:shadow-lg transition-all duration-200 group">
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          <DomainBadge domain={project.domain} />
          <StatusBadge status={project.status} size="sm" />
        </div>

        <h3 className="text-lg font-semibold text-white group-hover:text-cyan-300 transition-colors line-clamp-1 mb-2">
          {project.title}
        </h3>

        <p className="text-sm text-gray-400 line-clamp-3 mb-4 leading-relaxed">
          {project.description}
        </p>

        {project.technologies && project.technologies.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {project.technologies.slice(0, 4).map((tech, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-[#162032] text-gray-300 border border-gray-700/60"
              >
                <Cpu className="w-2.5 h-2.5 text-indigo-400" />
                {tech}
              </span>
            ))}
            {project.technologies.length > 4 && (
              <span className="text-[11px] font-mono px-1.5 py-0.5 text-gray-500">
                +{project.technologies.length - 4} more
              </span>
            )}
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-gray-800/80 flex items-center justify-between text-xs text-gray-400 mt-2">
        <div className="flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5 text-gray-500" />
          <span>{formattedDate}</span>
        </div>

        <div className="flex items-center gap-2">
          {onViewDetails && (
            <button
              onClick={() => onViewDetails(project)}
              className="px-2.5 py-1 text-xs font-medium text-gray-300 hover:text-white hover:bg-gray-800 rounded transition-colors inline-flex items-center gap-1"
            >
              Details
              <ArrowUpRight className="w-3 h-3" />
            </button>
          )}
          {onAnalyzeClick && (
            <button
              onClick={() => onAnalyzeClick(project)}
              className="px-2.5 py-1 text-xs font-medium bg-purple-600/20 text-purple-300 border border-purple-500/30 hover:bg-purple-600/30 rounded transition-colors inline-flex items-center gap-1"
            >
              <Sparkles className="w-3 h-3 text-purple-400" />
              Analyze
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

