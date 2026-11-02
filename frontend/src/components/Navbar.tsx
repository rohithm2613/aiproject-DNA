import React, { useEffect, useState, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Dna,
  PlusCircle,
  Menu,
  X,
  Sparkles,
  LogOut,
  User as UserIcon,
  ChevronDown,
  LogIn,
  UserPlus,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { projectService } from '../services/projectService';
import { HealthResponse } from '../types/health';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    projectService
      .getHealth()
      .then((data) => setHealth(data))
      .catch(() => setHealth(null));
  }, [location.pathname]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setUserDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  const handleLogout = async () => {
    setUserDropdownOpen(false);
    await logout();
    navigate('/login');
  };

  const navLinks = isAuthenticated
    ? [
        { name: 'Dashboard', path: '/dashboard' },
        { name: 'Projects', path: '/projects' },
        { name: 'Settings', path: '/settings' },
      ]
    : [
        { name: 'Overview', path: '/' },
        { name: 'Features', path: '/#features' },
      ];

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  };

  return (
    <nav className="sticky top-0 z-40 w-full border-b border-[#1F293D] bg-[#0B0F19]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-600 to-indigo-600 shadow-glow-purple group-hover:scale-105 transition-transform duration-200">
              <Dna className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
                AI Project<span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">DNA</span>
              </span>
              <span className="text-[10px] uppercase font-mono tracking-widest text-gray-400 -mt-1">
                Validation Platform
              </span>
            </div>
          </Link>

          {/* Desktop Nav Items */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-purple-600/15 text-purple-300 border border-purple-500/30'
                      : 'text-gray-300 hover:text-white hover:bg-gray-800/60'
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </div>

          {/* Right Action Area */}
          <div className="hidden md:flex items-center gap-3">
            {/* Live API Health indicator */}
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#111827] border border-[#232E47] text-xs text-gray-400"
              title={
                health
                  ? `Backend: ${health.status} (${health.database?.dialect || 'connected'})`
                  : 'Backend: offline'
              }
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === 'healthy'
                    ? 'bg-emerald-400 animate-pulse'
                    : health
                    ? 'bg-amber-400'
                    : 'bg-red-400'
                }`}
              />
              <span className="text-[11px] font-mono">
                {health?.status === 'healthy' ? 'API Online' : 'API Standalone'}
              </span>
            </div>

            {isAuthenticated && user ? (
              <>
                <Link
                  to="/new-project"
                  className="inline-flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-glow-purple transition-all duration-200"
                >
                  <PlusCircle className="w-4 h-4" />
                  Analyze New Idea
                </Link>

                {/* User Dropdown */}
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                    className="flex items-center gap-2 p-1.5 pl-2.5 rounded-xl bg-[#111827] hover:bg-[#162032] border border-[#232E47] text-gray-200 transition-colors"
                  >
                    <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-purple-600 to-cyan-500 flex items-center justify-center text-[11px] font-bold text-white">
                      {getInitials(user.full_name)}
                    </div>
                    <span className="text-xs font-medium max-w-[120px] truncate">
                      {user.full_name}
                    </span>
                    <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
                  </button>

                  {userDropdownOpen && (
                    <div className="absolute right-0 mt-2 w-52 bg-[#111827] border border-[#232E47] rounded-xl shadow-2xl py-1.5 z-50 animate-in fade-in">
                      <div className="px-3.5 py-2 border-b border-gray-800">
                        <p className="text-xs font-semibold text-white truncate">{user.full_name}</p>
                        <p className="text-[11px] text-gray-400 font-mono truncate">{user.email}</p>
                      </div>

                      <Link
                        to="/profile"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center gap-2 px-3.5 py-2 text-xs text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
                      >
                        <UserIcon className="w-4 h-4 text-purple-400" />
                        My Profile & Account
                      </Link>

                      <Link
                        to="/settings"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center gap-2 px-3.5 py-2 text-xs text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
                      >
                        <Sparkles className="w-4 h-4 text-cyan-400" />
                        Workspace Preferences
                      </Link>

                      <div className="border-t border-gray-800 my-1"></div>

                      <button
                        onClick={handleLogout}
                        className="w-full text-left flex items-center gap-2 px-3.5 py-2 text-xs text-rose-400 hover:bg-rose-500/10 transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-300 hover:text-white hover:bg-gray-800/80 rounded-lg transition-colors"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-purple-600 hover:bg-purple-500 text-white shadow-glow-purple transition-all"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu trigger */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#1F293D] bg-[#0E1424] px-4 pt-2 pb-4 space-y-2">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              to={link.path}
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                location.pathname === link.path
                  ? 'bg-purple-600/20 text-purple-300'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              {link.name}
            </Link>
          ))}

          {isAuthenticated && user ? (
            <div className="pt-2 border-t border-gray-800 space-y-2">
              <Link
                to="/profile"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-md"
              >
                Profile ({user.full_name})
              </Link>
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  handleLogout();
                }}
                className="w-full text-left px-3 py-2 text-sm text-rose-400 hover:bg-rose-500/10 rounded-md"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div className="pt-2 border-t border-gray-800 flex gap-2">
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="flex-1 py-2 text-center text-xs font-medium bg-gray-800 text-gray-200 rounded-lg"
              >
                Sign In
              </Link>
              <Link
                to="/signup"
                onClick={() => setMobileMenuOpen(false)}
                className="flex-1 py-2 text-center text-xs font-medium bg-purple-600 text-white rounded-lg"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      )}
    </nav>
  );
};
