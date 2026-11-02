import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  User,
  Mail,
  Calendar,
  Shield,
  Key,
  FolderGit2,
  PlusCircle,
  CheckCircle2,
  Lock,
} from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user } = useAuth();

  if (!user) return null;

  const joinDate = new Date(user.created_at).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="border-b border-[#1F293D] pb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Researcher Account & Security
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Identity credentials, verified authentication claims, and personal workspace parameters.
        </p>
      </div>

      {/* Main Profile Card */}
      <div className="dna-card p-6 space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#1F293D] pb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-500 flex items-center justify-center text-xl font-bold text-white shadow-glow-purple flex-shrink-0">
              {getInitials(user.full_name)}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{user.full_name}</h2>
              <p className="text-xs text-gray-400 font-mono mt-0.5">{user.email}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="w-3 h-3" />
                  Authenticated Session Active
                </span>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Link
              to="/new-project"
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-purple-600 hover:bg-purple-500 text-white flex items-center gap-1.5 shadow-glow-purple transition-all"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              New Project
            </Link>
            <Link
              to="/projects"
              className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[#162032] hover:bg-[#1E2B45] text-gray-200 border border-[#232E47] flex items-center gap-1.5 transition-colors"
            >
              <FolderGit2 className="w-3.5 h-3.5" />
              My Projects
            </Link>
          </div>
        </div>

        {/* Identity Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-4 rounded-lg bg-[#0E1424] border border-[#1F293D] space-y-1">
            <span className="text-gray-400 flex items-center gap-1.5 font-sans font-medium">
              <User className="w-3.5 h-3.5 text-purple-400" />
              Account ID (UUID)
            </span>
            <p className="text-gray-200 break-all">{user.id}</p>
          </div>

          <div className="p-4 rounded-lg bg-[#0E1424] border border-[#1F293D] space-y-1">
            <span className="text-gray-400 flex items-center gap-1.5 font-sans font-medium">
              <Mail className="w-3.5 h-3.5 text-cyan-400" />
              Primary Email
            </span>
            <p className="text-gray-200">{user.email}</p>
          </div>

          <div className="p-4 rounded-lg bg-[#0E1424] border border-[#1F293D] space-y-1">
            <span className="text-gray-400 flex items-center gap-1.5 font-sans font-medium">
              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
              Member Since
            </span>
            <p className="text-gray-200">{joinDate}</p>
          </div>

          <div className="p-4 rounded-lg bg-[#0E1424] border border-[#1F293D] space-y-1">
            <span className="text-gray-400 flex items-center gap-1.5 font-sans font-medium">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              Password Cryptography
            </span>
            <p className="text-emerald-300">Bcrypt (Cost Factor 12) + Salted Hash</p>
          </div>
        </div>
      </div>

      {/* Security Architecture Details */}
      <div className="dna-card p-6 space-y-4">
        <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
          <Key className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-semibold text-white">Active Session Security Measures</h3>
        </div>

        <div className="space-y-3 text-xs text-gray-300">
          <div className="flex items-start gap-2.5">
            <Lock className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">HttpOnly Cookie Architecture: </strong>
              Your JWT access token is stored in an HttpOnly, SameSite=Lax cookie. This prevents
              malicious client-side scripts from reading or exfiltrating your credentials via XSS attacks.
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <Shield className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Multi-Tenant Row-Level Ownership: </strong>
              Every project and research dataset in PostgreSQL is indexed and scoped directly by your
              user ID. Cross-tenant access is rejected at both the database and routing levels.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

