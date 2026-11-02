import React, { useState, useEffect } from 'react';
import {
  User,
  Info,
  CheckCircle,
  Save,
  Moon,
  Palette,
  Shield,
} from 'lucide-react';
import { projectService } from '../services/projectService';
import { HealthResponse } from '../types/health';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  // Profile state placeholder
  const [profile, setProfile] = useState({
    name: 'Dr. Alex Vance',
    email: 'alex.vance@stanford.edu',
    affiliation: 'Stanford AI & Neural Systems Lab',
    role: 'Lead Innovation Researcher',
    bio: 'Investigating neuro-symbolic reasoning models and distributed intelligence architectures.',
  });
  const [profileSaved, setProfileSaved] = useState(false);

  // Theme preferences state
  const [accentColor, setAccentColor] = useState<'purple' | 'blue' | 'cyan'>('purple');
  const [density, setDensity] = useState<'comfortable' | 'compact'>('comfortable');

  useEffect(() => {
    projectService
      .getHealth()
      .then((data) => {
        setHealth(data);
      })
      .catch((err) => {
        console.warn('Could not query backend health endpoint:', err);
      });
  }, []);

  const handleProfileSave = (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSaved(true);
    setTimeout(() => setProfileSaved(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="border-b border-[#1F293D] pb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Platform Settings & Configuration
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Manage your researcher profile, UI appearance, and view backend environment parameters.
        </p>
      </div>

      {/* 1. User Profile Placeholder */}
      <div className="dna-card p-6 space-y-6">
        <div className="flex items-center gap-3 border-b border-[#1F293D] pb-4">
          <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Researcher Profile</h2>
            <p className="text-xs text-gray-400">
              Institutional identity used for authorship on innovation reports.
            </p>
          </div>
        </div>

        <form onSubmit={handleProfileSave} className="space-y-4">
          <div className="flex items-center gap-4 pb-2">
            <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-xl font-bold text-white shadow-glow-purple flex-shrink-0">
              AV
            </div>
            <div>
              <p className="text-sm font-semibold text-white">{profile.name}</p>
              <p className="text-xs text-gray-400">{profile.email}</p>
              <span className="inline-block mt-1 text-[10px] font-mono uppercase bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded border border-purple-500/30">
                Verified Academic
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                className="w-full dna-input text-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                className="w-full dna-input text-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Affiliation / Lab / Company
              </label>
              <input
                type="text"
                value={profile.affiliation}
                onChange={(e) => setProfile({ ...profile, affiliation: e.target.value })}
                className="w-full dna-input text-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Primary Role
              </label>
              <input
                type="text"
                value={profile.role}
                onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                className="w-full dna-input text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">
              Research Focus & Specialization
            </label>
            <textarea
              rows={2}
              value={profile.bio}
              onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
              className="w-full dna-input text-xs resize-none"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            {profileSaved && (
              <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium animate-in fade-in">
                <CheckCircle className="w-4 h-4" />
                Profile preferences saved successfully
              </span>
            )}
            <div className="ml-auto">
              <button
                type="submit"
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-purple-600 hover:bg-purple-500 text-white transition-colors"
              >
                <Save className="w-3.5 h-3.5" />
                Save Profile
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* 2. Theme Preferences */}
      <div className="dna-card p-6 space-y-6">
        <div className="flex items-center gap-3 border-b border-[#1F293D] pb-4">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Palette className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Theme & Display Preferences</h2>
            <p className="text-xs text-gray-400">
              Customize visual ergonomics and accent highlights.
            </p>
          </div>
        </div>

        <div className="space-y-5 text-xs">
          {/* Theme mode */}
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-white">Default Theme</p>
              <p className="text-gray-400">
                AI ProjectDNA defaults to premium Dark Mode for high-contrast data visualization.
              </p>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#162032] border border-[#232E47] text-gray-200">
              <Moon className="w-3.5 h-3.5 text-purple-400" />
              <span>Dark Theme (Active)</span>
            </div>
          </div>

          {/* Accent Color */}
          <div className="flex items-center justify-between border-t border-gray-800/80 pt-4">
            <div>
              <p className="font-semibold text-white">Accent Palette</p>
              <p className="text-gray-400">Select active highlight gradient accents.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setAccentColor('purple')}
                className={`w-7 h-7 rounded-full bg-purple-600 border-2 transition-all ${
                  accentColor === 'purple' ? 'border-white scale-110 shadow-glow-purple' : 'border-transparent'
                }`}
                title="Electric Purple"
              />
              <button
                type="button"
                onClick={() => setAccentColor('blue')}
                className={`w-7 h-7 rounded-full bg-blue-600 border-2 transition-all ${
                  accentColor === 'blue' ? 'border-white scale-110 shadow-glow-blue' : 'border-transparent'
                }`}
                title="Electric Blue"
              />
              <button
                type="button"
                onClick={() => setAccentColor('cyan')}
                className={`w-7 h-7 rounded-full bg-cyan-500 border-2 transition-all ${
                  accentColor === 'cyan' ? 'border-white scale-110' : 'border-transparent'
                }`}
                title="Cyan Accent"
              />
            </div>
          </div>

          {/* Layout density */}
          <div className="flex items-center justify-between border-t border-gray-800/80 pt-4">
            <div>
              <p className="font-semibold text-white">Layout Spacing</p>
              <p className="text-gray-400">Choose dashboard card density.</p>
            </div>
            <div className="flex items-center gap-1 bg-[#162032] p-1 rounded-lg border border-[#232E47]">
              <button
                type="button"
                onClick={() => setDensity('comfortable')}
                className={`px-3 py-1 rounded text-xs transition-colors ${
                  density === 'comfortable' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                Comfortable
              </button>
              <button
                type="button"
                onClick={() => setDensity('compact')}
                className={`px-3 py-1 rounded text-xs transition-colors ${
                  density === 'compact' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                Compact
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Application Information & Diagnostics */}
      <div className="dna-card p-6 space-y-6">
        <div className="flex items-center gap-3 border-b border-[#1F293D] pb-4">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Info className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Application Information</h2>
            <p className="text-xs text-gray-400">
              System health, database configuration, and release parameters.
            </p>
          </div>
        </div>

        <div className="space-y-3 text-xs font-mono">
          <div className="flex items-center justify-between py-2 border-b border-gray-800/60">
            <span className="text-gray-400">Application Name:</span>
            <span className="text-white font-sans font-medium">AI ProjectDNA</span>
          </div>

          <div className="flex items-center justify-between py-2 border-b border-gray-800/60">
            <span className="text-gray-400">Current Milestone:</span>
            <span className="text-purple-300 font-sans font-medium">
              Phase 1 &ndash; Foundation & UI Development
            </span>
          </div>

          <div className="flex items-center justify-between py-2 border-b border-gray-800/60">
            <span className="text-gray-400">Backend API Status:</span>
            <span className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === 'healthy' ? 'bg-emerald-400' : 'bg-amber-400'
                }`}
              />
              <span className="text-gray-200">
                {health?.status ? `${health.status.toUpperCase()} (${health.version})` : 'Offline / Standalone Mode'}
              </span>
            </span>
          </div>

          <div className="flex items-center justify-between py-2 border-b border-gray-800/60">
            <span className="text-gray-400">Database Engine:</span>
            <span className="text-cyan-300">
              {health?.database?.dialect
                ? `${health.database.dialect.toUpperCase()} (${health.database.database})`
                : 'PostgreSQL 16 (Configured)'}
            </span>
          </div>

          <div className="flex items-center justify-between py-2">
            <span className="text-gray-400">Frontend Stack:</span>
            <span className="text-gray-200">React 18 &bull; TypeScript &bull; Vite &bull; Tailwind CSS</span>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-[#0E1424] border border-[#232E47] text-xs text-gray-400 flex items-start gap-2.5">
          <Shield className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
          <span>
            Phase 1 strictly establishes clean database schema creation, REST API endpoints, and a
            production UI shell. Real AI agent pipelines (RAG, embedding vector stores, and research
            retrieval) will be introduced in Phase 2.
          </span>
        </div>
      </div>
    </div>
  );
};

