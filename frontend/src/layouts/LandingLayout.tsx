import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Dna, Github, Twitter, Linkedin, Heart } from 'lucide-react';

export const LandingLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      
      {/* Platform Footer */}
      <footer className="border-t border-[#1F293D] bg-[#0E1424] py-12 text-sm text-gray-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-md bg-purple-600">
                <Dna className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-white text-base">AI ProjectDNA</span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Intelligent Innovation & Project Validation Platform designed for researchers, students, and product engineers.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-gray-200 uppercase tracking-wider font-mono mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-xs">
              <li><Link to="/dashboard" className="hover:text-cyan-400 transition-colors">Overview Dashboard</Link></li>
              <li><Link to="/projects" className="hover:text-cyan-400 transition-colors">Project Catalog</Link></li>
              <li><Link to="/new-project" className="hover:text-cyan-400 transition-colors">Validate New Idea</Link></li>
              <li><Link to="/settings" className="hover:text-cyan-400 transition-colors">Settings & Config</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-gray-200 uppercase tracking-wider font-mono mb-3">
              Architecture
            </h4>
            <ul className="space-y-2 text-xs">
              <li><span className="text-gray-400">Phase 1: Foundation & UI</span></li>
              <li><span className="text-gray-400">FastAPI & PostgreSQL Core</span></li>
              <li><span className="text-gray-400">Docker Containerized</span></li>
              <li><span className="text-gray-400">Tailwind & React 18</span></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-gray-200 uppercase tracking-wider font-mono mb-3">
              Connect
            </h4>
            <p className="text-xs text-gray-400 mb-3">
              Built with precision for high-impact innovation.
            </p>
            <div className="flex items-center gap-3">
              <a href="#" className="p-2 rounded-lg bg-[#162032] hover:text-white transition-colors">
                <Github className="w-4 h-4" />
              </a>
              <a href="#" className="p-2 rounded-lg bg-[#162032] hover:text-white transition-colors">
                <Twitter className="w-4 h-4" />
              </a>
              <a href="#" className="p-2 rounded-lg bg-[#162032] hover:text-white transition-colors">
                <Linkedin className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 pt-6 border-t border-[#1F293D]/60 flex flex-col sm:flex-row items-center justify-between text-xs text-gray-400">
          <p>© {new Date().getFullYear()} AI ProjectDNA. All rights reserved.</p>
          <p className="mt-2 sm:mt-0 flex items-center gap-1">
            Engineered with <Heart className="w-3.5 h-3.5 text-rose-500 inline fill-rose-500" /> for researchers & developers.
          </p>
        </div>
      </footer>
    </div>
  );
};

