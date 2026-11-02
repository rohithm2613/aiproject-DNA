import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  accentColor?: 'purple' | 'blue' | 'cyan' | 'emerald';
  trend?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  accentColor = 'purple',
  trend,
}) => {
  const accentStyles = {
    purple: {
      bg: 'bg-purple-500/10',
      text: 'text-purple-400',
      border: 'border-purple-500/20',
      hoverGlow: 'hover:border-purple-500/40 hover:shadow-glow-purple',
    },
    blue: {
      bg: 'bg-blue-500/10',
      text: 'text-blue-400',
      border: 'border-blue-500/20',
      hoverGlow: 'hover:border-blue-500/40 hover:shadow-glow-blue',
    },
    cyan: {
      bg: 'bg-cyan-500/10',
      text: 'text-cyan-400',
      border: 'border-cyan-500/20',
      hoverGlow: 'hover:border-cyan-500/40',
    },
    emerald: {
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-400',
      border: 'border-emerald-500/20',
      hoverGlow: 'hover:border-emerald-500/40',
    },
  }[accentColor];

  return (
    <div
      className={`dna-card p-5 relative overflow-hidden transition-all duration-300 ${accentStyles.hoverGlow}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium tracking-wider uppercase text-gray-400">
            {title}
          </p>
          <h3 className="text-2xl font-bold tracking-tight text-white mt-1.5 font-sans">
            {value}
          </h3>
        </div>
        <div className={`p-2.5 rounded-lg ${accentStyles.bg} ${accentStyles.border} border`}>
          <Icon className={`w-5 h-5 ${accentStyles.text}`} />
        </div>
      </div>
      {(subtitle || trend) && (
        <div className="mt-3.5 flex items-center justify-between text-xs border-t border-gray-800/80 pt-2.5">
          <span className="text-gray-400">{subtitle}</span>
          {trend && (
            <span className="text-emerald-400 font-medium">
              {trend}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

