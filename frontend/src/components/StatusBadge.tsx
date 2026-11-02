import React from 'react';
import { ProjectStatus } from '../types/project';
import { Clock, CheckCircle2, AlertCircle, FileEdit } from 'lucide-react';

interface StatusBadgeProps {
  status: ProjectStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toLowerCase();

  let label = 'Pending Validation';
  let colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  let Icon = Clock;

  if (normalized === 'ready_for_analysis') {
    label = 'Ready for Analysis';
    colorClasses = 'bg-sky-500/10 text-sky-400 border-sky-500/30';
    Icon = AlertCircle;
  } else if (normalized === 'validated') {
    label = 'Validated';
    colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    Icon = CheckCircle2;
  } else if (normalized === 'draft') {
    label = 'Draft';
    colorClasses = 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    Icon = FileEdit;
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${colorClasses} ${sizeClasses}`}
    >
      <Icon className="w-3.5 h-3.5" />
      <span>{label}</span>
    </span>
  );
};

