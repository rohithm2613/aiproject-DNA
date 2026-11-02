import React from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Search,
  Cpu,
  Layers,
  FileText,
  Compass,
  CheckCircle,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="space-y-24 py-12 md:py-20">
      {/* Hero Section */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-purple-900/30 border border-purple-500/30 text-purple-300 text-xs font-mono tracking-wide">
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span>PHASE 1 FOUNDATION &middot; INTELLIGENT INNOVATION PLATFORM</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-tight font-sans">
          Turn Your Ideas Into{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-indigo-300 to-cyan-400">
            Innovation.
          </span>
        </h1>

        <p className="max-w-2xl mx-auto text-base sm:text-xl text-gray-300 leading-relaxed font-normal">
          AI ProjectDNA empowers students, academic researchers, and startup founders to validate
          project ideas, discover prior art, uncover research gaps, and accelerate breakthroughs.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            to="/new-project"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white font-semibold text-base shadow-glow-purple transition-all duration-200"
          >
            Get Started
            <ArrowRight className="w-5 h-5" />
          </Link>
          <Link
            to="/dashboard"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-[#111827] hover:bg-[#1A2234] text-gray-200 border border-[#232E47] font-semibold text-base transition-colors"
          >
            Explore Dashboard
          </Link>
        </div>

        {/* Feature badges row */}
        <div className="pt-6 flex flex-wrap items-center justify-center gap-6 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            PostgreSQL & FastAPI Backbone
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-cyan-400" />
            AI & RAG-Ready Architecture
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-purple-400" />
            Prior Art & Gap Identification
          </span>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-3">
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Designed for Rigorous Project Validation
          </h2>
          <p className="text-gray-400 text-sm max-w-xl mx-auto">
            A purpose-built suite of validation tools designed to turn vague concepts into defensible, high-impact innovations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="dna-card p-6 space-y-4 hover:border-purple-500/40">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white">Idea Feasibility Validation</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Structure technical scopes, evaluate domain complexity, and assess core implementation feasibility before writing code.
            </p>
          </div>

          <div className="dna-card p-6 space-y-4 hover:border-blue-500/40">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Search className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white">Prior Art & Paper Discovery</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Scan across academic publications, open-source repositories, and patents to uncover overlapping work.
            </p>
          </div>

          <div className="dna-card p-6 space-y-4 hover:border-cyan-500/40">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Compass className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white">Research Gap Detection</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Identify underserved niches, unresolved benchmark problems, and unexplored algorithmic approaches.
            </p>
          </div>

          <div className="dna-card p-6 space-y-4 hover:border-emerald-500/40">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white">Innovation Opportunities</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Generate actionable recommendations for novel architectural layers, unique datasets, and key technical differentiators.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-3">
          <span className="text-xs uppercase font-mono tracking-widest text-cyan-400">
            System Workflow
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            How AI ProjectDNA Works
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          <div className="dna-card p-6 space-y-4 relative">
            <span className="text-4xl font-extrabold text-[#232E47] font-mono absolute top-4 right-4">
              01
            </span>
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white">Define Idea & Domain</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Enter your project title, core concept description, chosen domain, target technology stack, and primary objectives.
            </p>
          </div>

          <div className="dna-card p-6 space-y-4 relative">
            <span className="text-4xl font-extrabold text-[#232E47] font-mono absolute top-4 right-4">
              02
            </span>
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white">Cross-Index Prior Art</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              The platform catalog catalogs your project in PostgreSQL with structured metadata, primed for vector embeddings and multi-source research searches.
            </p>
          </div>

          <div className="dna-card p-6 space-y-4 relative">
            <span className="text-4xl font-extrabold text-[#232E47] font-mono absolute top-4 right-4">
              03
            </span>
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-white">Generate DNA Report</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Receive a comprehensive validation dossier breaking down originality scores, related literature, and strategic avenues for breakthrough impact.
            </p>
          </div>
        </div>
      </section>

      {/* Call to Action Bar */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="p-8 sm:p-12 rounded-2xl bg-gradient-to-r from-purple-900/30 via-slate-900 to-cyan-900/30 border border-[#232E47] text-center space-y-6">
          <h2 className="text-2xl sm:text-4xl font-bold text-white tracking-tight">
            Ready to test your project DNA?
          </h2>
          <p className="text-gray-300 text-sm sm:text-base max-w-xl mx-auto">
            Join students and researchers mapping the next generation of intelligent software and applied science.
          </p>
          <div className="pt-2">
            <Link
              to="/new-project"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-sm shadow-glow-purple transition-all"
            >
              Analyze Your First Project
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

