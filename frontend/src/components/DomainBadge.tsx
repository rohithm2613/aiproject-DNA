import React from 'react';
import { Layers } from 'lucide-react';

interface DomainBadgeProps {
  domain: string;
}

export const DomainBadge: React.FC<DomainBadgeProps> = ({ domain }) => {
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium bg-[#1E293B] text-cyan-300 border border-cyan-500/20">
      <Layers className="w-3 h-3 text-cyan-400" />
      {domain}
    </span>
  );
};

