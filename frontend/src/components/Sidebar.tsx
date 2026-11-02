import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  PlusCircle,
  User,
  Settings,
  Server,
  Sparkles,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Projects', path: '/projects', icon: FolderGit2 },
    { name: 'New Project', path: '/new-project', icon: PlusCircle },
    { name: 'Profile', path: '/profile', icon: User },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 flex-shrink-0 bg-[#0E1424] border-r border-[#1F293D] flex flex-col justify-between min-h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-6">
        {/* Brand Banner */}
        <div className="px-3 py-3 rounded-lg bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-500/20">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-semibold text-purple-300 uppercase tracking-wider">
              Phase 2 Active
            </span>
          </div>
          <p className="text-[11px] text-gray-400 leading-snug">
            Authenticated workspace & personal project dossiers.
          </p>
        </div>

        {/* Navigation Items */}
        <div className="space-y-1">
          <p className="px-3 text-[11px] font-semibold tracking-wider text-gray-400 uppercase font-mono mb-2">
            Workspace
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-purple-600/20 text-white border-l-2 border-purple-500 shadow-sm'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-[#162032]'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* System Status footer */}
      <div className="p-4 border-t border-[#1F293D] bg-[#0B0F19]/50">
        <div className="flex items-center justify-between text-xs text-gray-400 mb-1.5">
          <span className="flex items-center gap-1.5 font-mono text-[11px]">
            <Server className="w-3.5 h-3.5 text-cyan-400" />
            FastAPI Core
          </span>
          <span className="text-[10px] text-emerald-400 font-mono bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
            v1.0.0
          </span>
        </div>
        <p className="text-[10px] text-gray-400 font-mono">
          Ready for AI & RAG (Phase 2)
        </p>
      </div>
    </aside>
  );
};

