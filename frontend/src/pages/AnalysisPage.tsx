import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Sparkles,
  ArrowLeft,
  RefreshCw,
  Cpu,
  Layers,
  Target,
  Users,
  AlertTriangle,
  FileText,
  CheckCircle2,
  HardDrive,
  Code2,
  Gauge,
  HelpCircle,
  History,
  Copy,
  Check,
  AlertCircle,
  ExternalLink,
  BookOpen,
  Search,
  Unlock,
  Calendar,
  Filter,
  Github,
  GitFork,
  Star,
  Compass,
  Lightbulb,
  Database,
  Cloud,
  GitBranch,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  Sliders,
  Binary,
  Fingerprint,
  FileCheck2,
  Scale,
  ShieldCheck,
} from 'lucide-react';
import { analysisService } from '../services/analysisService';
import { projectService } from '../services/projectService';
import { researchService } from '../services/researchService';
import { githubService } from '../services/githubService';
import { repositoryAnalysisService } from '../services/repositoryAnalysisService';
import { embeddingService } from '../services/embeddingService';
import { ProjectAnalysis, ProjectAnalysisListResponse } from '../types/analysis';
import { Project } from '../types/project';
import { ResearchPaper, ResearchStatsResponse } from '../types/research';
import { GitHubRepository, GitHubStatsResponse, GitHubRateLimitInfo } from '../types/github';
import {
  RepositoryAnalysis,
  InnovationGap,
  RepositoryAnalysisStats,
} from '../types/repositoryAnalysis';
import {
  SemanticMatchItem,
  SimilarityStatsResponse,
} from '../types/embedding';
import {
  ValidationReportResponse,
  ValidationHistoryResponse,
} from '../types/validation';
import { validationService } from '../services/validationService';
import {
  Patent,
  PatentStatsResponse,
  PatentAnalysisResponse,
  PriorArtAnalysisItem,
} from '../types/patent';
import { patentService } from '../services/patentService';


export const AnalysisPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  const [project, setProject] = useState<Project | null>(null);
  const [analysis, setAnalysis] = useState<ProjectAnalysis | null>(null);
  const [history, setHistory] = useState<ProjectAnalysisListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisStep, setAnalysisStep] = useState<string>('Initializing analysis session...');
  const [error, setError] = useState<string | null>(null);
  const [copiedKeyword, setCopiedKeyword] = useState<string | null>(null);

  // Research Discovery State (Phase 4.1)
  const [researchPapers, setResearchPapers] = useState<ResearchPaper[]>([]);
  const [researchTotal, setResearchTotal] = useState<number>(0);
  const [researchStats, setResearchStats] = useState<ResearchStatsResponse | null>(null);
  const [researchLoading, setResearchLoading] = useState<boolean>(false);
  const [researchSearching, setResearchSearching] = useState<boolean>(false);
  const [researchError, setResearchError] = useState<string | null>(null);
  const [providerErrors, setProviderErrors] = useState<Record<string, string>>({});
  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const [selectedYear, setSelectedYear] = useState<string>('all');
  const [openAccessOnly, setOpenAccessOnly] = useState<boolean>(false);
  const [searchFilterKeyword, setSearchFilterKeyword] = useState<string>('');
  const [researchPage, setResearchPage] = useState<number>(1);
  const [expandedAbstracts, setExpandedAbstracts] = useState<Record<string, boolean>>({});

  const loadResearch = async (
    page = 1,
    provider = selectedProvider,
    year = selectedYear,
    oaOnly = openAccessOnly,
    kw = searchFilterKeyword
  ) => {
    if (!projectId) return;
    setResearchLoading(true);
    try {
      try {
        const stats = await researchService.getResearchStats(projectId);
        setResearchStats(stats);
      } catch {
        // Non-fatal
      }

      const params: any = {
        page,
        page_size: 10,
      };
      if (provider !== 'all') params.provider = provider;
      if (year !== 'all') params.year = parseInt(year, 10);
      if (oaOnly) params.open_access = true;
      if (kw.trim()) params.search = kw.trim();

      const res = await researchService.getStoredPapers(projectId, params);
      setResearchPapers(res.items);
      setResearchTotal(res.total);
      setResearchPage(page);
    } catch (err: any) {
      console.warn('Failed to load research papers:', err);
    } finally {
      setResearchLoading(false);
    }
  };

  const handleSearchResearch = async () => {
    if (!projectId) return;
    setResearchSearching(true);
    setResearchError(null);
    setProviderErrors({});

    try {
      const resp = await researchService.searchResearchPapers(projectId, {
        analysis_id: analysis?.id,
        max_results: 20,
      });

      if (resp.provider_errors && Object.keys(resp.provider_errors).length > 0) {
        setProviderErrors(resp.provider_errors);
      }

      await loadResearch(1, selectedProvider, selectedYear, openAccessOnly, searchFilterKeyword);
    } catch (err: any) {
      console.error('Research search error:', err);
      setResearchError(
        err.response?.data?.detail || 'Academic research search failed. Please try again.'
      );
    } finally {
      setResearchSearching(false);
    }
  };

  const toggleAbstract = (paperId: string) => {
    setExpandedAbstracts((prev) => ({
      ...prev,
      [paperId]: !prev[paperId],
    }));
  };

  // GitHub Discovery State (Phase 4.2)
  const [githubRepos, setGithubRepos] = useState<GitHubRepository[]>([]);
  const [githubTotal, setGithubTotal] = useState<number>(0);
  const [githubStats, setGithubStats] = useState<GitHubStatsResponse | null>(null);
  const [githubLoading, setGithubLoading] = useState<boolean>(false);
  const [githubSearching, setGithubSearching] = useState<boolean>(false);
  const [githubError, setGithubError] = useState<string | null>(null);
  const [githubRateLimit, setGithubRateLimit] = useState<GitHubRateLimitInfo | null>(null);
  const [githubErrors, setGithubErrors] = useState<Record<string, string>>({});
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [selectedMinStars, setSelectedMinStars] = useState<number>(0);
  const [includeArchived, setIncludeArchived] = useState<boolean>(false);
  const [includeForks, setIncludeForks] = useState<boolean>(false);
  const [githubSearchKeyword, setGithubSearchKeyword] = useState<string>('');
  const [githubSortBy, setGithubSortBy] = useState<string>('stars');
  const [githubPage, setGithubPage] = useState<number>(1);

  const loadGitHub = async (
    page = 1,
    lang = selectedLanguage,
    minStars = selectedMinStars,
    archived = includeArchived,
    fork = includeForks,
    kw = githubSearchKeyword,
    sortBy = githubSortBy
  ) => {
    if (!projectId) return;
    setGithubLoading(true);
    try {
      try {
        const stats = await githubService.getRepositoryStats(projectId);
        setGithubStats(stats);
      } catch {
        // Non-fatal if stats query fails
      }

      const params: any = {
        page,
        page_size: 10,
        sort_by: sortBy,
        sort_order: 'desc',
      };
      if (lang !== 'all') params.language = lang;
      if (minStars > 0) params.min_stars = minStars;
      if (archived) params.archived = true;
      if (fork) params.fork = true;
      if (kw.trim()) params.search = kw.trim();

      const res = await githubService.getStoredRepositories(projectId, params);
      setGithubRepos(res.items);
      setGithubTotal(res.total);
      setGithubPage(page);
    } catch (err: any) {
      console.warn('Failed to load GitHub repositories:', err);
    } finally {
      setGithubLoading(false);
    }
  };

  const handleSearchGitHub = async () => {
    if (!projectId) return;
    setGithubSearching(true);
    setGithubError(null);
    setGithubErrors({});

    try {
      const resp = await githubService.searchGitHubRepositories(projectId, {
        analysis_id: analysis?.id,
        max_results: 30,
        sort: githubSortBy,
        order: 'desc',
      });

      if (resp.rate_limit) {
        setGithubRateLimit(resp.rate_limit);
      }
      if (resp.errors && Object.keys(resp.errors).length > 0) {
        setGithubErrors(resp.errors);
      }

      await loadGitHub(1, selectedLanguage, selectedMinStars, includeArchived, includeForks, githubSearchKeyword, githubSortBy);
    } catch (err: any) {
      console.error('GitHub search error:', err);
      setGithubError(
        err.response?.data?.detail || 'GitHub repository discovery failed. Please try again.'
      );
    } finally {
      setGithubSearching(false);
    }
  };

  // GitHub Deep Analysis & Innovation Gaps State (Phase 4.3)
  const [repoAnalyses, setRepoAnalyses] = useState<RepositoryAnalysis[]>([]);
  const [repoAnalysesTotal, setRepoAnalysesTotal] = useState<number>(0);
  const [repoAnalysesPage, setRepoAnalysesPage] = useState<number>(1);
  const [repoAnalysesLoading, setRepoAnalysesLoading] = useState<boolean>(false);
  const [repoAnalyzing, setRepoAnalyzing] = useState<boolean>(false);
  const [repoAnalysisError, setRepoAnalysisError] = useState<string | null>(null);
  const [repoAnalysisBatchErrors, setRepoAnalysisBatchErrors] = useState<Record<string, string>>({});
  const [repoAnalysisMode, setRepoAnalysisMode] = useState<string>('ai_enhanced');

  const [innovationGaps, setInnovationGaps] = useState<InnovationGap[]>([]);
  const [selectedGapPriority, setSelectedGapPriority] = useState<string>('all');
  const [selectedGapCategory, setSelectedGapCategory] = useState<string>('all');
  const [repoAnalysisStats, setRepoAnalysisStats] = useState<RepositoryAnalysisStats | null>(null);
  const [expandedRepoAnalyses, setExpandedRepoAnalyses] = useState<Record<string, boolean>>({});
  const [expandedArchitecture, setExpandedArchitecture] = useState<Record<string, boolean>>({});

  const toggleRepoExpand = (repoId: string) => {
    setExpandedRepoAnalyses((prev) => ({
      ...prev,
      [repoId]: !prev[repoId],
    }));
  };

  const toggleArchitectureExpand = (repoId: string) => {
    setExpandedArchitecture((prev) => ({
      ...prev,
      [repoId]: !prev[repoId],
    }));
  };

  const loadRepoAnalyses = async (page = 1) => {
    if (!projectId) return;
    setRepoAnalysesLoading(true);
    try {
      const res = await repositoryAnalysisService.getStoredAnalyses(projectId, page, 10);
      setRepoAnalyses(res.items);
      setRepoAnalysesTotal(res.total);
      setRepoAnalysesPage(page);
    } catch (err: any) {
      console.warn('Failed to load repository analyses:', err);
    } finally {
      setRepoAnalysesLoading(false);
    }
  };

  const loadInnovationGaps = async (priority = selectedGapPriority, category = selectedGapCategory) => {
    if (!projectId) return;
    try {
      const p = priority !== 'all' ? priority : undefined;
      const c = category !== 'all' ? category : undefined;
      const res = await repositoryAnalysisService.getInnovationGaps(projectId, p, c);
      setInnovationGaps(res.items);
    } catch (err: any) {
      console.warn('Failed to load innovation gaps:', err);
    }
  };

  const loadRepoAnalysisStats = async () => {
    if (!projectId) return;
    try {
      const stats = await repositoryAnalysisService.getAnalysisStats(projectId);
      setRepoAnalysisStats(stats);
    } catch (err: any) {
      console.warn('Failed to load repository analysis stats:', err);
    }
  };

  // Semantic Embedding & Cross-Source Similarity State (Phase 4.4)
  const [similarityMatches, setSimilarityMatches] = useState<SemanticMatchItem[]>([]);
  const [similarityTotal, setSimilarityTotal] = useState<number>(0);
  const [similarityStats, setSimilarityStats] = useState<SimilarityStatsResponse | null>(null);
  const [similarityDisclaimer, setSimilarityDisclaimer] = useState<string>('');
  const [similarityLoading, setSimilarityLoading] = useState<boolean>(false);
  const [embeddingGenerating, setEmbeddingGenerating] = useState<boolean>(false);
  const [similarityError, setSimilarityError] = useState<string | null>(null);
  const [similaritySourceFilter, setSimilaritySourceFilter] = useState<string>('all');
  const [similarityMinThreshold, setSimilarityMinThreshold] = useState<number>(0);

  const loadSimilarityData = async (
    sourceType = similaritySourceFilter,
    minSim = similarityMinThreshold
  ) => {
    if (!projectId) return;
    setSimilarityLoading(true);
    setSimilarityError(null);
    try {
      try {
        const stats = await embeddingService.getSimilarityStats(projectId);
        setSimilarityStats(stats);
      } catch {
        // Non-fatal if stats query fails
      }

      const simRes = await embeddingService.getSemanticSimilarities(projectId, {
        source_type: sourceType,
        min_similarity: minSim > 0 ? minSim / 100 : undefined,
        limit: 50,
      });

      setSimilarityMatches(simRes.matches || []);
      setSimilarityTotal(simRes.total_matches || 0);
      setSimilarityDisclaimer(simRes.disclaimer || '');
    } catch (err: any) {
      console.warn('Failed to load semantic similarities:', err);
      if (err.response?.data?.detail) {
        setSimilarityError(err.response.data.detail);
      }
    } finally {
      setSimilarityLoading(false);
    }
  };

  const handleGenerateEmbeddings = async (forceRegenerate: boolean = false) => {
    if (!projectId) return;
    setEmbeddingGenerating(true);
    setSimilarityError(null);
    try {
      await embeddingService.generateEmbeddings(projectId, {
        force_regenerate: forceRegenerate,
        include_papers: true,
        include_repos: true,
      });
      await loadSimilarityData(similaritySourceFilter, similarityMinThreshold);
    } catch (err: any) {
      console.error('Embedding generation failed:', err);
      setSimilarityError(
        err.response?.data?.detail || 'Failed to generate vector embeddings. Please try again.'
      );
    } finally {
      setEmbeddingGenerating(false);
    }
  };

  const handleDeepAnalyze = async () => {
    if (!projectId) return;
    setRepoAnalyzing(true);
    setRepoAnalysisError(null);
    setRepoAnalysisBatchErrors({});

    try {
      const resp = await repositoryAnalysisService.analyzeRepositories(projectId, {
        max_repositories: 10,
        force_refresh: true,
      });

      setRepoAnalysisMode(resp.analysis_mode);
      if (resp.errors && Object.keys(resp.errors).length > 0) {
        setRepoAnalysisBatchErrors(resp.errors);
      }

      await Promise.all([
        loadRepoAnalyses(1),
        loadInnovationGaps(selectedGapPriority, selectedGapCategory),
        loadRepoAnalysisStats(),
      ]);
    } catch (err: any) {
      console.error('Repository deep analysis error:', err);
      setRepoAnalysisError(
        err.response?.data?.detail || 'Repository deep analysis failed. Please try again.'
      );
    } finally {
      setRepoAnalyzing(false);
    }
  };

  // Fetch project details and latest analysis

  // RAG Research Gap Validation State (Phase 4.5)
  const [validationReport, setValidationReport] = useState<ValidationReportResponse | null>(null);
  const [validationHistory, setValidationHistory] = useState<ValidationHistoryResponse | null>(null);
  const [validationLoading, setValidationLoading] = useState<boolean>(false);
  const [validationGenerating, setValidationGenerating] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [selectedValidationVersion, setSelectedValidationVersion] = useState<number | null>(null);
  const [evidenceModalOpen, setEvidenceModalOpen] = useState<boolean>(false);
  const [evidenceFilterType, setEvidenceFilterType] = useState<string>('all');
  const [activeReportTab, setActiveReportTab] = useState<string>('gaps');
  const [gapFilterStatus, setGapFilterStatus] = useState<string>('all');
  const [copiedValidationReport, setCopiedValidationReport] = useState<boolean>(false);

  const loadValidationData = async (versionOverride?: number) => {
    if (!projectId) return;
    setValidationLoading(true);
    setValidationError(null);
    try {
      try {
        const hist = await validationService.getValidationHistory(projectId);
        setValidationHistory(hist);
      } catch {
        // Non-fatal if history is empty
      }

      let report: ValidationReportResponse | null = null;
      if (versionOverride && validationHistory?.reports) {
        const target = validationHistory.reports.find((r) => r.version === versionOverride);
        if (target) {
          report = await validationService.getValidationReportById(projectId, target.id);
        }
      }
      if (!report) {
        try {
          report = await validationService.getLatestValidationReport(projectId);
        } catch (err: any) {
          if (err.response?.status === 404) {
            report = null;
          } else {
            throw err;
          }
        }
      }
      setValidationReport(report);
      if (report) {
        setSelectedValidationVersion(report.version);
      }
    } catch (err: any) {
      console.warn('Failed to load validation report:', err);
      if (err.response?.data?.detail) {
        setValidationError(err.response.data.detail);
      }
    } finally {
      setValidationLoading(false);
    }
  };

  const handleGenerateValidationReport = async (forceRegenerate: boolean = true) => {
    if (!projectId) return;
    setValidationGenerating(true);
    setValidationError(null);
    try {
      const resp = await validationService.generateValidationReport(projectId, {
        force_regenerate: forceRegenerate,
        max_papers: 15,
        max_repos: 15,
        max_gaps: 20,
        include_embeddings: true,
      });
      setValidationReport(resp);
      setSelectedValidationVersion(resp.version);
      // Reload history
      try {
        const hist = await validationService.getValidationHistory(projectId);
        setValidationHistory(hist);
      } catch {}
    } catch (err: any) {
      console.error('Validation report generation failed:', err);
      setValidationError(
        err.response?.data?.detail || 'Failed to generate RAG validation report. Please try again.'
      );
    } finally {
      setValidationGenerating(false);
    }
  };

  const handleCopyValidationReport = () => {
    if (!validationReport) return;
    const rep = validationReport.report;
    const text = `# Project Validation Dossier: ${rep.project_overview.project_title} (v${validationReport.version})\n\n` +
      `## Executive Summary\n${rep.final_assessment.existing_work_summary}\n\n` +
      `## Validated Research Gaps\n${rep.validated_research_gaps.gap_validation_summary}\n\n` +
      `## Novelty Caveat\n${rep.final_assessment.explicit_novelty_limitation}`;
    navigator.clipboard.writeText(text);
    setCopiedValidationReport(true);
    setTimeout(() => setCopiedValidationReport(false), 2000);
  };

  // Patent & Prior-Art Discovery Engine State (Phase 4.6)
  const [patents, setPatents] = useState<Patent[]>([]);
  const [patentTotal, setPatentTotal] = useState<number>(0);
  const [patentPage, setPatentPage] = useState<number>(1);
  const [patentStats, setPatentStats] = useState<PatentStatsResponse | null>(null);
  const [patentLoading, setPatentLoading] = useState<boolean>(false);
  const [patentSearching, setPatentSearching] = useState<boolean>(false);
  const [patentSearchError, setPatentSearchError] = useState<string | null>(null);
  const [patentJurisdiction, setPatentJurisdiction] = useState<string>('all');
  const [patentProvider, setPatentProvider] = useState<string>('all');
  const [patentSortBy, setPatentSortBy] = useState<'similarity' | 'publication_date' | 'created_at'>('similarity');
  const [patentSearchQuery, setPatentSearchQuery] = useState<string>('');
  const [selectedPatentPriorArt, setSelectedPatentPriorArt] = useState<PriorArtAnalysisItem | null>(null);
  const [patentAnalysis, setPatentAnalysis] = useState<PatentAnalysisResponse | null>(null);
  const [patentAnalyzing, setPatentAnalyzing] = useState<boolean>(false);
  const [priorArtModalOpen, setPriorArtModalOpen] = useState<boolean>(false);
  const [expandedPatentAbstracts, setExpandedPatentAbstracts] = useState<Record<string, boolean>>({});

  const togglePatentAbstract = (id: string) => {
    setExpandedPatentAbstracts((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const loadPatents = async (
    page = 1,
    jur = patentJurisdiction,
    prov = patentProvider,
    sort = patentSortBy,
    q = patentSearchQuery
  ) => {
    if (!projectId) return;
    setPatentLoading(true);
    setPatentSearchError(null);
    try {
      const res = await patentService.getPatents(projectId, {
        page,
        page_size: 10,
        jurisdiction: jur !== 'all' ? jur : undefined,
        provider: prov !== 'all' ? prov : undefined,
        search_query: q.trim() ? q.trim() : undefined,
        sort_by: sort,
      });
      setPatents(res.items);
      setPatentTotal(res.total);
      setPatentPage(page);

      try {
        const stats = await patentService.getPatentStats(projectId);
        setPatentStats(stats);
      } catch {}
    } catch (err: any) {
      console.warn('Failed to load patents:', err);
    } finally {
      setPatentLoading(false);
    }
  };

  const handleSearchPatents = async () => {
    if (!projectId) return;
    setPatentSearching(true);
    setPatentSearchError(null);
    try {
      await patentService.searchPatents(projectId, {
        analysis_id: analysis?.id,
        max_results: 25,
        providers: ['uspto', 'epo'],
      });
      await loadPatents(1, patentJurisdiction, patentProvider, patentSortBy, patentSearchQuery);
      try {
        const stats = await patentService.getPatentStats(projectId);
        setPatentStats(stats);
      } catch {}
    } catch (err: any) {
      console.error('Patent search error:', err);
      setPatentSearchError(
        err.response?.data?.detail || 'Patent discovery search failed. Please try again.'
      );
    } finally {
      setPatentSearching(false);
    }
  };

  const handleAnalyzePriorArt = async (patentIds?: string[]) => {
    if (!projectId) return;
    setPatentAnalyzing(true);
    try {
      const resp = await patentService.analyzePatents(projectId, {
        patent_ids: patentIds,
        max_patents: 10,
      });
      setPatentAnalysis(resp);
      if (patentIds && patentIds.length === 1 && resp.prior_art_analyses.length > 0) {
        setSelectedPatentPriorArt(resp.prior_art_analyses[0]);
        setPriorArtModalOpen(true);
      }
    } catch (err: any) {
      console.error('Prior-art analysis failed:', err);
    } finally {
      setPatentAnalyzing(false);
    }
  };

  const handleOpenSinglePriorArt = async (pat: Patent) => {
    if (patentAnalysis?.prior_art_analyses) {
      const existing = patentAnalysis.prior_art_analyses.find(
        (a) => a.patent_id === pat.id || a.publication_number === pat.publication_number
      );
      if (existing) {
        setSelectedPatentPriorArt(existing);
        setPriorArtModalOpen(true);
        return;
      }
    }
    await handleAnalyzePriorArt([pat.id]);
  };

  const loadData = async (selectedVersion?: number) => {
    if (!projectId) return;
    setLoading(true);
    setError(null);

    try {
      // 1. Fetch project
      const proj = await projectService.getProjectById(projectId);
      setProject(proj);

      // 2. Fetch analysis history
      try {
        const hist = await analysisService.getAnalysisHistory(projectId);
        setHistory(hist);
      } catch {
        setHistory(null);
      }

      // 3. Fetch specific or latest analysis
      try {
        const res = await analysisService.getLatestAnalysis(projectId, selectedVersion);
        setAnalysis(res);
      } catch (err: any) {
        if (err.response?.status === 404) {
          // No analysis exists yet; prompt user to trigger one
          setAnalysis(null);
        } else {
          throw err;
        }
      }

      // 4. Load research discovery, GitHub repositories, deep analyses, and innovation gaps
      loadResearch(1);
      loadGitHub(1);
      loadRepoAnalyses(1);
      loadInnovationGaps();
      loadRepoAnalysisStats();
      loadSimilarityData();
      loadValidationData();
      loadPatents(1);
    } catch (err: any) {
      console.error('Error loading project/analysis:', err);
      setError(
        err.response?.data?.detail ||
        'Failed to load project analysis. Please verify your connection or try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  // Trigger Gemini AI analysis run
  const handleRunAnalysis = async () => {
    if (!projectId) return;
    setAnalyzing(true);
    setError(null);

    const steps = [
      'Connecting to Google Gemini API...',
      'Deconstructing problem statement & architectural scope...',
      'Mapping domain taxonomy & technical keywords...',
      'Synthesizing hardware, software & dataset constraints...',
      'Validating structured Pydantic analysis schema...',
      'Finalizing analysis dossier and synchronizing database...',
    ];

    let stepIndex = 0;
    setAnalysisStep(steps[0]);
    const interval = setInterval(() => {
      stepIndex = (stepIndex + 1) % steps.length;
      setAnalysisStep(steps[stepIndex]);
    }, 2200);

    try {
      const newAnalysis = await analysisService.analyzeProject(projectId);
      setAnalysis(newAnalysis);

      // Refresh history & project status
      const hist = await analysisService.getAnalysisHistory(projectId);
      setHistory(hist);
      const updatedProject = await projectService.getProjectById(projectId);
      setProject(updatedProject);
    } catch (err: any) {
      console.error('Analysis failed:', err);
      const msg =
        err.response?.data?.detail ||
        'AI idea analysis failed. Please verify that GEMINI_API_KEY is configured in backend environment variables.';
      setError(msg);
    } finally {
      clearInterval(interval);
      setAnalyzing(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKeyword(text);
    setTimeout(() => setCopiedKeyword(null), 2000);
  };

  // Difficulty badge colors
  const getDifficultyColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'beginner':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'intermediate':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
      case 'advanced':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'expert':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-gray-500/10 text-gray-400 border-gray-500/30';
    }
  };

  if (loading) {
    return (
      <div className="dna-card p-12 text-center text-gray-400 animate-pulse my-8">
        Loading AI analysis dossier...
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Navigation & Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Link
            to="/projects"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Projects Catalog
          </Link>

          {/* Version Switcher if multiple runs exist */}
          {history && history.total_versions > 1 && (
            <div className="flex items-center gap-2">
              <History className="w-3.5 h-3.5 text-purple-400" />
              <span className="text-xs text-gray-400 font-mono">Version:</span>
              <select
                value={analysis?.version || history.total_versions}
                onChange={(e) => loadData(Number(e.target.value))}
                className="dna-input text-xs py-1 px-2.5 bg-[#111827] cursor-pointer"
              >
                {history.analyses.map((h) => (
                  <option key={h.id} value={h.version} className="bg-[#111827]">
                    v{h.version} ({new Date(h.created_at).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#1F293D] pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded text-xs font-mono uppercase tracking-wider bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                AI ProjectDNA Intelligence Report
              </span>
              {analysis && (
                <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/20">
                  Version {analysis.version}
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              {project?.title || 'Project Idea Analysis'}
            </h1>
            <p className="text-xs text-gray-400 mt-1 font-mono">
              Analyzed with {analysis?.model_name || 'Google Gemini API'} &bull;{' '}
              {analysis ? new Date(analysis.created_at).toLocaleString() : 'Not yet analyzed'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white font-medium text-xs shadow-glow-purple disabled:opacity-50 transition-all duration-200"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? 'Analyzing with Gemini...' : analysis ? 'Re-Analyze Idea' : 'Start AI Analysis'}
            </button>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-400" />
          <div className="space-y-1">
            <p className="font-semibold text-rose-200">Analysis Error Encountered</p>
            <p className="leading-relaxed">{error}</p>
            <p className="text-[11px] text-gray-400 font-mono pt-1">
              Tip: Ensure a valid Google Gemini API key is configured in backend environment variables.
            </p>
          </div>
        </div>
      )}

      {/* Analyzing Progress State */}
      {analyzing && (
        <div className="dna-card p-10 text-center space-y-4 border-purple-500/40 shadow-glow-purple">
          <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center mx-auto animate-pulse">
            <Sparkles className="w-7 h-7" />
          </div>
          <div className="space-y-1.5">
            <h3 className="text-base font-semibold text-white">
              Google Gemini is Analyzing Your Project Idea
            </h3>
            <p className="text-xs text-purple-300 font-mono animate-in fade-in">
              {analysisStep}
            </p>
          </div>
          <div className="w-48 h-1 bg-[#162032] rounded-full mx-auto overflow-hidden">
            <div className="w-full h-full bg-gradient-to-r from-purple-500 to-cyan-400 animate-pulse rounded-full" />
          </div>
        </div>
      )}

      {/* Empty State if Not Yet Analyzed */}
      {!analysis && !analyzing && (
        <div className="dna-card p-12 text-center space-y-5 border-dashed border-[#232E47]">
          <div className="w-14 h-14 rounded-2xl bg-[#162032] border border-[#232E47] text-gray-400 flex items-center justify-center mx-auto">
            <Sparkles className="w-7 h-7 text-purple-400" />
          </div>
          <div className="space-y-1.5 max-w-md mx-auto">
            <h3 className="text-lg font-bold text-white">No Analysis Dossier Generated Yet</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Submit this project to the Google Gemini AI Analyzer to extract domain taxonomy,
              structured problem definitions, recommended technical stacks, and objective KPIs.
            </p>
          </div>
          <button
            onClick={handleRunAnalysis}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs shadow-glow-purple transition-all"
          >
            <Sparkles className="w-4 h-4" />
            Generate Initial AI Analysis
          </button>
        </div>
      )}

      {/* Full Analysis Content */}
      {analysis && !analyzing && (
        <div className="space-y-8 animate-in fade-in duration-300">
          {/* Top Quick Attributes Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="dna-card p-4 flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[11px] font-mono uppercase text-gray-400">Primary Domain</p>
                <p className="text-sm font-semibold text-white mt-0.5">{analysis.primary_domain}</p>
              </div>
            </div>

            <div className="dna-card p-4 flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                <Code2 className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[11px] font-mono uppercase text-gray-400">Classification</p>
                <p className="text-sm font-semibold text-white mt-0.5">{analysis.project_type}</p>
              </div>
            </div>

            <div className="dna-card p-4 flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Gauge className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[11px] font-mono uppercase text-gray-400">Difficulty Level</p>
                <span className={`inline-block mt-0.5 px-2.5 py-0.5 rounded text-xs font-mono font-medium border ${getDifficultyColor(analysis.difficulty_level)}`}>
                  {analysis.difficulty_level}
                </span>
              </div>
            </div>
          </div>

          {/* 12. Academic Research Discovery (Phase 4.1) */}
          <div className="dna-card p-6 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1F293D] pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold text-white">12. Academic Research Discovery</h2>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                      Phase 4.1
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Discover verified research literature matching this idea across arXiv, Semantic Scholar, and OpenAlex
                  </p>
                </div>
              </div>

              <button
                onClick={handleSearchResearch}
                disabled={researchSearching}
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <RefreshCw className={`w-4 h-4 ${researchSearching ? 'animate-spin' : ''}`} />
                {researchSearching ? 'Searching Repositories...' : 'Search Research Papers'}
              </button>
            </div>

            {/* Provider in-progress banner */}
            {researchSearching && (
              <div className="p-4 rounded-xl bg-blue-950/30 border border-blue-500/30 flex items-center gap-3 animate-pulse">
                <RefreshCw className="w-5 h-5 text-cyan-400 animate-spin flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-cyan-200">
                    Querying arXiv, Semantic Scholar, and OpenAlex simultaneously...
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Synthesizing queries from problem statement, keywords, and technical domain...
                  </p>
                </div>
              </div>
            )}

            {/* Provider Warnings Banner */}
            {Object.keys(providerErrors).length > 0 && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs space-y-1">
                  <p className="font-semibold text-amber-300">
                    Notice: Some academic providers encountered rate limits or service timeouts
                  </p>
                  <ul className="list-disc list-inside text-gray-300 space-y-0.5">
                    {Object.entries(providerErrors).map(([prov, msg]) => (
                      <li key={prov}>
                        <span className="font-mono capitalize font-medium text-amber-200">{prov.replace('_', ' ')}</span>: {msg}
                      </li>
                    ))}
                  </ul>
                  <p className="text-[11px] text-gray-400">
                    Results from remaining operational repositories are safely preserved below.
                  </p>
                </div>
              </div>
            )}

            {/* General Research Error */}
            {researchError && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-300 text-xs">
                <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
                <span>{researchError}</span>
              </div>
            )}

            {/* Discovery Stats Bar */}
            {researchStats && researchStats.total_papers > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-gray-400 font-medium">Total Papers</span>
                  <span className="text-xl font-bold text-white mt-1">{researchStats.total_papers}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-rose-300 font-medium">arXiv</span>
                  <span className="text-xl font-bold text-rose-400 mt-1">{researchStats.by_provider.arxiv || 0}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-sky-300 font-medium">Semantic Scholar</span>
                  <span className="text-xl font-bold text-sky-400 mt-1">{researchStats.by_provider.semantic_scholar || 0}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-emerald-300 font-medium">OpenAlex</span>
                  <span className="text-xl font-bold text-emerald-400 mt-1">{researchStats.by_provider.openalex || 0}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-teal-300 font-medium">Open Access</span>
                  <span className="text-xl font-bold text-teal-400 mt-1">{researchStats.open_access_count}</span>
                </div>
              </div>
            )}

            {/* Filters Bar */}
            <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                {/* Provider Filter Pills */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-xs text-gray-400 font-medium mr-1 flex items-center gap-1">
                    <Filter className="w-3.5 h-3.5" /> Provider:
                  </span>
                  {[
                    { id: 'all', label: 'All Sources' },
                    { id: 'arxiv', label: 'arXiv' },
                    { id: 'semantic_scholar', label: 'Semantic Scholar' },
                    { id: 'openalex', label: 'OpenAlex' },
                  ].map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        setSelectedProvider(p.id);
                        loadResearch(1, p.id, selectedYear, openAccessOnly, searchFilterKeyword);
                      }}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        selectedProvider === p.id
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-[#151D30] text-gray-400 hover:text-white border border-[#1F293D]'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>

                {/* Right filters: Year & Open Access Toggle */}
                <div className="flex items-center gap-3 flex-wrap">
                  {/* Year Select */}
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-gray-400" />
                    <select
                      value={selectedYear}
                      onChange={(e) => {
                        setSelectedYear(e.target.value);
                        loadResearch(1, selectedProvider, e.target.value, openAccessOnly, searchFilterKeyword);
                      }}
                      className="bg-[#151D30] border border-[#1F293D] text-gray-300 text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:border-blue-500"
                    >
                      <option value="all">All Years</option>
                      {researchStats &&
                        Object.keys(researchStats.year_distribution || {})
                          .sort((a, b) => parseInt(b) - parseInt(a))
                          .map((yr) => (
                            <option key={yr} value={yr}>
                              {yr} ({researchStats.year_distribution[yr]})
                            </option>
                          ))}
                    </select>
                  </div>

                  {/* Open Access Toggle */}
                  <button
                    onClick={() => {
                      const next = !openAccessOnly;
                      setOpenAccessOnly(next);
                      loadResearch(1, selectedProvider, selectedYear, next, searchFilterKeyword);
                    }}
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                      openAccessOnly
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-[#151D30] text-gray-400 border-[#1F293D] hover:text-white'
                    }`}
                  >
                    <Unlock className="w-3.5 h-3.5" />
                    <span>Open Access Only</span>
                  </button>
                </div>
              </div>

              {/* Text Search Input */}
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Filter papers by title, abstract, author, or venue..."
                  value={searchFilterKeyword}
                  onChange={(e) => {
                    setSearchFilterKeyword(e.target.value);
                    loadResearch(1, selectedProvider, selectedYear, openAccessOnly, e.target.value);
                  }}
                  className="w-full bg-[#151D30] border border-[#1F293D] rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Papers List */}
            {researchLoading && !researchSearching ? (
              <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
                <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
                <p className="text-xs text-gray-400">Loading stored research papers...</p>
              </div>
            ) : researchPapers.length === 0 ? (
              <div className="py-12 px-4 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col items-center justify-center text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <BookOpen className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-white">No Research Papers Discovered Yet</h3>
                <p className="text-xs text-gray-400 max-w-md">
                  Click the "Search Research Papers" button to automatically retrieve academic papers matching this project's problem statement and technical architecture from arXiv, Semantic Scholar, and OpenAlex.
                </p>
                <button
                  onClick={handleSearchResearch}
                  disabled={researchSearching}
                  className="mt-2 flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md transition-all"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${researchSearching ? 'animate-spin' : ''}`} />
                  Discover Papers Now
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {researchPapers.map((paper) => {
                  const isExpanded = !!expandedAbstracts[paper.id];
                  const providerStyles =
                    paper.provider === 'arxiv'
                      ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                      : paper.provider === 'semantic_scholar'
                      ? 'bg-sky-500/10 text-sky-300 border-sky-500/30'
                      : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';

                  const providerLabel =
                    paper.provider === 'arxiv'
                      ? 'arXiv'
                      : paper.provider === 'semantic_scholar'
                      ? 'Semantic Scholar'
                      : 'OpenAlex';

                  return (
                    <div
                      key={paper.id}
                      className="p-5 rounded-xl bg-[#0E1424] border border-[#1F293D] hover:border-indigo-500/40 transition-all space-y-3"
                    >
                      {/* Paper Top Badges Row */}
                      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px]">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`px-2 py-0.5 rounded-md font-mono font-medium border ${providerStyles}`}>
                            {providerLabel}
                          </span>

                          {paper.open_access && (
                            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md font-mono bg-teal-500/10 text-teal-300 border border-teal-500/30">
                              <Unlock className="w-3 h-3" />
                              Open Access
                            </span>
                          )}

                          {paper.citation_count !== null && paper.citation_count !== undefined && (
                            <span className="px-2 py-0.5 rounded-md font-mono bg-purple-500/10 text-purple-300 border border-purple-500/30">
                              {paper.citation_count} citations
                            </span>
                          )}

                          {paper.primary_category && (
                            <span className="px-2 py-0.5 rounded-md font-mono bg-gray-500/10 text-gray-400 border border-gray-500/30">
                              {paper.primary_category}
                            </span>
                          )}
                        </div>

                        {(paper.publication_year || paper.publication_date) && (
                          <span className="text-gray-400 font-mono flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {paper.publication_date || paper.publication_year}
                          </span>
                        )}
                      </div>

                      {/* Paper Title */}
                      <div>
                        {paper.paper_url ? (
                          <a
                            href={paper.paper_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-semibold text-white hover:text-blue-400 inline-flex items-center gap-1.5 transition-colors group"
                          >
                            <span>{paper.title}</span>
                            <ExternalLink className="w-3.5 h-3.5 text-gray-500 group-hover:text-blue-400 flex-shrink-0" />
                          </a>
                        ) : (
                          <h4 className="text-sm font-semibold text-white">{paper.title}</h4>
                        )}
                      </div>

                      {/* Authors and Venue */}
                      <div className="text-xs text-gray-400 space-y-0.5">
                        {paper.authors && paper.authors.length > 0 && (
                          <p>
                            <span className="text-gray-500 font-medium">Authors:</span> {paper.authors.join(', ')}
                          </p>
                        )}
                        {paper.venue && (
                          <p>
                            <span className="text-gray-500 font-medium">Venue:</span> {paper.venue}
                          </p>
                        )}
                      </div>

                      {/* Abstract Preview */}
                      <div className="text-xs text-gray-300 leading-relaxed bg-[#0B0F19] p-3 rounded-lg border border-[#1F293D]/60">
                        {paper.abstract ? (
                          <div>
                            <p>
                              {isExpanded || paper.abstract.length <= 220
                                ? paper.abstract
                                : `${paper.abstract.slice(0, 220)}...`}
                            </p>
                            {paper.abstract.length > 220 && (
                              <button
                                onClick={() => toggleAbstract(paper.id)}
                                className="text-blue-400 hover:text-blue-300 font-medium text-[11px] mt-1.5 focus:outline-none"
                              >
                                {isExpanded ? 'Show less' : 'Read more'}
                              </button>
                            )}
                          </div>
                        ) : (
                          <p className="italic text-gray-500">Abstract not provided in repository index.</p>
                        )}
                      </div>

                      {/* Card Action Links Footer */}
                      <div className="flex flex-wrap items-center gap-3 pt-1 border-t border-[#1F293D]/60 text-xs">
                        {paper.doi && (
                          <a
                            href={`https://doi.org/${paper.doi}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-mono text-[11px]"
                          >
                            <span>DOI: {paper.doi}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}

                        {paper.pdf_url && (
                          <a
                            href={paper.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 border border-blue-500/30 text-[11px] font-medium transition-all"
                          >
                            <FileText className="w-3 h-3" />
                            <span>View PDF</span>
                          </a>
                        )}

                        {paper.arxiv_id && (
                          <span className="text-gray-500 font-mono text-[11px]">
                            arXiv ID: {paper.arxiv_id}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Pagination Controls */}
                <div className="flex items-center justify-between pt-3 border-t border-[#1F293D] text-xs text-gray-400">
                  <span>
                    Showing {(researchPage - 1) * 10 + 1} to {Math.min(researchPage * 10, researchTotal)} of {researchTotal} papers
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => loadResearch(researchPage - 1)}
                      disabled={researchPage <= 1}
                      className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="px-2 font-mono text-gray-300">
                      Page {researchPage} of {Math.max(1, Math.ceil(researchTotal / 10))}
                    </span>
                    <button
                      onClick={() => loadResearch(researchPage + 1)}
                      disabled={researchPage * 10 >= researchTotal}
                      className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ======================================================== */}
          {/* SECTION 14: GitHub Repository Deep Analysis & Innovation Gaps */}
          {/* ======================================================== */}
          <div className="bg-[#111827] border border-[#1F293D] rounded-xl p-6 space-y-6">
            {/* Header & Trigger Action */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#1F293D]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                    <Compass className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">
                    Repository Deep Analysis & Innovation Gaps
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    Phase 4.3
                  </span>
                  {repoAnalysisMode === 'deterministic_fallback' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      Heuristic Mode
                    </span>
                  )}
                  {repoAnalysisMode === 'ai_enhanced' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      AI Enhanced
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  In-depth architectural decomposition, tech stack evidence extraction, multi-factor similarity alignment, and open innovation gap synthesis.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleDeepAnalyze}
                  disabled={repoAnalyzing || githubTotal === 0}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <RefreshCw className={`w-4 h-4 ${repoAnalyzing ? 'animate-spin' : ''}`} />
                  <span>
                    {repoAnalyzing
                      ? 'Analyzing Repositories...'
                      : repoAnalyses.length > 0
                      ? 'Re-analyze Repositories'
                      : 'Run Deep Repository Analysis'}
                  </span>
                </button>
              </div>
            </div>

            {/* Error Message */}
            {repoAnalysisError && (
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <div className="space-y-1">
                  <p className="font-semibold">Analysis Notice</p>
                  <p>{repoAnalysisError}</p>
                </div>
              </div>
            )}

            {/* Batch Errors Warning */}
            {Object.keys(repoAnalysisBatchErrors).length > 0 && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-1">
                <div className="flex items-center gap-1.5 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Some repositories could not be analyzed:</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 pl-2 text-[11px] text-amber-200/80">
                  {Object.entries(repoAnalysisBatchErrors).map(([repoName, err]) => (
                    <li key={repoName}>
                      <span className="font-mono">{repoName}</span>: {err}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Stats Overview Grid */}
            {repoAnalysisStats && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Analyzed Repos</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-white font-mono">
                      {repoAnalysisStats.total_analyzed_repositories}
                    </span>
                    <span className="text-xs text-gray-500">/ {githubTotal}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Avg Similarity</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-blue-400 font-mono">
                      {repoAnalysisStats.average_similarity_score}%
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Detected Tech</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-emerald-400 font-mono">
                      {Object.keys(repoAnalysisStats.technology_distribution).length}
                    </span>
                    <span className="text-xs text-gray-500">tools</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Extracted Features</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-purple-400 font-mono">
                      {repoAnalysisStats.total_features_extracted}
                    </span>
                    <span className="text-xs text-gray-500">features</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 col-span-2 sm:col-span-1">
                  <span className="text-[11px] text-gray-400 font-medium">Innovation Gaps</span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-rose-400 font-mono">
                      {repoAnalysisStats.innovation_gaps_count}
                    </span>
                    <span className="text-[10px] text-rose-300/80 font-mono">
                      ({repoAnalysisStats.gaps_by_priority['high'] || 0} High)
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Not Yet Discovered */}
            {githubTotal === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-3">
                <Github className="w-10 h-10 text-gray-600 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    No Discovered Repositories Available
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Please discover relevant GitHub repositories in Section 13 above before launching deep repository analysis and innovation gap synthesis.
                  </p>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Discovered but Analysis Not Run Yet */}
            {githubTotal > 0 && repoAnalyses.length === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-4">
                <Compass className="w-10 h-10 text-blue-500/60 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    Ready for Deep Repository Analysis
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Analyze the {githubTotal} discovered GitHub repositories to extract real-world technical stacks, architecture topologies, and detect unaddressed innovation gaps.
                  </p>
                </div>
                <button
                  onClick={handleDeepAnalyze}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Start Deep Repository Analysis</span>
                </button>
              </div>
            )}

            {/* Loading Indicator */}
            {repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/60 border border-[#1F293D] text-center space-y-3">
                <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-white">
                    Conducting Deep Repository Intelligence...
                  </h4>
                  <p className="text-xs text-gray-400 max-w-md mx-auto">
                    Retrieving READMEs, scanning dependency manifests, mapping 7-category technology signatures, and synthesizing comparative innovation gaps.
                  </p>
                </div>
              </div>
            )}

            {/* SUB-SECTION A: Innovation Gaps Identified */}
            {innovationGaps.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-amber-400" />
                      <h4 className="text-sm font-semibold text-white">
                        Synthesized Innovation Gaps ({innovationGaps.length})
                      </h4>
                    </div>
                    <p className="text-xs text-gray-400">
                      Unaddressed capabilities, architectural shortcomings, and differentiation opportunities not found in analyzed open-source repositories.
                    </p>
                  </div>

                  {/* Priority & Category Filter Pills */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="flex items-center rounded-lg bg-[#151D30] p-1 border border-[#1F293D] text-[11px]">
                      {(['all', 'high', 'medium', 'low'] as const).map((p) => (
                        <button
                          key={p}
                          onClick={() => {
                            setSelectedGapPriority(p);
                            loadInnovationGaps(p, selectedGapCategory);
                          }}
                          className={`px-2.5 py-1 rounded-md font-medium capitalize transition-colors ${
                            selectedGapPriority === p
                              ? 'bg-blue-600 text-white'
                              : 'text-gray-400 hover:text-white'
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>

                    <select
                      value={selectedGapCategory}
                      onChange={(e) => {
                        setSelectedGapCategory(e.target.value);
                        loadInnovationGaps(selectedGapPriority, e.target.value);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-gray-300 focus:outline-none focus:border-blue-500"
                    >
                      <option value="all">All Categories</option>
                      <option value="missing_feature">Missing Feature</option>
                      <option value="partially_implemented">Partially Implemented</option>
                      <option value="improvement_opportunity">Improvement Opportunity</option>
                      <option value="differentiating_feature">Differentiating Feature</option>
                    </select>
                  </div>
                </div>

                {/* Innovation Gaps Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {innovationGaps.map((gap, gIdx) => {
                    const priorityColor =
                      gap.priority === 'high'
                        ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        : gap.priority === 'medium'
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                        : 'bg-blue-500/10 text-blue-300 border-blue-500/30';

                    const categoryBadge =
                      gap.category === 'missing_feature'
                        ? { label: 'Missing Feature', style: 'bg-rose-500/10 text-rose-300 border-rose-500/20' }
                        : gap.category === 'partially_implemented'
                        ? { label: 'Partially Implemented', style: 'bg-amber-500/10 text-amber-300 border-amber-500/20' }
                        : gap.category === 'improvement_opportunity'
                        ? { label: 'Improvement Opportunity', style: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20' }
                        : { label: 'Differentiating Feature', style: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' };

                    return (
                      <div
                        key={gap.id || gIdx}
                        className="p-4 rounded-xl bg-[#151D30] border border-[#1F293D] hover:border-blue-500/30 transition-all space-y-3 flex flex-col justify-between"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${categoryBadge.style}`}>
                              {categoryBadge.label}
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span className={`px-2 py-0.5 rounded-md text-[10px] font-mono uppercase font-bold border ${priorityColor}`}>
                                {gap.priority} Priority
                              </span>
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-gray-800 text-gray-300 border border-gray-700">
                                {gap.confidence_level} Confidence
                              </span>
                            </div>
                          </div>

                          <h5 className="text-sm font-semibold text-white leading-snug">
                            {gap.gap_title}
                          </h5>

                          <p className="text-xs text-gray-300 leading-relaxed">
                            {gap.description}
                          </p>
                        </div>

                        <div className="space-y-2.5 pt-2 border-t border-[#1F293D]/60 text-xs">
                          {/* Why It Matters */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wide">
                              Why It Matters
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.why_it_matters}
                            </p>
                          </div>

                          {/* Suggested Implementation */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wide">
                              Suggested Implementation
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.suggested_implementation}
                            </p>
                          </div>

                          {/* Supporting Evidence Citations */}
                          {gap.supporting_evidence && gap.supporting_evidence.length > 0 && (
                            <div className="space-y-1 pt-1">
                              <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                                Supporting Evidence
                              </span>
                              <div className="space-y-1">
                                {gap.supporting_evidence.map((ev, evIdx) => (
                                  <div
                                    key={evIdx}
                                    className="p-1.5 rounded bg-[#0B0F19]/80 border border-[#1F293D] text-[10px] font-mono text-gray-400 leading-tight"
                                  >
                                    {ev}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* SUB-SECTION B: Repository Deep Dive Cards */}
            {repoAnalyses.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-purple-400" />
                    <h4 className="text-sm font-semibold text-white">
                      Deep Analyzed Repositories ({repoAnalysesTotal})
                    </h4>
                  </div>
                  <span className="text-xs text-gray-400 font-mono">
                    Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                  </span>
                </div>

                <div className="space-y-4">
                  {repoAnalyses.map((item, idx) => {
                    const isExpanded = expandedRepoAnalyses[item.id || String(idx)] ?? true;
                    const isArchExpanded = expandedArchitecture[item.id || String(idx)] ?? false;
                    const overallSim = item.similarity?.overall_score ?? 0;

                    return (
                      <div
                        key={item.id || idx}
                        className="rounded-xl bg-[#151D30] border border-[#1F293D] overflow-hidden transition-all"
                      >
                        {/* Repository Deep Analysis Header */}
                        <div className="p-4 bg-[#111827]/70 border-b border-[#1F293D] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <GitBranch className="w-4 h-4 text-blue-400 shrink-0" />
                              <a
                                href={item.readme_url || `https://github.com/${item.repo_full_name}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-semibold text-white hover:text-blue-400 font-mono transition-colors flex items-center gap-1"
                              >
                                <span>{item.repo_full_name}</span>
                                <ExternalLink className="w-3 h-3 text-gray-500" />
                              </a>
                              {item.readme_present ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                  README ({item.readme_size ? `${Math.round(item.readme_size / 1024)} KB` : 'Verified'})
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-700/40 text-gray-400 border border-gray-700">
                                  No README
                                </span>
                              )}
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20">
                                {item.analysis_mode === 'deterministic_fallback' ? 'Heuristic' : 'AI-Enhanced'}
                              </span>
                            </div>
                            {item.summary && (
                              <p className="text-xs text-gray-400 leading-relaxed">
                                {item.summary}
                              </p>
                            )}
                          </div>

                          <div className="flex items-center gap-3 shrink-0">
                            {/* Similarity Score Pill */}
                            {item.similarity && (
                              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D]">
                                <span className="text-[11px] text-gray-400">Match:</span>
                                <span className="text-sm font-bold font-mono text-blue-400">
                                  {overallSim}%
                                </span>
                              </div>
                            )}

                            <button
                              onClick={() => toggleRepoExpand(item.id || String(idx))}
                              className="p-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-gray-400 hover:text-white transition-colors"
                            >
                              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>
                          </div>
                        </div>

                        {/* Collapsible Details Body */}
                        {isExpanded && (
                          <div className="p-4 space-y-4">
                            {/* Multi-Factor Similarity Alignment Breakdown */}
                            {item.similarity && (
                              <div className="p-3.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-3">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-1.5">
                                    <TrendingUp className="w-4 h-4 text-blue-400" />
                                    <span className="text-xs font-semibold text-white">
                                      Multi-Factor Similarity Alignment ({item.similarity.overall_score}%)
                                    </span>
                                  </div>
                                  <span className="text-[11px] text-gray-400">
                                    Weighted Composite Model
                                  </span>
                                </div>

                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Problem (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.problem_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-blue-500 rounded-full"
                                        style={{ width: `${item.similarity.problem_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Feature (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.feature_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-indigo-500 rounded-full"
                                        style={{ width: `${item.similarity.feature_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Tech Stack (25%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.tech_stack_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-purple-500 rounded-full"
                                        style={{ width: `${item.similarity.tech_stack_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Domain (15%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.domain_similarity}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-cyan-500 rounded-full"
                                        style={{ width: `${item.similarity.domain_similarity}%` }}
                                      />
                                    </div>
                                  </div>
                                </div>

                                {item.similarity.similarity_explanation && (
                                  <p className="text-[11px] text-gray-400 italic leading-relaxed pt-1 border-t border-[#1F293D]/60">
                                    {item.similarity.similarity_explanation}
                                  </p>
                                )}
                              </div>
                            )}

                            {/* Problem Statement */}
                            {item.problem_statement && (
                              <div className="space-y-1 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Problem Addressed by Repository
                                </span>
                                <p className="text-gray-300 leading-relaxed bg-[#0B0F19]/50 p-2.5 rounded-lg border border-[#1F293D]">
                                  {item.problem_statement}
                                </p>
                              </div>
                            )}

                            {/* 7 Standard Technology Stack Categories */}
                            <div className="space-y-2 text-xs">
                              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                Detected Technical Stack (Evidence Traceable)
                              </span>

                              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                                {/* Languages */}
                                {item.detected_technologies?.programming_languages?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-purple-400">
                                      <Code2 className="w-3.5 h-3.5" />
                                      <span>Languages</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.programming_languages.map((l, lIdx) => (
                                        <span
                                          key={lIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20"
                                        >
                                          {l}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Backend */}
                                {item.detected_technologies?.backend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-blue-400">
                                      <Cpu className="w-3.5 h-3.5" />
                                      <span>Backend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.backend_frameworks.map((b, bIdx) => (
                                        <span
                                          key={bIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20"
                                        >
                                          {b}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Frontend */}
                                {item.detected_technologies?.frontend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400">
                                      <Layers className="w-3.5 h-3.5" />
                                      <span>Frontend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.frontend_frameworks.map((f, fIdx) => (
                                        <span
                                          key={fIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                                        >
                                          {f}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* AI / ML */}
                                {item.detected_technologies?.ai_ml_libraries?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-rose-400">
                                      <Sparkles className="w-3.5 h-3.5" />
                                      <span>AI / ML Libraries</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.ai_ml_libraries.map((ai, aiIdx) => (
                                        <span
                                          key={aiIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-rose-500/10 text-rose-300 border border-rose-500/20"
                                        >
                                          {ai}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Databases */}
                                {item.detected_technologies?.databases?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-400">
                                      <Database className="w-3.5 h-3.5" />
                                      <span>Databases & Storage</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.databases.map((db, dbIdx) => (
                                        <span
                                          key={dbIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20"
                                        >
                                          {db}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Cloud & DevOps */}
                                {(item.detected_technologies?.cloud_deployment?.length > 0 ||
                                  item.detected_technologies?.devops_tools?.length > 0) && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-cyan-400">
                                      <Cloud className="w-3.5 h-3.5" />
                                      <span>Cloud & DevOps</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {[
                                        ...(item.detected_technologies.cloud_deployment || []),
                                        ...(item.detected_technologies.devops_tools || []),
                                      ].map((tool, tIdx) => (
                                        <span
                                          key={tIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/20"
                                        >
                                          {tool}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Extracted Features List */}
                            {item.features && item.features.length > 0 && (
                              <div className="space-y-2 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Extracted Repository Features ({item.features.length})
                                </span>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  {item.features.map((feat, fIdx) => (
                                    <div
                                      key={fIdx}
                                      className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1"
                                    >
                                      <div className="flex items-center justify-between gap-1">
                                        <span className="font-semibold text-white text-xs truncate">
                                          {feat.feature_name}
                                        </span>
                                        <div className="flex items-center gap-1 shrink-0">
                                          {feat.is_documented ? (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                              Doc
                                            </span>
                                          ) : (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-gray-800 text-gray-400 border border-gray-700">
                                              Inferred
                                            </span>
                                          )}
                                          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-blue-500/10 text-blue-300">
                                            {Math.round(feat.confidence_score * 100)}%
                                          </span>
                                        </div>
                                      </div>
                                      <p className="text-[11px] text-gray-400 leading-snug">
                                        {feat.description}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Architecture Topology Accordion */}
                            {item.architecture && (
                              <div className="pt-2 border-t border-[#1F293D]/60 space-y-2">
                                <button
                                  onClick={() => toggleArchitectureExpand(item.id || String(idx))}
                                  className="flex items-center justify-between w-full text-xs text-gray-400 hover:text-white transition-colors"
                                >
                                  <div className="flex items-center gap-1.5">
                                    <Layers className="w-3.5 h-3.5 text-blue-400" />
                                    <span className="font-medium">System Architecture Topology</span>
                                  </div>
                                  {isArchExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                </button>

                                {isArchExpanded && (
                                  <div className="p-3 rounded-lg bg-[#0B0F19] border border-[#1F293D] grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                                    {item.architecture.frontend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Frontend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.frontend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.backend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Backend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.backend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.database_layer && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Database</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.database_layer}</p>
                                      </div>
                                    )}
                                    {item.architecture.ai_ml_pipeline && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">AI/ML Pipeline</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.ai_ml_pipeline}</p>
                                      </div>
                                    )}
                                    {item.architecture.deployment_infrastructure && (
                                      <div className="space-y-0.5 sm:col-span-2">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Deployment</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.deployment_infrastructure}</p>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Pagination Controls for Repository Analyses */}
                {repoAnalysesTotal > 10 && (
                  <div className="flex items-center justify-between pt-3 border-t border-[#1F293D] text-xs text-gray-400">
                    <span>
                      Showing {(repoAnalysesPage - 1) * 10 + 1} to{' '}
                      {Math.min(repoAnalysesPage * 10, repoAnalysesTotal)} of {repoAnalysesTotal} analyzed repositories
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage - 1)}
                        disabled={repoAnalysesPage <= 1}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="px-2 font-mono text-gray-300">
                        Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                      </span>
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage + 1)}
                        disabled={repoAnalysesPage * 10 >= repoAnalysesTotal}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

                    {/* 1. Project Overview & Summary */}
          <div className="dna-card p-6 space-y-3">
            <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
              <FileText className="w-4 h-4 text-purple-400" />
              <h2 className="text-base font-semibold text-white">1. Project Overview & Summary</h2>
            </div>
            <p className="text-sm text-gray-300 leading-relaxed bg-[#0E1424] p-4 rounded-xl border border-[#1F293D]">
              {analysis.project_summary}
            </p>
          </div>

          {/* 2 & 3. Problem Statement & Proposed Solution */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="dna-card p-6 space-y-3">
              <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <h2 className="text-base font-semibold text-white">2. Problem Statement</h2>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed bg-[#0E1424] p-4 rounded-xl border border-[#1F293D] min-h-[140px]">
                {analysis.problem_statement}
              </p>
            </div>

            <div className="dna-card p-6 space-y-3">
              <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h2 className="text-base font-semibold text-white">3. Proposed Solution</h2>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed bg-[#0E1424] p-4 rounded-xl border border-[#1F293D] min-h-[140px]">
                {analysis.proposed_solution}
              </p>
            </div>
          </div>

          {/* 4. Domain Identification & Secondary Fields */}
          <div className="dna-card p-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
              <Layers className="w-4 h-4 text-cyan-400" />
              <h2 className="text-base font-semibold text-white">4. Domain Taxonomy</h2>
            </div>
            <div className="space-y-3">
              <div>
                <span className="text-[11px] font-mono text-gray-400 uppercase block mb-1.5">
                  Primary Domain:
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold bg-cyan-950/40 text-cyan-300 border border-cyan-500/30">
                  {analysis.primary_domain}
                </span>
              </div>

              {analysis.secondary_domains && analysis.secondary_domains.length > 0 && (
                <div>
                  <span className="text-[11px] font-mono text-gray-400 uppercase block mb-1.5">
                    Cross-Disciplinary & Secondary Domains:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {analysis.secondary_domains.map((dom, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 rounded text-xs font-medium bg-[#162032] text-gray-300 border border-gray-700/60"
                      >
                        {dom}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 5. Keyword Extraction (10-20 Keywords) */}
          <div className="dna-card p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#1F293D] pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <h2 className="text-base font-semibold text-white">5. Technical & Research Keywords</h2>
                <span className="text-xs font-mono text-gray-400 bg-[#162032] px-2 py-0.5 rounded border border-gray-700/50">
                  {analysis.keywords.length} terms
                </span>
              </div>
              <span className="text-[11px] text-gray-400 font-mono hidden sm:inline">
                Click keyword to copy
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {analysis.keywords.map((kw, i) => (
                <button
                  key={i}
                  onClick={() => handleCopy(kw)}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded-lg bg-[#162032] hover:bg-[#1E2B45] text-cyan-300 hover:text-white border border-[#232E47] transition-all group"
                  title="Click to copy"
                >
                  <span>{kw}</span>
                  {copiedKeyword === kw ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3 text-gray-400 group-hover:text-white" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* 6. Technology Identification (User vs AI-Recommended) */}
          <div className="dna-card p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-[#1F293D] pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <h2 className="text-base font-semibold text-white">6. Technology Stack Identification</h2>
              </div>
              <span className="text-xs font-mono text-purple-300 bg-purple-950/40 px-2.5 py-0.5 rounded border border-purple-500/20">
                User-Specified vs. AI-Recommended
              </span>
            </div>

            {/* User-Specified Stack */}
            <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
              <span className="text-xs font-semibold text-gray-300 block">
                User-Provided Stack Preferences:
              </span>
              <div className="flex flex-wrap gap-2">
                {analysis.user_technologies && analysis.user_technologies.length > 0 ? (
                  analysis.user_technologies.map((t, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 text-xs font-mono rounded bg-[#162032] text-gray-200 border border-gray-700/60"
                    >
                      {t}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-gray-400 italic">None specified by user</span>
                )}
              </div>
            </div>

            {/* AI-Recommended Categories */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="text-xs font-mono text-purple-400 uppercase font-semibold">
                  Languages:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.recommended_technologies.languages?.map((item, idx) => (
                    <span key={idx} className="px-2 py-0.5 text-xs font-mono rounded bg-[#162032] text-gray-300">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="text-xs font-mono text-cyan-400 uppercase font-semibold">
                  Frameworks & Libraries:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.recommended_technologies.frameworks?.map((item, idx) => (
                    <span key={idx} className="px-2 py-0.5 text-xs font-mono rounded bg-[#162032] text-gray-300">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="text-xs font-mono text-indigo-400 uppercase font-semibold">
                  Algorithms & Methods:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.recommended_technologies.algorithms?.map((item, idx) => (
                    <span key={idx} className="px-2 py-0.5 text-xs font-mono rounded bg-[#162032] text-gray-300">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="text-xs font-mono text-emerald-400 uppercase font-semibold">
                  Hardware & Compute:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.recommended_technologies.hardware?.map((item, idx) => (
                    <span key={idx} className="px-2 py-0.5 text-xs font-mono rounded bg-[#162032] text-gray-300">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="text-xs font-mono text-sky-400 uppercase font-semibold">
                  Tools & Middleware:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.recommended_technologies.tools?.map((item, idx) => (
                    <span key={idx} className="px-2 py-0.5 text-xs font-mono rounded bg-[#162032] text-gray-300">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="text-xs font-mono text-amber-400 uppercase font-semibold">
                  Infrastructure & DB:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.recommended_technologies.infrastructure?.map((item, idx) => (
                    <span key={idx} className="px-2 py-0.5 text-xs font-mono rounded bg-[#162032] text-gray-300">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 12. Academic Research Discovery (Phase 4.1) */}
          <div className="dna-card p-6 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1F293D] pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold text-white">12. Academic Research Discovery</h2>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                      Phase 4.1
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Discover verified research literature matching this idea across arXiv, Semantic Scholar, and OpenAlex
                  </p>
                </div>
              </div>

              <button
                onClick={handleSearchResearch}
                disabled={researchSearching}
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <RefreshCw className={`w-4 h-4 ${researchSearching ? 'animate-spin' : ''}`} />
                {researchSearching ? 'Searching Repositories...' : 'Search Research Papers'}
              </button>
            </div>

            {/* Provider in-progress banner */}
            {researchSearching && (
              <div className="p-4 rounded-xl bg-blue-950/30 border border-blue-500/30 flex items-center gap-3 animate-pulse">
                <RefreshCw className="w-5 h-5 text-cyan-400 animate-spin flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-cyan-200">
                    Querying arXiv, Semantic Scholar, and OpenAlex simultaneously...
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Synthesizing queries from problem statement, keywords, and technical domain...
                  </p>
                </div>
              </div>
            )}

            {/* Provider Warnings Banner */}
            {Object.keys(providerErrors).length > 0 && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs space-y-1">
                  <p className="font-semibold text-amber-300">
                    Notice: Some academic providers encountered rate limits or service timeouts
                  </p>
                  <ul className="list-disc list-inside text-gray-300 space-y-0.5">
                    {Object.entries(providerErrors).map(([prov, msg]) => (
                      <li key={prov}>
                        <span className="font-mono capitalize font-medium text-amber-200">{prov.replace('_', ' ')}</span>: {msg}
                      </li>
                    ))}
                  </ul>
                  <p className="text-[11px] text-gray-400">
                    Results from remaining operational repositories are safely preserved below.
                  </p>
                </div>
              </div>
            )}

            {/* General Research Error */}
            {researchError && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-300 text-xs">
                <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
                <span>{researchError}</span>
              </div>
            )}

            {/* Discovery Stats Bar */}
            {researchStats && researchStats.total_papers > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-gray-400 font-medium">Total Papers</span>
                  <span className="text-xl font-bold text-white mt-1">{researchStats.total_papers}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-rose-300 font-medium">arXiv</span>
                  <span className="text-xl font-bold text-rose-400 mt-1">{researchStats.by_provider.arxiv || 0}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-sky-300 font-medium">Semantic Scholar</span>
                  <span className="text-xl font-bold text-sky-400 mt-1">{researchStats.by_provider.semantic_scholar || 0}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-emerald-300 font-medium">OpenAlex</span>
                  <span className="text-xl font-bold text-emerald-400 mt-1">{researchStats.by_provider.openalex || 0}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-teal-300 font-medium">Open Access</span>
                  <span className="text-xl font-bold text-teal-400 mt-1">{researchStats.open_access_count}</span>
                </div>
              </div>
            )}

            {/* Filters Bar */}
            <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                {/* Provider Filter Pills */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-xs text-gray-400 font-medium mr-1 flex items-center gap-1">
                    <Filter className="w-3.5 h-3.5" /> Provider:
                  </span>
                  {[
                    { id: 'all', label: 'All Sources' },
                    { id: 'arxiv', label: 'arXiv' },
                    { id: 'semantic_scholar', label: 'Semantic Scholar' },
                    { id: 'openalex', label: 'OpenAlex' },
                  ].map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        setSelectedProvider(p.id);
                        loadResearch(1, p.id, selectedYear, openAccessOnly, searchFilterKeyword);
                      }}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        selectedProvider === p.id
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-[#151D30] text-gray-400 hover:text-white border border-[#1F293D]'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>

                {/* Right filters: Year & Open Access Toggle */}
                <div className="flex items-center gap-3 flex-wrap">
                  {/* Year Select */}
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-gray-400" />
                    <select
                      value={selectedYear}
                      onChange={(e) => {
                        setSelectedYear(e.target.value);
                        loadResearch(1, selectedProvider, e.target.value, openAccessOnly, searchFilterKeyword);
                      }}
                      className="bg-[#151D30] border border-[#1F293D] text-gray-300 text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:border-blue-500"
                    >
                      <option value="all">All Years</option>
                      {researchStats &&
                        Object.keys(researchStats.year_distribution || {})
                          .sort((a, b) => parseInt(b) - parseInt(a))
                          .map((yr) => (
                            <option key={yr} value={yr}>
                              {yr} ({researchStats.year_distribution[yr]})
                            </option>
                          ))}
                    </select>
                  </div>

                  {/* Open Access Toggle */}
                  <button
                    onClick={() => {
                      const next = !openAccessOnly;
                      setOpenAccessOnly(next);
                      loadResearch(1, selectedProvider, selectedYear, next, searchFilterKeyword);
                    }}
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                      openAccessOnly
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-[#151D30] text-gray-400 border-[#1F293D] hover:text-white'
                    }`}
                  >
                    <Unlock className="w-3.5 h-3.5" />
                    <span>Open Access Only</span>
                  </button>
                </div>
              </div>

              {/* Text Search Input */}
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Filter papers by title, abstract, author, or venue..."
                  value={searchFilterKeyword}
                  onChange={(e) => {
                    setSearchFilterKeyword(e.target.value);
                    loadResearch(1, selectedProvider, selectedYear, openAccessOnly, e.target.value);
                  }}
                  className="w-full bg-[#151D30] border border-[#1F293D] rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Papers List */}
            {researchLoading && !researchSearching ? (
              <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
                <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
                <p className="text-xs text-gray-400">Loading stored research papers...</p>
              </div>
            ) : researchPapers.length === 0 ? (
              <div className="py-12 px-4 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col items-center justify-center text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <BookOpen className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-white">No Research Papers Discovered Yet</h3>
                <p className="text-xs text-gray-400 max-w-md">
                  Click the "Search Research Papers" button to automatically retrieve academic papers matching this project's problem statement and technical architecture from arXiv, Semantic Scholar, and OpenAlex.
                </p>
                <button
                  onClick={handleSearchResearch}
                  disabled={researchSearching}
                  className="mt-2 flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md transition-all"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${researchSearching ? 'animate-spin' : ''}`} />
                  Discover Papers Now
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {researchPapers.map((paper) => {
                  const isExpanded = !!expandedAbstracts[paper.id];
                  const providerStyles =
                    paper.provider === 'arxiv'
                      ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                      : paper.provider === 'semantic_scholar'
                      ? 'bg-sky-500/10 text-sky-300 border-sky-500/30'
                      : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';

                  const providerLabel =
                    paper.provider === 'arxiv'
                      ? 'arXiv'
                      : paper.provider === 'semantic_scholar'
                      ? 'Semantic Scholar'
                      : 'OpenAlex';

                  return (
                    <div
                      key={paper.id}
                      className="p-5 rounded-xl bg-[#0E1424] border border-[#1F293D] hover:border-indigo-500/40 transition-all space-y-3"
                    >
                      {/* Paper Top Badges Row */}
                      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px]">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`px-2 py-0.5 rounded-md font-mono font-medium border ${providerStyles}`}>
                            {providerLabel}
                          </span>

                          {paper.open_access && (
                            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md font-mono bg-teal-500/10 text-teal-300 border border-teal-500/30">
                              <Unlock className="w-3 h-3" />
                              Open Access
                            </span>
                          )}

                          {paper.citation_count !== null && paper.citation_count !== undefined && (
                            <span className="px-2 py-0.5 rounded-md font-mono bg-purple-500/10 text-purple-300 border border-purple-500/30">
                              {paper.citation_count} citations
                            </span>
                          )}

                          {paper.primary_category && (
                            <span className="px-2 py-0.5 rounded-md font-mono bg-gray-500/10 text-gray-400 border border-gray-500/30">
                              {paper.primary_category}
                            </span>
                          )}
                        </div>

                        {(paper.publication_year || paper.publication_date) && (
                          <span className="text-gray-400 font-mono flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {paper.publication_date || paper.publication_year}
                          </span>
                        )}
                      </div>

                      {/* Paper Title */}
                      <div>
                        {paper.paper_url ? (
                          <a
                            href={paper.paper_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-semibold text-white hover:text-blue-400 inline-flex items-center gap-1.5 transition-colors group"
                          >
                            <span>{paper.title}</span>
                            <ExternalLink className="w-3.5 h-3.5 text-gray-500 group-hover:text-blue-400 flex-shrink-0" />
                          </a>
                        ) : (
                          <h4 className="text-sm font-semibold text-white">{paper.title}</h4>
                        )}
                      </div>

                      {/* Authors and Venue */}
                      <div className="text-xs text-gray-400 space-y-0.5">
                        {paper.authors && paper.authors.length > 0 && (
                          <p>
                            <span className="text-gray-500 font-medium">Authors:</span> {paper.authors.join(', ')}
                          </p>
                        )}
                        {paper.venue && (
                          <p>
                            <span className="text-gray-500 font-medium">Venue:</span> {paper.venue}
                          </p>
                        )}
                      </div>

                      {/* Abstract Preview */}
                      <div className="text-xs text-gray-300 leading-relaxed bg-[#0B0F19] p-3 rounded-lg border border-[#1F293D]/60">
                        {paper.abstract ? (
                          <div>
                            <p>
                              {isExpanded || paper.abstract.length <= 220
                                ? paper.abstract
                                : `${paper.abstract.slice(0, 220)}...`}
                            </p>
                            {paper.abstract.length > 220 && (
                              <button
                                onClick={() => toggleAbstract(paper.id)}
                                className="text-blue-400 hover:text-blue-300 font-medium text-[11px] mt-1.5 focus:outline-none"
                              >
                                {isExpanded ? 'Show less' : 'Read more'}
                              </button>
                            )}
                          </div>
                        ) : (
                          <p className="italic text-gray-500">Abstract not provided in repository index.</p>
                        )}
                      </div>

                      {/* Card Action Links Footer */}
                      <div className="flex flex-wrap items-center gap-3 pt-1 border-t border-[#1F293D]/60 text-xs">
                        {paper.doi && (
                          <a
                            href={`https://doi.org/${paper.doi}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-mono text-[11px]"
                          >
                            <span>DOI: {paper.doi}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}

                        {paper.pdf_url && (
                          <a
                            href={paper.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 border border-blue-500/30 text-[11px] font-medium transition-all"
                          >
                            <FileText className="w-3 h-3" />
                            <span>View PDF</span>
                          </a>
                        )}

                        {paper.arxiv_id && (
                          <span className="text-gray-500 font-mono text-[11px]">
                            arXiv ID: {paper.arxiv_id}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Pagination Controls */}
                <div className="flex items-center justify-between pt-3 border-t border-[#1F293D] text-xs text-gray-400">
                  <span>
                    Showing {(researchPage - 1) * 10 + 1} to {Math.min(researchPage * 10, researchTotal)} of {researchTotal} papers
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => loadResearch(researchPage - 1)}
                      disabled={researchPage <= 1}
                      className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="px-2 font-mono text-gray-300">
                      Page {researchPage} of {Math.max(1, Math.ceil(researchTotal / 10))}
                    </span>
                    <button
                      onClick={() => loadResearch(researchPage + 1)}
                      disabled={researchPage * 10 >= researchTotal}
                      className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ======================================================== */}
          {/* SECTION 14: GitHub Repository Deep Analysis & Innovation Gaps */}
          {/* ======================================================== */}
          <div className="bg-[#111827] border border-[#1F293D] rounded-xl p-6 space-y-6">
            {/* Header & Trigger Action */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#1F293D]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                    <Compass className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">
                    Repository Deep Analysis & Innovation Gaps
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    Phase 4.3
                  </span>
                  {repoAnalysisMode === 'deterministic_fallback' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      Heuristic Mode
                    </span>
                  )}
                  {repoAnalysisMode === 'ai_enhanced' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      AI Enhanced
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  In-depth architectural decomposition, tech stack evidence extraction, multi-factor similarity alignment, and open innovation gap synthesis.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleDeepAnalyze}
                  disabled={repoAnalyzing || githubTotal === 0}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <RefreshCw className={`w-4 h-4 ${repoAnalyzing ? 'animate-spin' : ''}`} />
                  <span>
                    {repoAnalyzing
                      ? 'Analyzing Repositories...'
                      : repoAnalyses.length > 0
                      ? 'Re-analyze Repositories'
                      : 'Run Deep Repository Analysis'}
                  </span>
                </button>
              </div>
            </div>

            {/* Error Message */}
            {repoAnalysisError && (
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <div className="space-y-1">
                  <p className="font-semibold">Analysis Notice</p>
                  <p>{repoAnalysisError}</p>
                </div>
              </div>
            )}

            {/* Batch Errors Warning */}
            {Object.keys(repoAnalysisBatchErrors).length > 0 && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-1">
                <div className="flex items-center gap-1.5 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Some repositories could not be analyzed:</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 pl-2 text-[11px] text-amber-200/80">
                  {Object.entries(repoAnalysisBatchErrors).map(([repoName, err]) => (
                    <li key={repoName}>
                      <span className="font-mono">{repoName}</span>: {err}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Stats Overview Grid */}
            {repoAnalysisStats && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Analyzed Repos</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-white font-mono">
                      {repoAnalysisStats.total_analyzed_repositories}
                    </span>
                    <span className="text-xs text-gray-500">/ {githubTotal}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Avg Similarity</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-blue-400 font-mono">
                      {repoAnalysisStats.average_similarity_score}%
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Detected Tech</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-emerald-400 font-mono">
                      {Object.keys(repoAnalysisStats.technology_distribution).length}
                    </span>
                    <span className="text-xs text-gray-500">tools</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Extracted Features</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-purple-400 font-mono">
                      {repoAnalysisStats.total_features_extracted}
                    </span>
                    <span className="text-xs text-gray-500">features</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 col-span-2 sm:col-span-1">
                  <span className="text-[11px] text-gray-400 font-medium">Innovation Gaps</span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-rose-400 font-mono">
                      {repoAnalysisStats.innovation_gaps_count}
                    </span>
                    <span className="text-[10px] text-rose-300/80 font-mono">
                      ({repoAnalysisStats.gaps_by_priority['high'] || 0} High)
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Not Yet Discovered */}
            {githubTotal === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-3">
                <Github className="w-10 h-10 text-gray-600 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    No Discovered Repositories Available
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Please discover relevant GitHub repositories in Section 13 above before launching deep repository analysis and innovation gap synthesis.
                  </p>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Discovered but Analysis Not Run Yet */}
            {githubTotal > 0 && repoAnalyses.length === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-4">
                <Compass className="w-10 h-10 text-blue-500/60 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    Ready for Deep Repository Analysis
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Analyze the {githubTotal} discovered GitHub repositories to extract real-world technical stacks, architecture topologies, and detect unaddressed innovation gaps.
                  </p>
                </div>
                <button
                  onClick={handleDeepAnalyze}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Start Deep Repository Analysis</span>
                </button>
              </div>
            )}

            {/* Loading Indicator */}
            {repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/60 border border-[#1F293D] text-center space-y-3">
                <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-white">
                    Conducting Deep Repository Intelligence...
                  </h4>
                  <p className="text-xs text-gray-400 max-w-md mx-auto">
                    Retrieving READMEs, scanning dependency manifests, mapping 7-category technology signatures, and synthesizing comparative innovation gaps.
                  </p>
                </div>
              </div>
            )}

            {/* SUB-SECTION A: Innovation Gaps Identified */}
            {innovationGaps.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-amber-400" />
                      <h4 className="text-sm font-semibold text-white">
                        Synthesized Innovation Gaps ({innovationGaps.length})
                      </h4>
                    </div>
                    <p className="text-xs text-gray-400">
                      Unaddressed capabilities, architectural shortcomings, and differentiation opportunities not found in analyzed open-source repositories.
                    </p>
                  </div>

                  {/* Priority & Category Filter Pills */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="flex items-center rounded-lg bg-[#151D30] p-1 border border-[#1F293D] text-[11px]">
                      {(['all', 'high', 'medium', 'low'] as const).map((p) => (
                        <button
                          key={p}
                          onClick={() => {
                            setSelectedGapPriority(p);
                            loadInnovationGaps(p, selectedGapCategory);
                          }}
                          className={`px-2.5 py-1 rounded-md font-medium capitalize transition-colors ${
                            selectedGapPriority === p
                              ? 'bg-blue-600 text-white'
                              : 'text-gray-400 hover:text-white'
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>

                    <select
                      value={selectedGapCategory}
                      onChange={(e) => {
                        setSelectedGapCategory(e.target.value);
                        loadInnovationGaps(selectedGapPriority, e.target.value);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-gray-300 focus:outline-none focus:border-blue-500"
                    >
                      <option value="all">All Categories</option>
                      <option value="missing_feature">Missing Feature</option>
                      <option value="partially_implemented">Partially Implemented</option>
                      <option value="improvement_opportunity">Improvement Opportunity</option>
                      <option value="differentiating_feature">Differentiating Feature</option>
                    </select>
                  </div>
                </div>

                {/* Innovation Gaps Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {innovationGaps.map((gap, gIdx) => {
                    const priorityColor =
                      gap.priority === 'high'
                        ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        : gap.priority === 'medium'
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                        : 'bg-blue-500/10 text-blue-300 border-blue-500/30';

                    const categoryBadge =
                      gap.category === 'missing_feature'
                        ? { label: 'Missing Feature', style: 'bg-rose-500/10 text-rose-300 border-rose-500/20' }
                        : gap.category === 'partially_implemented'
                        ? { label: 'Partially Implemented', style: 'bg-amber-500/10 text-amber-300 border-amber-500/20' }
                        : gap.category === 'improvement_opportunity'
                        ? { label: 'Improvement Opportunity', style: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20' }
                        : { label: 'Differentiating Feature', style: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' };

                    return (
                      <div
                        key={gap.id || gIdx}
                        className="p-4 rounded-xl bg-[#151D30] border border-[#1F293D] hover:border-blue-500/30 transition-all space-y-3 flex flex-col justify-between"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${categoryBadge.style}`}>
                              {categoryBadge.label}
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span className={`px-2 py-0.5 rounded-md text-[10px] font-mono uppercase font-bold border ${priorityColor}`}>
                                {gap.priority} Priority
                              </span>
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-gray-800 text-gray-300 border border-gray-700">
                                {gap.confidence_level} Confidence
                              </span>
                            </div>
                          </div>

                          <h5 className="text-sm font-semibold text-white leading-snug">
                            {gap.gap_title}
                          </h5>

                          <p className="text-xs text-gray-300 leading-relaxed">
                            {gap.description}
                          </p>
                        </div>

                        <div className="space-y-2.5 pt-2 border-t border-[#1F293D]/60 text-xs">
                          {/* Why It Matters */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wide">
                              Why It Matters
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.why_it_matters}
                            </p>
                          </div>

                          {/* Suggested Implementation */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wide">
                              Suggested Implementation
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.suggested_implementation}
                            </p>
                          </div>

                          {/* Supporting Evidence Citations */}
                          {gap.supporting_evidence && gap.supporting_evidence.length > 0 && (
                            <div className="space-y-1 pt-1">
                              <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                                Supporting Evidence
                              </span>
                              <div className="space-y-1">
                                {gap.supporting_evidence.map((ev, evIdx) => (
                                  <div
                                    key={evIdx}
                                    className="p-1.5 rounded bg-[#0B0F19]/80 border border-[#1F293D] text-[10px] font-mono text-gray-400 leading-tight"
                                  >
                                    {ev}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* SUB-SECTION B: Repository Deep Dive Cards */}
            {repoAnalyses.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-purple-400" />
                    <h4 className="text-sm font-semibold text-white">
                      Deep Analyzed Repositories ({repoAnalysesTotal})
                    </h4>
                  </div>
                  <span className="text-xs text-gray-400 font-mono">
                    Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                  </span>
                </div>

                <div className="space-y-4">
                  {repoAnalyses.map((item, idx) => {
                    const isExpanded = expandedRepoAnalyses[item.id || String(idx)] ?? true;
                    const isArchExpanded = expandedArchitecture[item.id || String(idx)] ?? false;
                    const overallSim = item.similarity?.overall_score ?? 0;

                    return (
                      <div
                        key={item.id || idx}
                        className="rounded-xl bg-[#151D30] border border-[#1F293D] overflow-hidden transition-all"
                      >
                        {/* Repository Deep Analysis Header */}
                        <div className="p-4 bg-[#111827]/70 border-b border-[#1F293D] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <GitBranch className="w-4 h-4 text-blue-400 shrink-0" />
                              <a
                                href={item.readme_url || `https://github.com/${item.repo_full_name}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-semibold text-white hover:text-blue-400 font-mono transition-colors flex items-center gap-1"
                              >
                                <span>{item.repo_full_name}</span>
                                <ExternalLink className="w-3 h-3 text-gray-500" />
                              </a>
                              {item.readme_present ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                  README ({item.readme_size ? `${Math.round(item.readme_size / 1024)} KB` : 'Verified'})
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-700/40 text-gray-400 border border-gray-700">
                                  No README
                                </span>
                              )}
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20">
                                {item.analysis_mode === 'deterministic_fallback' ? 'Heuristic' : 'AI-Enhanced'}
                              </span>
                            </div>
                            {item.summary && (
                              <p className="text-xs text-gray-400 leading-relaxed">
                                {item.summary}
                              </p>
                            )}
                          </div>

                          <div className="flex items-center gap-3 shrink-0">
                            {/* Similarity Score Pill */}
                            {item.similarity && (
                              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D]">
                                <span className="text-[11px] text-gray-400">Match:</span>
                                <span className="text-sm font-bold font-mono text-blue-400">
                                  {overallSim}%
                                </span>
                              </div>
                            )}

                            <button
                              onClick={() => toggleRepoExpand(item.id || String(idx))}
                              className="p-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-gray-400 hover:text-white transition-colors"
                            >
                              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>
                          </div>
                        </div>

                        {/* Collapsible Details Body */}
                        {isExpanded && (
                          <div className="p-4 space-y-4">
                            {/* Multi-Factor Similarity Alignment Breakdown */}
                            {item.similarity && (
                              <div className="p-3.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-3">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-1.5">
                                    <TrendingUp className="w-4 h-4 text-blue-400" />
                                    <span className="text-xs font-semibold text-white">
                                      Multi-Factor Similarity Alignment ({item.similarity.overall_score}%)
                                    </span>
                                  </div>
                                  <span className="text-[11px] text-gray-400">
                                    Weighted Composite Model
                                  </span>
                                </div>

                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Problem (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.problem_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-blue-500 rounded-full"
                                        style={{ width: `${item.similarity.problem_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Feature (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.feature_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-indigo-500 rounded-full"
                                        style={{ width: `${item.similarity.feature_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Tech Stack (25%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.tech_stack_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-purple-500 rounded-full"
                                        style={{ width: `${item.similarity.tech_stack_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Domain (15%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.domain_similarity}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-cyan-500 rounded-full"
                                        style={{ width: `${item.similarity.domain_similarity}%` }}
                                      />
                                    </div>
                                  </div>
                                </div>

                                {item.similarity.similarity_explanation && (
                                  <p className="text-[11px] text-gray-400 italic leading-relaxed pt-1 border-t border-[#1F293D]/60">
                                    {item.similarity.similarity_explanation}
                                  </p>
                                )}
                              </div>
                            )}

                            {/* Problem Statement */}
                            {item.problem_statement && (
                              <div className="space-y-1 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Problem Addressed by Repository
                                </span>
                                <p className="text-gray-300 leading-relaxed bg-[#0B0F19]/50 p-2.5 rounded-lg border border-[#1F293D]">
                                  {item.problem_statement}
                                </p>
                              </div>
                            )}

                            {/* 7 Standard Technology Stack Categories */}
                            <div className="space-y-2 text-xs">
                              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                Detected Technical Stack (Evidence Traceable)
                              </span>

                              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                                {/* Languages */}
                                {item.detected_technologies?.programming_languages?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-purple-400">
                                      <Code2 className="w-3.5 h-3.5" />
                                      <span>Languages</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.programming_languages.map((l, lIdx) => (
                                        <span
                                          key={lIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20"
                                        >
                                          {l}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Backend */}
                                {item.detected_technologies?.backend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-blue-400">
                                      <Cpu className="w-3.5 h-3.5" />
                                      <span>Backend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.backend_frameworks.map((b, bIdx) => (
                                        <span
                                          key={bIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20"
                                        >
                                          {b}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Frontend */}
                                {item.detected_technologies?.frontend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400">
                                      <Layers className="w-3.5 h-3.5" />
                                      <span>Frontend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.frontend_frameworks.map((f, fIdx) => (
                                        <span
                                          key={fIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                                        >
                                          {f}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* AI / ML */}
                                {item.detected_technologies?.ai_ml_libraries?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-rose-400">
                                      <Sparkles className="w-3.5 h-3.5" />
                                      <span>AI / ML Libraries</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.ai_ml_libraries.map((ai, aiIdx) => (
                                        <span
                                          key={aiIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-rose-500/10 text-rose-300 border border-rose-500/20"
                                        >
                                          {ai}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Databases */}
                                {item.detected_technologies?.databases?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-400">
                                      <Database className="w-3.5 h-3.5" />
                                      <span>Databases & Storage</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.databases.map((db, dbIdx) => (
                                        <span
                                          key={dbIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20"
                                        >
                                          {db}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Cloud & DevOps */}
                                {(item.detected_technologies?.cloud_deployment?.length > 0 ||
                                  item.detected_technologies?.devops_tools?.length > 0) && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-cyan-400">
                                      <Cloud className="w-3.5 h-3.5" />
                                      <span>Cloud & DevOps</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {[
                                        ...(item.detected_technologies.cloud_deployment || []),
                                        ...(item.detected_technologies.devops_tools || []),
                                      ].map((tool, tIdx) => (
                                        <span
                                          key={tIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/20"
                                        >
                                          {tool}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Extracted Features List */}
                            {item.features && item.features.length > 0 && (
                              <div className="space-y-2 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Extracted Repository Features ({item.features.length})
                                </span>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  {item.features.map((feat, fIdx) => (
                                    <div
                                      key={fIdx}
                                      className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1"
                                    >
                                      <div className="flex items-center justify-between gap-1">
                                        <span className="font-semibold text-white text-xs truncate">
                                          {feat.feature_name}
                                        </span>
                                        <div className="flex items-center gap-1 shrink-0">
                                          {feat.is_documented ? (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                              Doc
                                            </span>
                                          ) : (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-gray-800 text-gray-400 border border-gray-700">
                                              Inferred
                                            </span>
                                          )}
                                          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-blue-500/10 text-blue-300">
                                            {Math.round(feat.confidence_score * 100)}%
                                          </span>
                                        </div>
                                      </div>
                                      <p className="text-[11px] text-gray-400 leading-snug">
                                        {feat.description}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Architecture Topology Accordion */}
                            {item.architecture && (
                              <div className="pt-2 border-t border-[#1F293D]/60 space-y-2">
                                <button
                                  onClick={() => toggleArchitectureExpand(item.id || String(idx))}
                                  className="flex items-center justify-between w-full text-xs text-gray-400 hover:text-white transition-colors"
                                >
                                  <div className="flex items-center gap-1.5">
                                    <Layers className="w-3.5 h-3.5 text-blue-400" />
                                    <span className="font-medium">System Architecture Topology</span>
                                  </div>
                                  {isArchExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                </button>

                                {isArchExpanded && (
                                  <div className="p-3 rounded-lg bg-[#0B0F19] border border-[#1F293D] grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                                    {item.architecture.frontend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Frontend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.frontend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.backend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Backend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.backend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.database_layer && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Database</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.database_layer}</p>
                                      </div>
                                    )}
                                    {item.architecture.ai_ml_pipeline && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">AI/ML Pipeline</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.ai_ml_pipeline}</p>
                                      </div>
                                    )}
                                    {item.architecture.deployment_infrastructure && (
                                      <div className="space-y-0.5 sm:col-span-2">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Deployment</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.deployment_infrastructure}</p>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Pagination Controls for Repository Analyses */}
                {repoAnalysesTotal > 10 && (
                  <div className="flex items-center justify-between pt-3 border-t border-[#1F293D] text-xs text-gray-400">
                    <span>
                      Showing {(repoAnalysesPage - 1) * 10 + 1} to{' '}
                      {Math.min(repoAnalysesPage * 10, repoAnalysesTotal)} of {repoAnalysesTotal} analyzed repositories
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage - 1)}
                        disabled={repoAnalysesPage <= 1}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="px-2 font-mono text-gray-300">
                        Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                      </span>
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage + 1)}
                        disabled={repoAnalysesPage * 10 >= repoAnalysesTotal}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

                    {/* 7 & 8. Objectives Generation & Target Users */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Objectives */}
            <div className="dna-card p-6 space-y-4">
              <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
                <Target className="w-4 h-4 text-emerald-400" />
                <h2 className="text-base font-semibold text-white">7. Actionable Project Objectives</h2>
              </div>
              <ul className="space-y-2.5 text-xs text-gray-300">
                {analysis.objectives.map((obj, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-mono text-[10px] flex-shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed">{obj}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Target Users */}
            <div className="dna-card p-6 space-y-4">
              <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
                <Users className="w-4 h-4 text-purple-400" />
                <h2 className="text-base font-semibold text-white">8. Target Beneficiaries & Users</h2>
              </div>
              <ul className="space-y-2.5 text-xs text-gray-300">
                {analysis.target_users.map((user, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 flex-shrink-0 mt-1.5" />
                    <span className="leading-relaxed">{user}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* 9. Technical Difficulty & Reasoning */}
          <div className="dna-card p-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
              <Gauge className="w-4 h-4 text-cyan-400" />
              <h2 className="text-base font-semibold text-white">9. Technical Difficulty Assessment</h2>
            </div>
            <div className="space-y-2 bg-[#0E1424] p-4 rounded-xl border border-[#1F293D]">
              <div className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded text-xs font-mono font-bold border ${getDifficultyColor(analysis.difficulty_level)}`}>
                  {analysis.difficulty_level} Complexity
                </span>
                <span className="text-xs font-mono text-gray-400">
                  Classification: <strong>{analysis.project_type}</strong>
                </span>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed pt-1">
                {analysis.difficulty_reasoning}
              </p>
            </div>
          </div>

          {/* 10. Project Requirements & Candidate Datasets */}
          <div className="dna-card p-6 space-y-5">
            <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
              <HardDrive className="w-4 h-4 text-indigo-400" />
              <h2 className="text-base font-semibold text-white">10. Technical Requirements & Candidate Datasets</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="font-semibold text-cyan-300 flex items-center gap-1.5">
                  Candidate Datasets:
                </span>
                <p className="text-[11px] text-gray-400 font-mono">
                  *Unverified candidate data sources suggested for benchmark testing
                </p>
                <ul className="space-y-1 text-gray-300 list-disc list-inside">
                  {analysis.requirements.possible_datasets?.map((ds, i) => (
                    <li key={i}>{ds}</li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="font-semibold text-purple-300">Hardware & Compute Needs:</span>
                <ul className="space-y-1 text-gray-300 list-disc list-inside">
                  {analysis.requirements.hardware_requirements?.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="font-semibold text-emerald-300">Software & Runtimes:</span>
                <ul className="space-y-1 text-gray-300 list-disc list-inside">
                  {analysis.requirements.software_requirements?.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-2">
                <span className="font-semibold text-rose-300">Technical Constraints & Dependencies:</span>
                <ul className="space-y-1 text-gray-300 list-disc list-inside">
                  {analysis.requirements.technical_constraints?.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* 11. Assumptions and Risks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="dna-card p-6 space-y-3">
              <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
                <HelpCircle className="w-4 h-4 text-purple-400" />
                <h2 className="text-base font-semibold text-white">11A. Engineering Assumptions</h2>
              </div>
              <ul className="space-y-2 text-xs text-gray-300 bg-[#0E1424] p-4 rounded-xl border border-[#1F293D] min-h-[140px]">
                {analysis.assumptions.map((ass, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 flex-shrink-0 mt-1.5" />
                    <span>{ass}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="dna-card p-6 space-y-3">
              <div className="flex items-center gap-2 border-b border-[#1F293D] pb-3">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <h2 className="text-base font-semibold text-white">11B. Technical Challenges & Risks</h2>
              </div>
              <div className="space-y-2 text-xs text-gray-300 bg-[#0E1424] p-4 rounded-xl border border-[#1F293D] min-h-[140px]">
                <p className="font-semibold text-amber-300 font-mono">Algorithmic & Technical:</p>
                <ul className="space-y-1 list-disc list-inside pb-2">
                  {analysis.risks.technical_challenges?.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
                <p className="font-semibold text-rose-300 font-mono">Implementation & Deployment:</p>
                <ul className="space-y-1 list-disc list-inside">
                  {analysis.risks.implementation_risks?.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* 12. Academic Research Discovery (Phase 4.1) */}
          <div className="dna-card p-6 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1F293D] pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold text-white">12. Academic Research Discovery</h2>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                      Phase 4.1
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Discover verified research literature matching this idea across arXiv, Semantic Scholar, and OpenAlex
                  </p>
                </div>
              </div>

              <button
                onClick={handleSearchResearch}
                disabled={researchSearching}
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <RefreshCw className={`w-4 h-4 ${researchSearching ? 'animate-spin' : ''}`} />
                {researchSearching ? 'Searching Repositories...' : 'Search Research Papers'}
              </button>
            </div>

            {/* Provider in-progress banner */}
            {researchSearching && (
              <div className="p-4 rounded-xl bg-blue-950/30 border border-blue-500/30 flex items-center gap-3 animate-pulse">
                <RefreshCw className="w-5 h-5 text-cyan-400 animate-spin flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-cyan-200">
                    Querying arXiv, Semantic Scholar, and OpenAlex simultaneously...
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Synthesizing queries from problem statement, keywords, and technical domain...
                  </p>
                </div>
              </div>
            )}

            {/* Provider Warnings Banner */}
            {Object.keys(providerErrors).length > 0 && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs space-y-1">
                  <p className="font-semibold text-amber-300">
                    Notice: Some academic providers encountered rate limits or service timeouts
                  </p>
                  <ul className="list-disc list-inside text-gray-300 space-y-0.5">
                    {Object.entries(providerErrors).map(([prov, msg]) => (
                      <li key={prov}>
                        <span className="font-mono capitalize font-medium text-amber-200">{prov.replace('_', ' ')}</span>: {msg}
                      </li>
                    ))}
                  </ul>
                  <p className="text-[11px] text-gray-400">
                    Results from remaining operational repositories are safely preserved below.
                  </p>
                </div>
              </div>
            )}

            {/* General Research Error */}
            {researchError && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-300 text-xs">
                <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
                <span>{researchError}</span>
              </div>
            )}

            {/* Discovery Stats Bar */}
            {researchStats && researchStats.total_papers > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-gray-400 font-medium">Total Papers</span>
                  <span className="text-xl font-bold text-white mt-1">{researchStats.total_papers}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-rose-300 font-medium">arXiv</span>
                  <span className="text-xl font-bold text-rose-400 mt-1">{researchStats.by_provider.arxiv || 0}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-sky-300 font-medium">Semantic Scholar</span>
                  <span className="text-xl font-bold text-sky-400 mt-1">{researchStats.by_provider.semantic_scholar || 0}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-emerald-300 font-medium">OpenAlex</span>
                  <span className="text-xl font-bold text-emerald-400 mt-1">{researchStats.by_provider.openalex || 0}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-teal-300 font-medium">Open Access</span>
                  <span className="text-xl font-bold text-teal-400 mt-1">{researchStats.open_access_count}</span>
                </div>
              </div>
            )}

            {/* Filters Bar */}
            <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                {/* Provider Filter Pills */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-xs text-gray-400 font-medium mr-1 flex items-center gap-1">
                    <Filter className="w-3.5 h-3.5" /> Provider:
                  </span>
                  {[
                    { id: 'all', label: 'All Sources' },
                    { id: 'arxiv', label: 'arXiv' },
                    { id: 'semantic_scholar', label: 'Semantic Scholar' },
                    { id: 'openalex', label: 'OpenAlex' },
                  ].map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        setSelectedProvider(p.id);
                        loadResearch(1, p.id, selectedYear, openAccessOnly, searchFilterKeyword);
                      }}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        selectedProvider === p.id
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-[#151D30] text-gray-400 hover:text-white border border-[#1F293D]'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>

                {/* Right filters: Year & Open Access Toggle */}
                <div className="flex items-center gap-3 flex-wrap">
                  {/* Year Select */}
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-gray-400" />
                    <select
                      value={selectedYear}
                      onChange={(e) => {
                        setSelectedYear(e.target.value);
                        loadResearch(1, selectedProvider, e.target.value, openAccessOnly, searchFilterKeyword);
                      }}
                      className="bg-[#151D30] border border-[#1F293D] text-gray-300 text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:border-blue-500"
                    >
                      <option value="all">All Years</option>
                      {researchStats &&
                        Object.keys(researchStats.year_distribution || {})
                          .sort((a, b) => parseInt(b) - parseInt(a))
                          .map((yr) => (
                            <option key={yr} value={yr}>
                              {yr} ({researchStats.year_distribution[yr]})
                            </option>
                          ))}
                    </select>
                  </div>

                  {/* Open Access Toggle */}
                  <button
                    onClick={() => {
                      const next = !openAccessOnly;
                      setOpenAccessOnly(next);
                      loadResearch(1, selectedProvider, selectedYear, next, searchFilterKeyword);
                    }}
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                      openAccessOnly
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-[#151D30] text-gray-400 border-[#1F293D] hover:text-white'
                    }`}
                  >
                    <Unlock className="w-3.5 h-3.5" />
                    <span>Open Access Only</span>
                  </button>
                </div>
              </div>

              {/* Text Search Input */}
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Filter papers by title, abstract, author, or venue..."
                  value={searchFilterKeyword}
                  onChange={(e) => {
                    setSearchFilterKeyword(e.target.value);
                    loadResearch(1, selectedProvider, selectedYear, openAccessOnly, e.target.value);
                  }}
                  className="w-full bg-[#151D30] border border-[#1F293D] rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Papers List */}
            {researchLoading && !researchSearching ? (
              <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
                <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
                <p className="text-xs text-gray-400">Loading stored research papers...</p>
              </div>
            ) : researchPapers.length === 0 ? (
              <div className="py-12 px-4 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col items-center justify-center text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <BookOpen className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-white">No Research Papers Discovered Yet</h3>
                <p className="text-xs text-gray-400 max-w-md">
                  Click the "Search Research Papers" button to automatically retrieve academic papers matching this project's problem statement and technical architecture from arXiv, Semantic Scholar, and OpenAlex.
                </p>
                <button
                  onClick={handleSearchResearch}
                  disabled={researchSearching}
                  className="mt-2 flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md transition-all"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${researchSearching ? 'animate-spin' : ''}`} />
                  Discover Papers Now
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {researchPapers.map((paper) => {
                  const isExpanded = !!expandedAbstracts[paper.id];
                  const providerStyles =
                    paper.provider === 'arxiv'
                      ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                      : paper.provider === 'semantic_scholar'
                      ? 'bg-sky-500/10 text-sky-300 border-sky-500/30'
                      : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';

                  const providerLabel =
                    paper.provider === 'arxiv'
                      ? 'arXiv'
                      : paper.provider === 'semantic_scholar'
                      ? 'Semantic Scholar'
                      : 'OpenAlex';

                  return (
                    <div
                      key={paper.id}
                      className="p-5 rounded-xl bg-[#0E1424] border border-[#1F293D] hover:border-indigo-500/40 transition-all space-y-3"
                    >
                      {/* Paper Top Badges Row */}
                      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px]">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`px-2 py-0.5 rounded-md font-mono font-medium border ${providerStyles}`}>
                            {providerLabel}
                          </span>

                          {paper.open_access && (
                            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md font-mono bg-teal-500/10 text-teal-300 border border-teal-500/30">
                              <Unlock className="w-3 h-3" />
                              Open Access
                            </span>
                          )}

                          {paper.citation_count !== null && paper.citation_count !== undefined && (
                            <span className="px-2 py-0.5 rounded-md font-mono bg-purple-500/10 text-purple-300 border border-purple-500/30">
                              {paper.citation_count} citations
                            </span>
                          )}

                          {paper.primary_category && (
                            <span className="px-2 py-0.5 rounded-md font-mono bg-gray-500/10 text-gray-400 border border-gray-500/30">
                              {paper.primary_category}
                            </span>
                          )}
                        </div>

                        {(paper.publication_year || paper.publication_date) && (
                          <span className="text-gray-400 font-mono flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {paper.publication_date || paper.publication_year}
                          </span>
                        )}
                      </div>

                      {/* Paper Title */}
                      <div>
                        {paper.paper_url ? (
                          <a
                            href={paper.paper_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-semibold text-white hover:text-blue-400 inline-flex items-center gap-1.5 transition-colors group"
                          >
                            <span>{paper.title}</span>
                            <ExternalLink className="w-3.5 h-3.5 text-gray-500 group-hover:text-blue-400 flex-shrink-0" />
                          </a>
                        ) : (
                          <h4 className="text-sm font-semibold text-white">{paper.title}</h4>
                        )}
                      </div>

                      {/* Authors and Venue */}
                      <div className="text-xs text-gray-400 space-y-0.5">
                        {paper.authors && paper.authors.length > 0 && (
                          <p>
                            <span className="text-gray-500 font-medium">Authors:</span> {paper.authors.join(', ')}
                          </p>
                        )}
                        {paper.venue && (
                          <p>
                            <span className="text-gray-500 font-medium">Venue:</span> {paper.venue}
                          </p>
                        )}
                      </div>

                      {/* Abstract Preview */}
                      <div className="text-xs text-gray-300 leading-relaxed bg-[#0B0F19] p-3 rounded-lg border border-[#1F293D]/60">
                        {paper.abstract ? (
                          <div>
                            <p>
                              {isExpanded || paper.abstract.length <= 220
                                ? paper.abstract
                                : `${paper.abstract.slice(0, 220)}...`}
                            </p>
                            {paper.abstract.length > 220 && (
                              <button
                                onClick={() => toggleAbstract(paper.id)}
                                className="text-blue-400 hover:text-blue-300 font-medium text-[11px] mt-1.5 focus:outline-none"
                              >
                                {isExpanded ? 'Show less' : 'Read more'}
                              </button>
                            )}
                          </div>
                        ) : (
                          <p className="italic text-gray-500">Abstract not provided in repository index.</p>
                        )}
                      </div>

                      {/* Card Action Links Footer */}
                      <div className="flex flex-wrap items-center gap-3 pt-1 border-t border-[#1F293D]/60 text-xs">
                        {paper.doi && (
                          <a
                            href={`https://doi.org/${paper.doi}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-mono text-[11px]"
                          >
                            <span>DOI: {paper.doi}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}

                        {paper.pdf_url && (
                          <a
                            href={paper.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 border border-blue-500/30 text-[11px] font-medium transition-all"
                          >
                            <FileText className="w-3 h-3" />
                            <span>View PDF</span>
                          </a>
                        )}

                        {paper.arxiv_id && (
                          <span className="text-gray-500 font-mono text-[11px]">
                            arXiv ID: {paper.arxiv_id}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Pagination Controls */}
                <div className="flex items-center justify-between pt-3 border-t border-[#1F293D] text-xs text-gray-400">
                  <span>
                    Showing {(researchPage - 1) * 10 + 1} to {Math.min(researchPage * 10, researchTotal)} of {researchTotal} papers
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => loadResearch(researchPage - 1)}
                      disabled={researchPage <= 1}
                      className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="px-2 font-mono text-gray-300">
                      Page {researchPage} of {Math.max(1, Math.ceil(researchTotal / 10))}
                    </span>
                    <button
                      onClick={() => loadResearch(researchPage + 1)}
                      disabled={researchPage * 10 >= researchTotal}
                      className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ======================================================== */}
          {/* SECTION 14: GitHub Repository Deep Analysis & Innovation Gaps */}
          {/* ======================================================== */}
          <div className="bg-[#111827] border border-[#1F293D] rounded-xl p-6 space-y-6">
            {/* Header & Trigger Action */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#1F293D]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                    <Compass className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">
                    Repository Deep Analysis & Innovation Gaps
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    Phase 4.3
                  </span>
                  {repoAnalysisMode === 'deterministic_fallback' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      Heuristic Mode
                    </span>
                  )}
                  {repoAnalysisMode === 'ai_enhanced' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      AI Enhanced
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  In-depth architectural decomposition, tech stack evidence extraction, multi-factor similarity alignment, and open innovation gap synthesis.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleDeepAnalyze}
                  disabled={repoAnalyzing || githubTotal === 0}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <RefreshCw className={`w-4 h-4 ${repoAnalyzing ? 'animate-spin' : ''}`} />
                  <span>
                    {repoAnalyzing
                      ? 'Analyzing Repositories...'
                      : repoAnalyses.length > 0
                      ? 'Re-analyze Repositories'
                      : 'Run Deep Repository Analysis'}
                  </span>
                </button>
              </div>
            </div>

            {/* Error Message */}
            {repoAnalysisError && (
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <div className="space-y-1">
                  <p className="font-semibold">Analysis Notice</p>
                  <p>{repoAnalysisError}</p>
                </div>
              </div>
            )}

            {/* Batch Errors Warning */}
            {Object.keys(repoAnalysisBatchErrors).length > 0 && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-1">
                <div className="flex items-center gap-1.5 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Some repositories could not be analyzed:</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 pl-2 text-[11px] text-amber-200/80">
                  {Object.entries(repoAnalysisBatchErrors).map(([repoName, err]) => (
                    <li key={repoName}>
                      <span className="font-mono">{repoName}</span>: {err}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Stats Overview Grid */}
            {repoAnalysisStats && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Analyzed Repos</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-white font-mono">
                      {repoAnalysisStats.total_analyzed_repositories}
                    </span>
                    <span className="text-xs text-gray-500">/ {githubTotal}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Avg Similarity</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-blue-400 font-mono">
                      {repoAnalysisStats.average_similarity_score}%
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Detected Tech</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-emerald-400 font-mono">
                      {Object.keys(repoAnalysisStats.technology_distribution).length}
                    </span>
                    <span className="text-xs text-gray-500">tools</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Extracted Features</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-purple-400 font-mono">
                      {repoAnalysisStats.total_features_extracted}
                    </span>
                    <span className="text-xs text-gray-500">features</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 col-span-2 sm:col-span-1">
                  <span className="text-[11px] text-gray-400 font-medium">Innovation Gaps</span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-rose-400 font-mono">
                      {repoAnalysisStats.innovation_gaps_count}
                    </span>
                    <span className="text-[10px] text-rose-300/80 font-mono">
                      ({repoAnalysisStats.gaps_by_priority['high'] || 0} High)
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Not Yet Discovered */}
            {githubTotal === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-3">
                <Github className="w-10 h-10 text-gray-600 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    No Discovered Repositories Available
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Please discover relevant GitHub repositories in Section 13 above before launching deep repository analysis and innovation gap synthesis.
                  </p>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Discovered but Analysis Not Run Yet */}
            {githubTotal > 0 && repoAnalyses.length === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-4">
                <Compass className="w-10 h-10 text-blue-500/60 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    Ready for Deep Repository Analysis
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Analyze the {githubTotal} discovered GitHub repositories to extract real-world technical stacks, architecture topologies, and detect unaddressed innovation gaps.
                  </p>
                </div>
                <button
                  onClick={handleDeepAnalyze}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Start Deep Repository Analysis</span>
                </button>
              </div>
            )}

            {/* Loading Indicator */}
            {repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/60 border border-[#1F293D] text-center space-y-3">
                <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-white">
                    Conducting Deep Repository Intelligence...
                  </h4>
                  <p className="text-xs text-gray-400 max-w-md mx-auto">
                    Retrieving READMEs, scanning dependency manifests, mapping 7-category technology signatures, and synthesizing comparative innovation gaps.
                  </p>
                </div>
              </div>
            )}

            {/* SUB-SECTION A: Innovation Gaps Identified */}
            {innovationGaps.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-amber-400" />
                      <h4 className="text-sm font-semibold text-white">
                        Synthesized Innovation Gaps ({innovationGaps.length})
                      </h4>
                    </div>
                    <p className="text-xs text-gray-400">
                      Unaddressed capabilities, architectural shortcomings, and differentiation opportunities not found in analyzed open-source repositories.
                    </p>
                  </div>

                  {/* Priority & Category Filter Pills */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="flex items-center rounded-lg bg-[#151D30] p-1 border border-[#1F293D] text-[11px]">
                      {(['all', 'high', 'medium', 'low'] as const).map((p) => (
                        <button
                          key={p}
                          onClick={() => {
                            setSelectedGapPriority(p);
                            loadInnovationGaps(p, selectedGapCategory);
                          }}
                          className={`px-2.5 py-1 rounded-md font-medium capitalize transition-colors ${
                            selectedGapPriority === p
                              ? 'bg-blue-600 text-white'
                              : 'text-gray-400 hover:text-white'
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>

                    <select
                      value={selectedGapCategory}
                      onChange={(e) => {
                        setSelectedGapCategory(e.target.value);
                        loadInnovationGaps(selectedGapPriority, e.target.value);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-gray-300 focus:outline-none focus:border-blue-500"
                    >
                      <option value="all">All Categories</option>
                      <option value="missing_feature">Missing Feature</option>
                      <option value="partially_implemented">Partially Implemented</option>
                      <option value="improvement_opportunity">Improvement Opportunity</option>
                      <option value="differentiating_feature">Differentiating Feature</option>
                    </select>
                  </div>
                </div>

                {/* Innovation Gaps Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {innovationGaps.map((gap, gIdx) => {
                    const priorityColor =
                      gap.priority === 'high'
                        ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        : gap.priority === 'medium'
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                        : 'bg-blue-500/10 text-blue-300 border-blue-500/30';

                    const categoryBadge =
                      gap.category === 'missing_feature'
                        ? { label: 'Missing Feature', style: 'bg-rose-500/10 text-rose-300 border-rose-500/20' }
                        : gap.category === 'partially_implemented'
                        ? { label: 'Partially Implemented', style: 'bg-amber-500/10 text-amber-300 border-amber-500/20' }
                        : gap.category === 'improvement_opportunity'
                        ? { label: 'Improvement Opportunity', style: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20' }
                        : { label: 'Differentiating Feature', style: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' };

                    return (
                      <div
                        key={gap.id || gIdx}
                        className="p-4 rounded-xl bg-[#151D30] border border-[#1F293D] hover:border-blue-500/30 transition-all space-y-3 flex flex-col justify-between"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${categoryBadge.style}`}>
                              {categoryBadge.label}
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span className={`px-2 py-0.5 rounded-md text-[10px] font-mono uppercase font-bold border ${priorityColor}`}>
                                {gap.priority} Priority
                              </span>
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-gray-800 text-gray-300 border border-gray-700">
                                {gap.confidence_level} Confidence
                              </span>
                            </div>
                          </div>

                          <h5 className="text-sm font-semibold text-white leading-snug">
                            {gap.gap_title}
                          </h5>

                          <p className="text-xs text-gray-300 leading-relaxed">
                            {gap.description}
                          </p>
                        </div>

                        <div className="space-y-2.5 pt-2 border-t border-[#1F293D]/60 text-xs">
                          {/* Why It Matters */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wide">
                              Why It Matters
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.why_it_matters}
                            </p>
                          </div>

                          {/* Suggested Implementation */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wide">
                              Suggested Implementation
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.suggested_implementation}
                            </p>
                          </div>

                          {/* Supporting Evidence Citations */}
                          {gap.supporting_evidence && gap.supporting_evidence.length > 0 && (
                            <div className="space-y-1 pt-1">
                              <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                                Supporting Evidence
                              </span>
                              <div className="space-y-1">
                                {gap.supporting_evidence.map((ev, evIdx) => (
                                  <div
                                    key={evIdx}
                                    className="p-1.5 rounded bg-[#0B0F19]/80 border border-[#1F293D] text-[10px] font-mono text-gray-400 leading-tight"
                                  >
                                    {ev}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* SUB-SECTION B: Repository Deep Dive Cards */}
            {repoAnalyses.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-purple-400" />
                    <h4 className="text-sm font-semibold text-white">
                      Deep Analyzed Repositories ({repoAnalysesTotal})
                    </h4>
                  </div>
                  <span className="text-xs text-gray-400 font-mono">
                    Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                  </span>
                </div>

                <div className="space-y-4">
                  {repoAnalyses.map((item, idx) => {
                    const isExpanded = expandedRepoAnalyses[item.id || String(idx)] ?? true;
                    const isArchExpanded = expandedArchitecture[item.id || String(idx)] ?? false;
                    const overallSim = item.similarity?.overall_score ?? 0;

                    return (
                      <div
                        key={item.id || idx}
                        className="rounded-xl bg-[#151D30] border border-[#1F293D] overflow-hidden transition-all"
                      >
                        {/* Repository Deep Analysis Header */}
                        <div className="p-4 bg-[#111827]/70 border-b border-[#1F293D] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <GitBranch className="w-4 h-4 text-blue-400 shrink-0" />
                              <a
                                href={item.readme_url || `https://github.com/${item.repo_full_name}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-semibold text-white hover:text-blue-400 font-mono transition-colors flex items-center gap-1"
                              >
                                <span>{item.repo_full_name}</span>
                                <ExternalLink className="w-3 h-3 text-gray-500" />
                              </a>
                              {item.readme_present ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                  README ({item.readme_size ? `${Math.round(item.readme_size / 1024)} KB` : 'Verified'})
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-700/40 text-gray-400 border border-gray-700">
                                  No README
                                </span>
                              )}
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20">
                                {item.analysis_mode === 'deterministic_fallback' ? 'Heuristic' : 'AI-Enhanced'}
                              </span>
                            </div>
                            {item.summary && (
                              <p className="text-xs text-gray-400 leading-relaxed">
                                {item.summary}
                              </p>
                            )}
                          </div>

                          <div className="flex items-center gap-3 shrink-0">
                            {/* Similarity Score Pill */}
                            {item.similarity && (
                              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D]">
                                <span className="text-[11px] text-gray-400">Match:</span>
                                <span className="text-sm font-bold font-mono text-blue-400">
                                  {overallSim}%
                                </span>
                              </div>
                            )}

                            <button
                              onClick={() => toggleRepoExpand(item.id || String(idx))}
                              className="p-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-gray-400 hover:text-white transition-colors"
                            >
                              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>
                          </div>
                        </div>

                        {/* Collapsible Details Body */}
                        {isExpanded && (
                          <div className="p-4 space-y-4">
                            {/* Multi-Factor Similarity Alignment Breakdown */}
                            {item.similarity && (
                              <div className="p-3.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-3">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-1.5">
                                    <TrendingUp className="w-4 h-4 text-blue-400" />
                                    <span className="text-xs font-semibold text-white">
                                      Multi-Factor Similarity Alignment ({item.similarity.overall_score}%)
                                    </span>
                                  </div>
                                  <span className="text-[11px] text-gray-400">
                                    Weighted Composite Model
                                  </span>
                                </div>

                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Problem (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.problem_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-blue-500 rounded-full"
                                        style={{ width: `${item.similarity.problem_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Feature (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.feature_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-indigo-500 rounded-full"
                                        style={{ width: `${item.similarity.feature_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Tech Stack (25%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.tech_stack_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-purple-500 rounded-full"
                                        style={{ width: `${item.similarity.tech_stack_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Domain (15%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.domain_similarity}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-cyan-500 rounded-full"
                                        style={{ width: `${item.similarity.domain_similarity}%` }}
                                      />
                                    </div>
                                  </div>
                                </div>

                                {item.similarity.similarity_explanation && (
                                  <p className="text-[11px] text-gray-400 italic leading-relaxed pt-1 border-t border-[#1F293D]/60">
                                    {item.similarity.similarity_explanation}
                                  </p>
                                )}
                              </div>
                            )}

                            {/* Problem Statement */}
                            {item.problem_statement && (
                              <div className="space-y-1 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Problem Addressed by Repository
                                </span>
                                <p className="text-gray-300 leading-relaxed bg-[#0B0F19]/50 p-2.5 rounded-lg border border-[#1F293D]">
                                  {item.problem_statement}
                                </p>
                              </div>
                            )}

                            {/* 7 Standard Technology Stack Categories */}
                            <div className="space-y-2 text-xs">
                              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                Detected Technical Stack (Evidence Traceable)
                              </span>

                              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                                {/* Languages */}
                                {item.detected_technologies?.programming_languages?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-purple-400">
                                      <Code2 className="w-3.5 h-3.5" />
                                      <span>Languages</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.programming_languages.map((l, lIdx) => (
                                        <span
                                          key={lIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20"
                                        >
                                          {l}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Backend */}
                                {item.detected_technologies?.backend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-blue-400">
                                      <Cpu className="w-3.5 h-3.5" />
                                      <span>Backend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.backend_frameworks.map((b, bIdx) => (
                                        <span
                                          key={bIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20"
                                        >
                                          {b}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Frontend */}
                                {item.detected_technologies?.frontend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400">
                                      <Layers className="w-3.5 h-3.5" />
                                      <span>Frontend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.frontend_frameworks.map((f, fIdx) => (
                                        <span
                                          key={fIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                                        >
                                          {f}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* AI / ML */}
                                {item.detected_technologies?.ai_ml_libraries?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-rose-400">
                                      <Sparkles className="w-3.5 h-3.5" />
                                      <span>AI / ML Libraries</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.ai_ml_libraries.map((ai, aiIdx) => (
                                        <span
                                          key={aiIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-rose-500/10 text-rose-300 border border-rose-500/20"
                                        >
                                          {ai}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Databases */}
                                {item.detected_technologies?.databases?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-400">
                                      <Database className="w-3.5 h-3.5" />
                                      <span>Databases & Storage</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.databases.map((db, dbIdx) => (
                                        <span
                                          key={dbIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20"
                                        >
                                          {db}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Cloud & DevOps */}
                                {(item.detected_technologies?.cloud_deployment?.length > 0 ||
                                  item.detected_technologies?.devops_tools?.length > 0) && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-cyan-400">
                                      <Cloud className="w-3.5 h-3.5" />
                                      <span>Cloud & DevOps</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {[
                                        ...(item.detected_technologies.cloud_deployment || []),
                                        ...(item.detected_technologies.devops_tools || []),
                                      ].map((tool, tIdx) => (
                                        <span
                                          key={tIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/20"
                                        >
                                          {tool}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Extracted Features List */}
                            {item.features && item.features.length > 0 && (
                              <div className="space-y-2 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Extracted Repository Features ({item.features.length})
                                </span>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  {item.features.map((feat, fIdx) => (
                                    <div
                                      key={fIdx}
                                      className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1"
                                    >
                                      <div className="flex items-center justify-between gap-1">
                                        <span className="font-semibold text-white text-xs truncate">
                                          {feat.feature_name}
                                        </span>
                                        <div className="flex items-center gap-1 shrink-0">
                                          {feat.is_documented ? (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                              Doc
                                            </span>
                                          ) : (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-gray-800 text-gray-400 border border-gray-700">
                                              Inferred
                                            </span>
                                          )}
                                          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-blue-500/10 text-blue-300">
                                            {Math.round(feat.confidence_score * 100)}%
                                          </span>
                                        </div>
                                      </div>
                                      <p className="text-[11px] text-gray-400 leading-snug">
                                        {feat.description}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Architecture Topology Accordion */}
                            {item.architecture && (
                              <div className="pt-2 border-t border-[#1F293D]/60 space-y-2">
                                <button
                                  onClick={() => toggleArchitectureExpand(item.id || String(idx))}
                                  className="flex items-center justify-between w-full text-xs text-gray-400 hover:text-white transition-colors"
                                >
                                  <div className="flex items-center gap-1.5">
                                    <Layers className="w-3.5 h-3.5 text-blue-400" />
                                    <span className="font-medium">System Architecture Topology</span>
                                  </div>
                                  {isArchExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                </button>

                                {isArchExpanded && (
                                  <div className="p-3 rounded-lg bg-[#0B0F19] border border-[#1F293D] grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                                    {item.architecture.frontend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Frontend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.frontend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.backend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Backend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.backend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.database_layer && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Database</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.database_layer}</p>
                                      </div>
                                    )}
                                    {item.architecture.ai_ml_pipeline && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">AI/ML Pipeline</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.ai_ml_pipeline}</p>
                                      </div>
                                    )}
                                    {item.architecture.deployment_infrastructure && (
                                      <div className="space-y-0.5 sm:col-span-2">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Deployment</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.deployment_infrastructure}</p>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Pagination Controls for Repository Analyses */}
                {repoAnalysesTotal > 10 && (
                  <div className="flex items-center justify-between pt-3 border-t border-[#1F293D] text-xs text-gray-400">
                    <span>
                      Showing {(repoAnalysesPage - 1) * 10 + 1} to{' '}
                      {Math.min(repoAnalysesPage * 10, repoAnalysesTotal)} of {repoAnalysesTotal} analyzed repositories
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage - 1)}
                        disabled={repoAnalysesPage <= 1}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="px-2 font-mono text-gray-300">
                        Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                      </span>
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage + 1)}
                        disabled={repoAnalysesPage * 10 >= repoAnalysesTotal}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

                    {/* 13. GitHub Existing Projects Discovery (Phase 4.2) */}
          <div className="dna-card p-6 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1F293D] pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                  <Github className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold text-white">13. GitHub Existing Projects Discovery</h2>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-purple-500/10 text-purple-300 border border-purple-500/30">
                      Phase 4.2
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Discover open-source implementations, reference architectures, and active repositories related to your project idea
                  </p>
                </div>
              </div>

              <button
                onClick={handleSearchGitHub}
                disabled={githubSearching}
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-medium text-xs shadow-lg shadow-purple-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <RefreshCw className={`w-4 h-4 ${githubSearching ? 'animate-spin' : ''}`} />
                {githubSearching ? 'Discovering Repositories...' : 'Search GitHub Repositories'}
              </button>
            </div>

            {/* Discovery In-Progress Banner */}
            {githubSearching && (
              <div className="p-4 rounded-xl bg-purple-950/30 border border-purple-500/30 flex items-center gap-3 animate-pulse">
                <RefreshCw className="w-5 h-5 text-purple-400 animate-spin flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-purple-200">
                    Querying GitHub REST API for relevant open-source projects...
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Generating targeted domain queries, extracting technology stacks, and de-duplicating repository records...
                  </p>
                </div>
              </div>
            )}

            {/* Rate Limit / Provider Error Warnings */}
            {githubRateLimit && (githubRateLimit.remaining !== undefined && githubRateLimit.remaining !== null && githubRateLimit.remaining <= 10) && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs space-y-1">
                  <p className="font-semibold text-amber-300">
                    GitHub Search API Rate Limit Notice: {githubRateLimit.remaining} remaining requests of {githubRateLimit.limit}
                  </p>
                  <p className="text-[11px] text-gray-400">
                    {githubRateLimit.remaining === 0 
                      ? 'GitHub search rate limit reached. Please wait for the rate window to reset or configure a GITHUB_TOKEN in your backend environment for 5,000 requests/hour.'
                      : 'Rate limit is running low. Queries are executed sequentially to preserve quota.'}
                  </p>
                </div>
              </div>
            )}

            {Object.keys(githubErrors).length > 0 && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs space-y-1">
                  <p className="font-semibold text-amber-300">
                    Notice: Some search queries returned rate-limit or timeout errors
                  </p>
                  <ul className="list-disc list-inside text-gray-300 space-y-0.5">
                    {Object.entries(githubErrors).map(([query, msg]) => (
                      <li key={query}>
                        <span className="font-mono text-amber-200">"{query}"</span>: {msg}
                      </li>
                    ))}
                  </ul>
                  <p className="text-[11px] text-gray-400">
                    Successfully discovered repositories from other queries are preserved below.
                  </p>
                </div>
              </div>
            )}

            {/* General GitHub Error */}
            {githubError && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-300 text-xs">
                <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
                <span>{githubError}</span>
              </div>
            )}

            {/* Discovery Stats Bar */}
            {githubStats && githubStats.total_repositories > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-gray-400 font-medium">Total Discovered Repos</span>
                  <span className="text-xl font-bold text-white mt-1">{githubStats.total_repositories}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-amber-300 font-medium flex items-center gap-1">
                    <Star className="w-3.5 h-3.5" /> Total Stars
                  </span>
                  <span className="text-xl font-bold text-amber-400 mt-1">{githubStats.total_stars.toLocaleString()}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-blue-300 font-medium flex items-center gap-1">
                    <GitFork className="w-3.5 h-3.5" /> Total Forks
                  </span>
                  <span className="text-xl font-bold text-blue-400 mt-1">{githubStats.total_forks.toLocaleString()}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0E1424] border border-[#1F293D] flex flex-col justify-between">
                  <span className="text-[11px] text-purple-300 font-medium">Distinct Languages</span>
                  <span className="text-xl font-bold text-purple-400 mt-1">{Object.keys(githubStats.language_distribution).length}</span>
                </div>
              </div>
            )}

            {/* Filters Bar */}
            <div className="p-4 rounded-xl bg-[#0E1424] border border-[#1F293D] space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                {/* Language Filter */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-xs text-gray-400 font-medium mr-1 flex items-center gap-1">
                    <Filter className="w-3.5 h-3.5" /> Language:
                  </span>
                  {['all', 'Python', 'TypeScript', 'JavaScript', 'C++', 'Go', 'Rust', 'Java'].map((lang) => (
                    <button
                      key={lang}
                      onClick={() => {
                        setSelectedLanguage(lang);
                        loadGitHub(1, lang, selectedMinStars, includeArchived, includeForks, githubSearchKeyword, githubSortBy);
                      }}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                        selectedLanguage === lang
                          ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                          : 'bg-[#151D30] text-gray-400 hover:text-white hover:bg-[#1E2942]'
                      }`}
                    >
                      {lang === 'all' ? 'All Languages' : lang}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-3">
                  {/* Min Stars Filter */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-gray-400 font-medium">Min Stars:</span>
                    <select
                      value={selectedMinStars}
                      onChange={(e) => {
                        const val = parseInt(e.target.value, 10);
                        setSelectedMinStars(val);
                        loadGitHub(1, selectedLanguage, val, includeArchived, includeForks, githubSearchKeyword, githubSortBy);
                      }}
                      className="bg-[#151D30] text-xs text-gray-200 border border-[#1F293D] rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-purple-500"
                    >
                      <option value={0}>Any Stars</option>
                      <option value={50}>≥ 50 Stars</option>
                      <option value={100}>≥ 100 Stars</option>
                      <option value={500}>≥ 500 Stars</option>
                      <option value={1000}>≥ 1,000 Stars</option>
                      <option value={5000}>≥ 5,000 Stars</option>
                    </select>
                  </div>

                  {/* Sort By Dropdown */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-gray-400 font-medium">Sort:</span>
                    <select
                      value={githubSortBy}
                      onChange={(e) => {
                        const val = e.target.value;
                        setGithubSortBy(val);
                        loadGitHub(1, selectedLanguage, selectedMinStars, includeArchived, includeForks, githubSearchKeyword, val);
                      }}
                      className="bg-[#151D30] text-xs text-gray-200 border border-[#1F293D] rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-purple-500"
                    >
                      <option value="stars">Most Stars</option>
                      <option value="forks">Most Forks</option>
                      <option value="updated">Recently Updated</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Search + Flags Controls */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-[#1F293D]/60">
                <div className="relative w-full sm:w-80">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type="text"
                    placeholder="Filter repositories by name or topic..."
                    value={githubSearchKeyword}
                    onChange={(e) => {
                      setGithubSearchKeyword(e.target.value);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        loadGitHub(1, selectedLanguage, selectedMinStars, includeArchived, includeForks, githubSearchKeyword, githubSortBy);
                      }
                    }}
                    className="w-full bg-[#151D30] text-xs text-gray-200 pl-8 pr-3 py-1.5 rounded-lg border border-[#1F293D] focus:outline-none focus:border-purple-500 placeholder-gray-500"
                  />
                </div>

                <div className="flex items-center gap-4 text-xs text-gray-300">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={includeArchived}
                      onChange={(e) => {
                        setIncludeArchived(e.target.checked);
                        loadGitHub(1, selectedLanguage, selectedMinStars, e.target.checked, includeForks, githubSearchKeyword, githubSortBy);
                      }}
                      className="rounded bg-[#151D30] border-[#1F293D] text-purple-600 focus:ring-0 focus:ring-offset-0"
                    />
                    <span>Include Archived</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={includeForks}
                      onChange={(e) => {
                        setIncludeForks(e.target.checked);
                        loadGitHub(1, selectedLanguage, selectedMinStars, includeArchived, e.target.checked, githubSearchKeyword, githubSortBy);
                      }}
                      className="rounded bg-[#151D30] border-[#1F293D] text-purple-600 focus:ring-0 focus:ring-offset-0"
                    />
                    <span>Include Forks</span>
                  </label>

                  {/* Reset Filters */}
                  {(selectedLanguage !== 'all' || selectedMinStars > 0 || includeArchived || includeForks || githubSearchKeyword) && (
                    <button
                      onClick={() => {
                        setSelectedLanguage('all');
                        setSelectedMinStars(0);
                        setIncludeArchived(false);
                        setIncludeForks(false);
                        setGithubSearchKeyword('');
                        loadGitHub(1, 'all', 0, false, false, '', githubSortBy);
                      }}
                      className="text-purple-400 hover:text-purple-300 text-xs font-medium underline"
                    >
                      Reset Filters
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Repositories List */}
            {githubLoading ? (
              <div className="py-12 flex flex-col items-center justify-center gap-3 text-gray-400">
                <RefreshCw className="w-6 h-6 animate-spin text-purple-400" />
                <span className="text-xs">Loading discovered repositories...</span>
              </div>
            ) : githubRepos.length === 0 ? (
              <div className="py-12 px-4 rounded-xl bg-[#0E1424] border border-[#1F293D] text-center space-y-3">
                <Github className="w-10 h-10 text-gray-600 mx-auto" />
                <div>
                  <h4 className="text-sm font-semibold text-white">No GitHub Repositories Found</h4>
                  <p className="text-xs text-gray-400 mt-1 max-w-md mx-auto">
                    {githubTotal === 0
                      ? 'No GitHub repositories have been discovered for this project yet. Click "Search GitHub Repositories" to start multi-query discovery.'
                      : 'No repositories match your active filter criteria. Try resetting filters.'}
                  </p>
                </div>
                {githubTotal === 0 && (
                  <button
                    onClick={handleSearchGitHub}
                    disabled={githubSearching}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium transition-colors"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${githubSearching ? 'animate-spin' : ''}`} />
                    Start GitHub Discovery
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  {githubRepos.map((repo) => (
                    <div
                      key={repo.id || repo.github_repository_id}
                      className="p-5 rounded-xl bg-[#0E1424] border border-[#1F293D] hover:border-purple-500/40 transition-all duration-200 space-y-3"
                    >
                      {/* Top Row: Owner / Repo Name + Metrics */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2.5">
                          {repo.owner_avatar_url ? (
                            <img
                              src={repo.owner_avatar_url}
                              alt={repo.owner_login}
                              className="w-6 h-6 rounded-full border border-[#1F293D]"
                            />
                          ) : (
                            <Github className="w-5 h-5 text-gray-400" />
                          )}
                          <a
                            href={repo.html_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-semibold text-white hover:text-purple-400 inline-flex items-center gap-1.5 transition-colors group"
                          >
                            <span>{repo.full_name}</span>
                            <ExternalLink className="w-3.5 h-3.5 text-gray-500 group-hover:text-purple-400 flex-shrink-0" />
                          </a>

                          {repo.archived && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30">
                              archived
                            </span>
                          )}
                          {repo.fork && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-400 border border-blue-500/30">
                              fork
                            </span>
                          )}
                        </div>

                        {/* Star / Fork / Issue counters */}
                        <div className="flex items-center gap-3 text-xs text-gray-400">
                          <span className="inline-flex items-center gap-1 text-amber-300 font-medium">
                            <Star className="w-3.5 h-3.5 fill-amber-400/20 text-amber-400" />
                            {repo.stargazers_count.toLocaleString()}
                          </span>
                          <span className="inline-flex items-center gap-1 text-blue-300 font-medium">
                            <GitFork className="w-3.5 h-3.5 text-blue-400" />
                            {repo.forks_count.toLocaleString()}
                          </span>
                          {repo.open_issues_count > 0 && (
                            <span className="inline-flex items-center gap-1 text-gray-400">
                              <AlertCircle className="w-3.5 h-3.5 text-gray-500" />
                              {repo.open_issues_count}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-xs text-gray-300 leading-relaxed">
                        {repo.description || (
                          <span className="italic text-gray-500">No repository description provided.</span>
                        )}
                      </p>

                      {/* Topics */}
                      {repo.topics && repo.topics.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {repo.topics.map((topic, tidx) => (
                            <span
                              key={tidx}
                              className="px-2 py-0.5 rounded-md text-[11px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Footer Row: Language, License, Dates */}
                      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#1F293D]/60 text-[11px] text-gray-400">
                        <div className="flex items-center gap-4 flex-wrap">
                          {repo.language && (
                            <span className="inline-flex items-center gap-1.5 text-gray-300 font-medium">
                              <span className="w-2 h-2 rounded-full bg-purple-400" />
                              {repo.language}
                            </span>
                          )}
                          {repo.license_name && (
                            <span className="text-gray-400 font-mono">
                              {repo.license_spdx || repo.license_name}
                            </span>
                          )}
                          {repo.updated_at_repo && (
                            <span className="text-gray-500">
                              Updated {new Date(repo.updated_at_repo).toLocaleDateString()}
                            </span>
                          )}
                        </div>

                        <a
                          href={repo.html_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-purple-400 hover:text-purple-300 font-medium transition-colors"
                        >
                          <span>View on GitHub</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination Controls */}
                <div className="flex items-center justify-between pt-3 border-t border-[#1F293D] text-xs text-gray-400">
                  <span>
                    Showing {(githubPage - 1) * 10 + 1} to {Math.min(githubPage * 10, githubTotal)} of {githubTotal} repositories
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => loadGitHub(githubPage - 1)}
                      disabled={githubPage <= 1}
                      className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="px-2 font-mono text-gray-300">
                      Page {githubPage} of {Math.max(1, Math.ceil(githubTotal / 10))}
                    </span>
                    <button
                      onClick={() => loadGitHub(githubPage + 1)}
                      disabled={githubPage * 10 >= githubTotal}
                      className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ======================================================== */}
          {/* SECTION 14: GitHub Repository Deep Analysis & Innovation Gaps */}
          {/* ======================================================== */}
          <div className="bg-[#111827] border border-[#1F293D] rounded-xl p-6 space-y-6">
            {/* Header & Trigger Action */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#1F293D]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                    <Compass className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">
                    Repository Deep Analysis & Innovation Gaps
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    Phase 4.3
                  </span>
                  {repoAnalysisMode === 'deterministic_fallback' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      Heuristic Mode
                    </span>
                  )}
                  {repoAnalysisMode === 'ai_enhanced' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      AI Enhanced
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  In-depth architectural decomposition, tech stack evidence extraction, multi-factor similarity alignment, and open innovation gap synthesis.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleDeepAnalyze}
                  disabled={repoAnalyzing || githubTotal === 0}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <RefreshCw className={`w-4 h-4 ${repoAnalyzing ? 'animate-spin' : ''}`} />
                  <span>
                    {repoAnalyzing
                      ? 'Analyzing Repositories...'
                      : repoAnalyses.length > 0
                      ? 'Re-analyze Repositories'
                      : 'Run Deep Repository Analysis'}
                  </span>
                </button>
              </div>
            </div>

            {/* Error Message */}
            {repoAnalysisError && (
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <div className="space-y-1">
                  <p className="font-semibold">Analysis Notice</p>
                  <p>{repoAnalysisError}</p>
                </div>
              </div>
            )}

            {/* Batch Errors Warning */}
            {Object.keys(repoAnalysisBatchErrors).length > 0 && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-1">
                <div className="flex items-center gap-1.5 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Some repositories could not be analyzed:</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 pl-2 text-[11px] text-amber-200/80">
                  {Object.entries(repoAnalysisBatchErrors).map(([repoName, err]) => (
                    <li key={repoName}>
                      <span className="font-mono">{repoName}</span>: {err}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Stats Overview Grid */}
            {repoAnalysisStats && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Analyzed Repos</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-white font-mono">
                      {repoAnalysisStats.total_analyzed_repositories}
                    </span>
                    <span className="text-xs text-gray-500">/ {githubTotal}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Avg Similarity</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-blue-400 font-mono">
                      {repoAnalysisStats.average_similarity_score}%
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Detected Tech</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-emerald-400 font-mono">
                      {Object.keys(repoAnalysisStats.technology_distribution).length}
                    </span>
                    <span className="text-xs text-gray-500">tools</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Extracted Features</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-purple-400 font-mono">
                      {repoAnalysisStats.total_features_extracted}
                    </span>
                    <span className="text-xs text-gray-500">features</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 col-span-2 sm:col-span-1">
                  <span className="text-[11px] text-gray-400 font-medium">Innovation Gaps</span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-rose-400 font-mono">
                      {repoAnalysisStats.innovation_gaps_count}
                    </span>
                    <span className="text-[10px] text-rose-300/80 font-mono">
                      ({repoAnalysisStats.gaps_by_priority['high'] || 0} High)
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Not Yet Discovered */}
            {githubTotal === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-3">
                <Github className="w-10 h-10 text-gray-600 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    No Discovered Repositories Available
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Please discover relevant GitHub repositories in Section 13 above before launching deep repository analysis and innovation gap synthesis.
                  </p>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Discovered but Analysis Not Run Yet */}
            {githubTotal > 0 && repoAnalyses.length === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-4">
                <Compass className="w-10 h-10 text-blue-500/60 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    Ready for Deep Repository Analysis
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Analyze the {githubTotal} discovered GitHub repositories to extract real-world technical stacks, architecture topologies, and detect unaddressed innovation gaps.
                  </p>
                </div>
                <button
                  onClick={handleDeepAnalyze}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Start Deep Repository Analysis</span>
                </button>
              </div>
            )}

            {/* Loading Indicator */}
            {repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/60 border border-[#1F293D] text-center space-y-3">
                <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-white">
                    Conducting Deep Repository Intelligence...
                  </h4>
                  <p className="text-xs text-gray-400 max-w-md mx-auto">
                    Retrieving READMEs, scanning dependency manifests, mapping 7-category technology signatures, and synthesizing comparative innovation gaps.
                  </p>
                </div>
              </div>
            )}

            {/* SUB-SECTION A: Innovation Gaps Identified */}
            {innovationGaps.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-amber-400" />
                      <h4 className="text-sm font-semibold text-white">
                        Synthesized Innovation Gaps ({innovationGaps.length})
                      </h4>
                    </div>
                    <p className="text-xs text-gray-400">
                      Unaddressed capabilities, architectural shortcomings, and differentiation opportunities not found in analyzed open-source repositories.
                    </p>
                  </div>

                  {/* Priority & Category Filter Pills */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="flex items-center rounded-lg bg-[#151D30] p-1 border border-[#1F293D] text-[11px]">
                      {(['all', 'high', 'medium', 'low'] as const).map((p) => (
                        <button
                          key={p}
                          onClick={() => {
                            setSelectedGapPriority(p);
                            loadInnovationGaps(p, selectedGapCategory);
                          }}
                          className={`px-2.5 py-1 rounded-md font-medium capitalize transition-colors ${
                            selectedGapPriority === p
                              ? 'bg-blue-600 text-white'
                              : 'text-gray-400 hover:text-white'
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>

                    <select
                      value={selectedGapCategory}
                      onChange={(e) => {
                        setSelectedGapCategory(e.target.value);
                        loadInnovationGaps(selectedGapPriority, e.target.value);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-gray-300 focus:outline-none focus:border-blue-500"
                    >
                      <option value="all">All Categories</option>
                      <option value="missing_feature">Missing Feature</option>
                      <option value="partially_implemented">Partially Implemented</option>
                      <option value="improvement_opportunity">Improvement Opportunity</option>
                      <option value="differentiating_feature">Differentiating Feature</option>
                    </select>
                  </div>
                </div>

                {/* Innovation Gaps Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {innovationGaps.map((gap, gIdx) => {
                    const priorityColor =
                      gap.priority === 'high'
                        ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        : gap.priority === 'medium'
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                        : 'bg-blue-500/10 text-blue-300 border-blue-500/30';

                    const categoryBadge =
                      gap.category === 'missing_feature'
                        ? { label: 'Missing Feature', style: 'bg-rose-500/10 text-rose-300 border-rose-500/20' }
                        : gap.category === 'partially_implemented'
                        ? { label: 'Partially Implemented', style: 'bg-amber-500/10 text-amber-300 border-amber-500/20' }
                        : gap.category === 'improvement_opportunity'
                        ? { label: 'Improvement Opportunity', style: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20' }
                        : { label: 'Differentiating Feature', style: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' };

                    return (
                      <div
                        key={gap.id || gIdx}
                        className="p-4 rounded-xl bg-[#151D30] border border-[#1F293D] hover:border-blue-500/30 transition-all space-y-3 flex flex-col justify-between"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${categoryBadge.style}`}>
                              {categoryBadge.label}
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span className={`px-2 py-0.5 rounded-md text-[10px] font-mono uppercase font-bold border ${priorityColor}`}>
                                {gap.priority} Priority
                              </span>
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-gray-800 text-gray-300 border border-gray-700">
                                {gap.confidence_level} Confidence
                              </span>
                            </div>
                          </div>

                          <h5 className="text-sm font-semibold text-white leading-snug">
                            {gap.gap_title}
                          </h5>

                          <p className="text-xs text-gray-300 leading-relaxed">
                            {gap.description}
                          </p>
                        </div>

                        <div className="space-y-2.5 pt-2 border-t border-[#1F293D]/60 text-xs">
                          {/* Why It Matters */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wide">
                              Why It Matters
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.why_it_matters}
                            </p>
                          </div>

                          {/* Suggested Implementation */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wide">
                              Suggested Implementation
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.suggested_implementation}
                            </p>
                          </div>

                          {/* Supporting Evidence Citations */}
                          {gap.supporting_evidence && gap.supporting_evidence.length > 0 && (
                            <div className="space-y-1 pt-1">
                              <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                                Supporting Evidence
                              </span>
                              <div className="space-y-1">
                                {gap.supporting_evidence.map((ev, evIdx) => (
                                  <div
                                    key={evIdx}
                                    className="p-1.5 rounded bg-[#0B0F19]/80 border border-[#1F293D] text-[10px] font-mono text-gray-400 leading-tight"
                                  >
                                    {ev}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* SUB-SECTION B: Repository Deep Dive Cards */}
            {repoAnalyses.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-purple-400" />
                    <h4 className="text-sm font-semibold text-white">
                      Deep Analyzed Repositories ({repoAnalysesTotal}) {repoAnalysesLoading && <span className="text-xs text-blue-400 font-normal animate-pulse">(updating...)</span>}
                    </h4>
                  </div>
                  <span className="text-xs text-gray-400 font-mono">
                    Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                  </span>
                </div>

                <div className="space-y-4">
                  {repoAnalyses.map((item, idx) => {
                    const isExpanded = expandedRepoAnalyses[item.id || String(idx)] ?? true;
                    const isArchExpanded = expandedArchitecture[item.id || String(idx)] ?? false;
                    const overallSim = item.similarity?.overall_score ?? 0;

                    return (
                      <div
                        key={item.id || idx}
                        className="rounded-xl bg-[#151D30] border border-[#1F293D] overflow-hidden transition-all"
                      >
                        {/* Repository Deep Analysis Header */}
                        <div className="p-4 bg-[#111827]/70 border-b border-[#1F293D] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <GitBranch className="w-4 h-4 text-blue-400 shrink-0" />
                              <a
                                href={item.readme_url || `https://github.com/${item.repo_full_name}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-semibold text-white hover:text-blue-400 font-mono transition-colors flex items-center gap-1"
                              >
                                <span>{item.repo_full_name}</span>
                                <ExternalLink className="w-3 h-3 text-gray-500" />
                              </a>
                              {item.readme_present ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                  README ({item.readme_size ? `${Math.round(item.readme_size / 1024)} KB` : 'Verified'})
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-700/40 text-gray-400 border border-gray-700">
                                  No README
                                </span>
                              )}
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20">
                                {item.analysis_mode === 'deterministic_fallback' ? 'Heuristic' : 'AI-Enhanced'}
                              </span>
                            </div>
                            {item.summary && (
                              <p className="text-xs text-gray-400 leading-relaxed">
                                {item.summary}
                              </p>
                            )}
                          </div>

                          <div className="flex items-center gap-3 shrink-0">
                            {/* Similarity Score Pill */}
                            {item.similarity && (
                              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D]">
                                <span className="text-[11px] text-gray-400">Match:</span>
                                <span className="text-sm font-bold font-mono text-blue-400">
                                  {overallSim}%
                                </span>
                              </div>
                            )}

                            <button
                              onClick={() => toggleRepoExpand(item.id || String(idx))}
                              className="p-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-gray-400 hover:text-white transition-colors"
                            >
                              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>
                          </div>
                        </div>

                        {/* Collapsible Details Body */}
                        {isExpanded && (
                          <div className="p-4 space-y-4">
                            {/* Multi-Factor Similarity Alignment Breakdown */}
                            {item.similarity && (
                              <div className="p-3.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-3">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-1.5">
                                    <TrendingUp className="w-4 h-4 text-blue-400" />
                                    <span className="text-xs font-semibold text-white">
                                      Multi-Factor Similarity Alignment ({item.similarity.overall_score}%)
                                    </span>
                                  </div>
                                  <span className="text-[11px] text-gray-400">
                                    Weighted Composite Model
                                  </span>
                                </div>

                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Problem (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.problem_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-blue-500 rounded-full"
                                        style={{ width: `${item.similarity.problem_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Feature (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.feature_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-indigo-500 rounded-full"
                                        style={{ width: `${item.similarity.feature_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Tech Stack (25%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.tech_stack_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-purple-500 rounded-full"
                                        style={{ width: `${item.similarity.tech_stack_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Domain (15%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.domain_similarity}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-cyan-500 rounded-full"
                                        style={{ width: `${item.similarity.domain_similarity}%` }}
                                      />
                                    </div>
                                  </div>
                                </div>

                                {item.similarity.similarity_explanation && (
                                  <p className="text-[11px] text-gray-400 italic leading-relaxed pt-1 border-t border-[#1F293D]/60">
                                    {item.similarity.similarity_explanation}
                                  </p>
                                )}
                              </div>
                            )}

                            {/* Problem Statement */}
                            {item.problem_statement && (
                              <div className="space-y-1 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Problem Addressed by Repository
                                </span>
                                <p className="text-gray-300 leading-relaxed bg-[#0B0F19]/50 p-2.5 rounded-lg border border-[#1F293D]">
                                  {item.problem_statement}
                                </p>
                              </div>
                            )}

                            {/* 7 Standard Technology Stack Categories */}
                            <div className="space-y-2 text-xs">
                              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                Detected Technical Stack (Evidence Traceable)
                              </span>

                              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                                {/* Languages */}
                                {item.detected_technologies?.programming_languages?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-purple-400">
                                      <Code2 className="w-3.5 h-3.5" />
                                      <span>Languages</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.programming_languages.map((l, lIdx) => (
                                        <span
                                          key={lIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20"
                                        >
                                          {l}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Backend */}
                                {item.detected_technologies?.backend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-blue-400">
                                      <Cpu className="w-3.5 h-3.5" />
                                      <span>Backend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.backend_frameworks.map((b, bIdx) => (
                                        <span
                                          key={bIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20"
                                        >
                                          {b}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Frontend */}
                                {item.detected_technologies?.frontend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400">
                                      <Layers className="w-3.5 h-3.5" />
                                      <span>Frontend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.frontend_frameworks.map((f, fIdx) => (
                                        <span
                                          key={fIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                                        >
                                          {f}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* AI / ML */}
                                {item.detected_technologies?.ai_ml_libraries?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-rose-400">
                                      <Sparkles className="w-3.5 h-3.5" />
                                      <span>AI / ML Libraries</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.ai_ml_libraries.map((ai, aiIdx) => (
                                        <span
                                          key={aiIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-rose-500/10 text-rose-300 border border-rose-500/20"
                                        >
                                          {ai}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Databases */}
                                {item.detected_technologies?.databases?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-400">
                                      <Database className="w-3.5 h-3.5" />
                                      <span>Databases & Storage</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.databases.map((db, dbIdx) => (
                                        <span
                                          key={dbIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20"
                                        >
                                          {db}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Cloud & DevOps */}
                                {(item.detected_technologies?.cloud_deployment?.length > 0 ||
                                  item.detected_technologies?.devops_tools?.length > 0) && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-cyan-400">
                                      <Cloud className="w-3.5 h-3.5" />
                                      <span>Cloud & DevOps</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {[
                                        ...(item.detected_technologies.cloud_deployment || []),
                                        ...(item.detected_technologies.devops_tools || []),
                                      ].map((tool, tIdx) => (
                                        <span
                                          key={tIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/20"
                                        >
                                          {tool}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Extracted Features List */}
                            {item.features && item.features.length > 0 && (
                              <div className="space-y-2 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Extracted Repository Features ({item.features.length})
                                </span>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  {item.features.map((feat, fIdx) => (
                                    <div
                                      key={fIdx}
                                      className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1"
                                    >
                                      <div className="flex items-center justify-between gap-1">
                                        <span className="font-semibold text-white text-xs truncate">
                                          {feat.feature_name}
                                        </span>
                                        <div className="flex items-center gap-1 shrink-0">
                                          {feat.is_documented ? (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                              Doc
                                            </span>
                                          ) : (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-gray-800 text-gray-400 border border-gray-700">
                                              Inferred
                                            </span>
                                          )}
                                          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-blue-500/10 text-blue-300">
                                            {Math.round(feat.confidence_score * 100)}%
                                          </span>
                                        </div>
                                      </div>
                                      <p className="text-[11px] text-gray-400 leading-snug">
                                        {feat.description}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Architecture Topology Accordion */}
                            {item.architecture && (
                              <div className="pt-2 border-t border-[#1F293D]/60 space-y-2">
                                <button
                                  onClick={() => toggleArchitectureExpand(item.id || String(idx))}
                                  className="flex items-center justify-between w-full text-xs text-gray-400 hover:text-white transition-colors"
                                >
                                  <div className="flex items-center gap-1.5">
                                    <Layers className="w-3.5 h-3.5 text-blue-400" />
                                    <span className="font-medium">System Architecture Topology</span>
                                  </div>
                                  {isArchExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                </button>

                                {isArchExpanded && (
                                  <div className="p-3 rounded-lg bg-[#0B0F19] border border-[#1F293D] grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                                    {item.architecture.frontend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Frontend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.frontend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.backend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Backend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.backend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.database_layer && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Database</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.database_layer}</p>
                                      </div>
                                    )}
                                    {item.architecture.ai_ml_pipeline && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">AI/ML Pipeline</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.ai_ml_pipeline}</p>
                                      </div>
                                    )}
                                    {item.architecture.deployment_infrastructure && (
                                      <div className="space-y-0.5 sm:col-span-2">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Deployment</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.deployment_infrastructure}</p>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Pagination Controls for Repository Analyses */}
                {repoAnalysesTotal > 10 && (
                  <div className="flex items-center justify-between pt-3 border-t border-[#1F293D] text-xs text-gray-400">
                    <span>
                      Showing {(repoAnalysesPage - 1) * 10 + 1} to{' '}
                      {Math.min(repoAnalysesPage * 10, repoAnalysesTotal)} of {repoAnalysesTotal} analyzed repositories
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage - 1)}
                        disabled={repoAnalysesPage <= 1}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="px-2 font-mono text-gray-300">
                        Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                      </span>
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage + 1)}
                        disabled={repoAnalysesPage * 10 >= repoAnalysesTotal}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ======================================================== */}
          {/* SECTION 14: GitHub Repository Deep Analysis & Innovation Gaps */}
          {/* ======================================================== */}
          <div className="bg-[#111827] border border-[#1F293D] rounded-xl p-6 space-y-6">
            {/* Header & Trigger Action */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#1F293D]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                    <Compass className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">
                    Repository Deep Analysis & Innovation Gaps
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    Phase 4.3
                  </span>
                  {repoAnalysisMode === 'deterministic_fallback' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      Heuristic Mode
                    </span>
                  )}
                  {repoAnalysisMode === 'ai_enhanced' && (
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      AI Enhanced
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  In-depth architectural decomposition, tech stack evidence extraction, multi-factor similarity alignment, and open innovation gap synthesis.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleDeepAnalyze}
                  disabled={repoAnalyzing || githubTotal === 0}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <RefreshCw className={`w-4 h-4 ${repoAnalyzing ? 'animate-spin' : ''}`} />
                  <span>
                    {repoAnalyzing
                      ? 'Analyzing Repositories...'
                      : repoAnalyses.length > 0
                      ? 'Re-analyze Repositories'
                      : 'Run Deep Repository Analysis'}
                  </span>
                </button>
              </div>
            </div>

            {/* Error Message */}
            {repoAnalysisError && (
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <div className="space-y-1">
                  <p className="font-semibold">Analysis Notice</p>
                  <p>{repoAnalysisError}</p>
                </div>
              </div>
            )}

            {/* Batch Errors Warning */}
            {Object.keys(repoAnalysisBatchErrors).length > 0 && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-1">
                <div className="flex items-center gap-1.5 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Some repositories could not be analyzed:</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 pl-2 text-[11px] text-amber-200/80">
                  {Object.entries(repoAnalysisBatchErrors).map(([repoName, err]) => (
                    <li key={repoName}>
                      <span className="font-mono">{repoName}</span>: {err}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Stats Overview Grid */}
            {repoAnalysisStats && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Analyzed Repos</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-white font-mono">
                      {repoAnalysisStats.total_analyzed_repositories}
                    </span>
                    <span className="text-xs text-gray-500">/ {githubTotal}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Avg Similarity</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-blue-400 font-mono">
                      {repoAnalysisStats.average_similarity_score}%
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Detected Tech</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-emerald-400 font-mono">
                      {Object.keys(repoAnalysisStats.technology_distribution).length}
                    </span>
                    <span className="text-xs text-gray-500">tools</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1">
                  <span className="text-[11px] text-gray-400 font-medium">Extracted Features</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-purple-400 font-mono">
                      {repoAnalysisStats.total_features_extracted}
                    </span>
                    <span className="text-xs text-gray-500">features</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 col-span-2 sm:col-span-1">
                  <span className="text-[11px] text-gray-400 font-medium">Innovation Gaps</span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-rose-400 font-mono">
                      {repoAnalysisStats.innovation_gaps_count}
                    </span>
                    <span className="text-[10px] text-rose-300/80 font-mono">
                      ({repoAnalysisStats.gaps_by_priority['high'] || 0} High)
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Not Yet Discovered */}
            {githubTotal === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-3">
                <Github className="w-10 h-10 text-gray-600 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    No Discovered Repositories Available
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Please discover relevant GitHub repositories in Section 13 above before launching deep repository analysis and innovation gap synthesis.
                  </p>
                </div>
              </div>
            )}

            {/* Empty State: Repositories Discovered but Analysis Not Run Yet */}
            {githubTotal > 0 && repoAnalyses.length === 0 && !repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/40 border border-dashed border-[#1F293D] text-center space-y-4">
                <Compass className="w-10 h-10 text-blue-500/60 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">
                    Ready for Deep Repository Analysis
                  </h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Analyze the {githubTotal} discovered GitHub repositories to extract real-world technical stacks, architecture topologies, and detect unaddressed innovation gaps.
                  </p>
                </div>
                <button
                  onClick={handleDeepAnalyze}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Start Deep Repository Analysis</span>
                </button>
              </div>
            )}

            {/* Loading Indicator */}
            {repoAnalyzing && (
              <div className="p-8 rounded-lg bg-[#151D30]/60 border border-[#1F293D] text-center space-y-3">
                <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-white">
                    Conducting Deep Repository Intelligence...
                  </h4>
                  <p className="text-xs text-gray-400 max-w-md mx-auto">
                    Retrieving READMEs, scanning dependency manifests, mapping 7-category technology signatures, and synthesizing comparative innovation gaps.
                  </p>
                </div>
              </div>
            )}

            {/* SUB-SECTION A: Innovation Gaps Identified */}
            {innovationGaps.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-amber-400" />
                      <h4 className="text-sm font-semibold text-white">
                        Synthesized Innovation Gaps ({innovationGaps.length})
                      </h4>
                    </div>
                    <p className="text-xs text-gray-400">
                      Unaddressed capabilities, architectural shortcomings, and differentiation opportunities not found in analyzed open-source repositories.
                    </p>
                  </div>

                  {/* Priority & Category Filter Pills */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="flex items-center rounded-lg bg-[#151D30] p-1 border border-[#1F293D] text-[11px]">
                      {(['all', 'high', 'medium', 'low'] as const).map((p) => (
                        <button
                          key={p}
                          onClick={() => {
                            setSelectedGapPriority(p);
                            loadInnovationGaps(p, selectedGapCategory);
                          }}
                          className={`px-2.5 py-1 rounded-md font-medium capitalize transition-colors ${
                            selectedGapPriority === p
                              ? 'bg-blue-600 text-white'
                              : 'text-gray-400 hover:text-white'
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>

                    <select
                      value={selectedGapCategory}
                      onChange={(e) => {
                        setSelectedGapCategory(e.target.value);
                        loadInnovationGaps(selectedGapPriority, e.target.value);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-gray-300 focus:outline-none focus:border-blue-500"
                    >
                      <option value="all">All Categories</option>
                      <option value="missing_feature">Missing Feature</option>
                      <option value="partially_implemented">Partially Implemented</option>
                      <option value="improvement_opportunity">Improvement Opportunity</option>
                      <option value="differentiating_feature">Differentiating Feature</option>
                    </select>
                  </div>
                </div>

                {/* Innovation Gaps Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {innovationGaps.map((gap, gIdx) => {
                    const priorityColor =
                      gap.priority === 'high'
                        ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        : gap.priority === 'medium'
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                        : 'bg-blue-500/10 text-blue-300 border-blue-500/30';

                    const categoryBadge =
                      gap.category === 'missing_feature'
                        ? { label: 'Missing Feature', style: 'bg-rose-500/10 text-rose-300 border-rose-500/20' }
                        : gap.category === 'partially_implemented'
                        ? { label: 'Partially Implemented', style: 'bg-amber-500/10 text-amber-300 border-amber-500/20' }
                        : gap.category === 'improvement_opportunity'
                        ? { label: 'Improvement Opportunity', style: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20' }
                        : { label: 'Differentiating Feature', style: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' };

                    return (
                      <div
                        key={gap.id || gIdx}
                        className="p-4 rounded-xl bg-[#151D30] border border-[#1F293D] hover:border-blue-500/30 transition-all space-y-3 flex flex-col justify-between"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${categoryBadge.style}`}>
                              {categoryBadge.label}
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span className={`px-2 py-0.5 rounded-md text-[10px] font-mono uppercase font-bold border ${priorityColor}`}>
                                {gap.priority} Priority
                              </span>
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-gray-800 text-gray-300 border border-gray-700">
                                {gap.confidence_level} Confidence
                              </span>
                            </div>
                          </div>

                          <h5 className="text-sm font-semibold text-white leading-snug">
                            {gap.gap_title}
                          </h5>

                          <p className="text-xs text-gray-300 leading-relaxed">
                            {gap.description}
                          </p>
                        </div>

                        <div className="space-y-2.5 pt-2 border-t border-[#1F293D]/60 text-xs">
                          {/* Why It Matters */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wide">
                              Why It Matters
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.why_it_matters}
                            </p>
                          </div>

                          {/* Suggested Implementation */}
                          <div className="space-y-0.5">
                            <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wide">
                              Suggested Implementation
                            </span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">
                              {gap.suggested_implementation}
                            </p>
                          </div>

                          {/* Supporting Evidence Citations */}
                          {gap.supporting_evidence && gap.supporting_evidence.length > 0 && (
                            <div className="space-y-1 pt-1">
                              <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                                Supporting Evidence
                              </span>
                              <div className="space-y-1">
                                {gap.supporting_evidence.map((ev, evIdx) => (
                                  <div
                                    key={evIdx}
                                    className="p-1.5 rounded bg-[#0B0F19]/80 border border-[#1F293D] text-[10px] font-mono text-gray-400 leading-tight"
                                  >
                                    {ev}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* SUB-SECTION B: Repository Deep Dive Cards */}
            {repoAnalyses.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-[#1F293D]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-purple-400" />
                    <h4 className="text-sm font-semibold text-white">
                      Deep Analyzed Repositories ({repoAnalysesTotal})
                    </h4>
                  </div>
                  <span className="text-xs text-gray-400 font-mono">
                    Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                  </span>
                </div>

                <div className="space-y-4">
                  {repoAnalyses.map((item, idx) => {
                    const isExpanded = expandedRepoAnalyses[item.id || String(idx)] ?? true;
                    const isArchExpanded = expandedArchitecture[item.id || String(idx)] ?? false;
                    const overallSim = item.similarity?.overall_score ?? 0;

                    return (
                      <div
                        key={item.id || idx}
                        className="rounded-xl bg-[#151D30] border border-[#1F293D] overflow-hidden transition-all"
                      >
                        {/* Repository Deep Analysis Header */}
                        <div className="p-4 bg-[#111827]/70 border-b border-[#1F293D] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <GitBranch className="w-4 h-4 text-blue-400 shrink-0" />
                              <a
                                href={item.readme_url || `https://github.com/${item.repo_full_name}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-semibold text-white hover:text-blue-400 font-mono transition-colors flex items-center gap-1"
                              >
                                <span>{item.repo_full_name}</span>
                                <ExternalLink className="w-3 h-3 text-gray-500" />
                              </a>
                              {item.readme_present ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                  README ({item.readme_size ? `${Math.round(item.readme_size / 1024)} KB` : 'Verified'})
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-700/40 text-gray-400 border border-gray-700">
                                  No README
                                </span>
                              )}
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20">
                                {item.analysis_mode === 'deterministic_fallback' ? 'Heuristic' : 'AI-Enhanced'}
                              </span>
                            </div>
                            {item.summary && (
                              <p className="text-xs text-gray-400 leading-relaxed">
                                {item.summary}
                              </p>
                            )}
                          </div>

                          <div className="flex items-center gap-3 shrink-0">
                            {/* Similarity Score Pill */}
                            {item.similarity && (
                              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D]">
                                <span className="text-[11px] text-gray-400">Match:</span>
                                <span className="text-sm font-bold font-mono text-blue-400">
                                  {overallSim}%
                                </span>
                              </div>
                            )}

                            <button
                              onClick={() => toggleRepoExpand(item.id || String(idx))}
                              className="p-1.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-gray-400 hover:text-white transition-colors"
                            >
                              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>
                          </div>
                        </div>

                        {/* Collapsible Details Body */}
                        {isExpanded && (
                          <div className="p-4 space-y-4">
                            {/* Multi-Factor Similarity Alignment Breakdown */}
                            {item.similarity && (
                              <div className="p-3.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-3">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-1.5">
                                    <TrendingUp className="w-4 h-4 text-blue-400" />
                                    <span className="text-xs font-semibold text-white">
                                      Multi-Factor Similarity Alignment ({item.similarity.overall_score}%)
                                    </span>
                                  </div>
                                  <span className="text-[11px] text-gray-400">
                                    Weighted Composite Model
                                  </span>
                                </div>

                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Problem (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.problem_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-blue-500 rounded-full"
                                        style={{ width: `${item.similarity.problem_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Feature (30%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.feature_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-indigo-500 rounded-full"
                                        style={{ width: `${item.similarity.feature_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Tech Stack (25%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.tech_stack_overlap}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-purple-500 rounded-full"
                                        style={{ width: `${item.similarity.tech_stack_overlap}%` }}
                                      />
                                    </div>
                                  </div>

                                  <div className="space-y-1">
                                    <div className="flex justify-between text-[11px]">
                                      <span className="text-gray-400">Domain (15%)</span>
                                      <span className="font-mono text-gray-300">{item.similarity.domain_similarity}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-[#1F293D] rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-cyan-500 rounded-full"
                                        style={{ width: `${item.similarity.domain_similarity}%` }}
                                      />
                                    </div>
                                  </div>
                                </div>

                                {item.similarity.similarity_explanation && (
                                  <p className="text-[11px] text-gray-400 italic leading-relaxed pt-1 border-t border-[#1F293D]/60">
                                    {item.similarity.similarity_explanation}
                                  </p>
                                )}
                              </div>
                            )}

                            {/* Problem Statement */}
                            {item.problem_statement && (
                              <div className="space-y-1 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Problem Addressed by Repository
                                </span>
                                <p className="text-gray-300 leading-relaxed bg-[#0B0F19]/50 p-2.5 rounded-lg border border-[#1F293D]">
                                  {item.problem_statement}
                                </p>
                              </div>
                            )}

                            {/* 7 Standard Technology Stack Categories */}
                            <div className="space-y-2 text-xs">
                              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                Detected Technical Stack (Evidence Traceable)
                              </span>

                              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                                {/* Languages */}
                                {item.detected_technologies?.programming_languages?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-purple-400">
                                      <Code2 className="w-3.5 h-3.5" />
                                      <span>Languages</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.programming_languages.map((l, lIdx) => (
                                        <span
                                          key={lIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20"
                                        >
                                          {l}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Backend */}
                                {item.detected_technologies?.backend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-blue-400">
                                      <Cpu className="w-3.5 h-3.5" />
                                      <span>Backend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.backend_frameworks.map((b, bIdx) => (
                                        <span
                                          key={bIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20"
                                        >
                                          {b}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Frontend */}
                                {item.detected_technologies?.frontend_frameworks?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400">
                                      <Layers className="w-3.5 h-3.5" />
                                      <span>Frontend Frameworks</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.frontend_frameworks.map((f, fIdx) => (
                                        <span
                                          key={fIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                                        >
                                          {f}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* AI / ML */}
                                {item.detected_technologies?.ai_ml_libraries?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-rose-400">
                                      <Sparkles className="w-3.5 h-3.5" />
                                      <span>AI / ML Libraries</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.ai_ml_libraries.map((ai, aiIdx) => (
                                        <span
                                          key={aiIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-rose-500/10 text-rose-300 border border-rose-500/20"
                                        >
                                          {ai}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Databases */}
                                {item.detected_technologies?.databases?.length > 0 && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-400">
                                      <Database className="w-3.5 h-3.5" />
                                      <span>Databases & Storage</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {item.detected_technologies.databases.map((db, dbIdx) => (
                                        <span
                                          key={dbIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20"
                                        >
                                          {db}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Cloud & DevOps */}
                                {(item.detected_technologies?.cloud_deployment?.length > 0 ||
                                  item.detected_technologies?.devops_tools?.length > 0) && (
                                  <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1.5">
                                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-cyan-400">
                                      <Cloud className="w-3.5 h-3.5" />
                                      <span>Cloud & DevOps</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {[
                                        ...(item.detected_technologies.cloud_deployment || []),
                                        ...(item.detected_technologies.devops_tools || []),
                                      ].map((tool, tIdx) => (
                                        <span
                                          key={tIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/20"
                                        >
                                          {tool}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Extracted Features List */}
                            {item.features && item.features.length > 0 && (
                              <div className="space-y-2 text-xs">
                                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                                  Extracted Repository Features ({item.features.length})
                                </span>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  {item.features.map((feat, fIdx) => (
                                    <div
                                      key={fIdx}
                                      className="p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] space-y-1"
                                    >
                                      <div className="flex items-center justify-between gap-1">
                                        <span className="font-semibold text-white text-xs truncate">
                                          {feat.feature_name}
                                        </span>
                                        <div className="flex items-center gap-1 shrink-0">
                                          {feat.is_documented ? (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                              Doc
                                            </span>
                                          ) : (
                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-gray-800 text-gray-400 border border-gray-700">
                                              Inferred
                                            </span>
                                          )}
                                          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-blue-500/10 text-blue-300">
                                            {Math.round(feat.confidence_score * 100)}%
                                          </span>
                                        </div>
                                      </div>
                                      <p className="text-[11px] text-gray-400 leading-snug">
                                        {feat.description}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Architecture Topology Accordion */}
                            {item.architecture && (
                              <div className="pt-2 border-t border-[#1F293D]/60 space-y-2">
                                <button
                                  onClick={() => toggleArchitectureExpand(item.id || String(idx))}
                                  className="flex items-center justify-between w-full text-xs text-gray-400 hover:text-white transition-colors"
                                >
                                  <div className="flex items-center gap-1.5">
                                    <Layers className="w-3.5 h-3.5 text-blue-400" />
                                    <span className="font-medium">System Architecture Topology</span>
                                  </div>
                                  {isArchExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                </button>

                                {isArchExpanded && (
                                  <div className="p-3 rounded-lg bg-[#0B0F19] border border-[#1F293D] grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                                    {item.architecture.frontend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Frontend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.frontend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.backend_architecture && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Backend</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.backend_architecture}</p>
                                      </div>
                                    )}
                                    {item.architecture.database_layer && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Database</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.database_layer}</p>
                                      </div>
                                    )}
                                    {item.architecture.ai_ml_pipeline && (
                                      <div className="space-y-0.5">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">AI/ML Pipeline</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.ai_ml_pipeline}</p>
                                      </div>
                                    )}
                                    {item.architecture.deployment_infrastructure && (
                                      <div className="space-y-0.5 sm:col-span-2">
                                        <span className="text-[10px] font-semibold text-gray-500 uppercase">Deployment</span>
                                        <p className="text-gray-300 text-[11px]">{item.architecture.deployment_infrastructure}</p>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Pagination Controls for Repository Analyses */}
                {repoAnalysesTotal > 10 && (
                  <div className="flex items-center justify-between pt-3 border-t border-[#1F293D] text-xs text-gray-400">
                    <span>
                      Showing {(repoAnalysesPage - 1) * 10 + 1} to{' '}
                      {Math.min(repoAnalysesPage * 10, repoAnalysesTotal)} of {repoAnalysesTotal} analyzed repositories
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage - 1)}
                        disabled={repoAnalysesPage <= 1}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="px-2 font-mono text-gray-300">
                        Page {repoAnalysesPage} of {Math.max(1, Math.ceil(repoAnalysesTotal / 10))}
                      </span>
                      <button
                        onClick={() => loadRepoAnalyses(repoAnalysesPage + 1)}
                        disabled={repoAnalysesPage * 10 >= repoAnalysesTotal}
                        className="px-3 py-1 rounded-lg bg-[#151D30] border border-[#1F293D] text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* SECTION 15: SEMANTIC SIMILARITY & CROSS-SOURCE MATCHING (PHASE 4.4) */}
          <div className="p-6 rounded-2xl bg-[#0E1424] border border-[#1F293D] shadow-xl space-y-6">
            {/* Section Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-[#1F293D]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Binary className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      15. Semantic Similarity & Cross-Source Matching
                      <span className="px-2 py-0.5 text-xs font-mono font-medium rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        Phase 4.4
                      </span>
                    </h2>
                    <p className="text-xs text-gray-400">
                      Evidence-based dense vector retrieval comparing your project idea against academic research papers and GitHub repositories.
                    </p>
                  </div>
                </div>
              </div>

              {/* Header Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleGenerateEmbeddings(false)}
                  disabled={embeddingGenerating}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white shadow-lg shadow-indigo-500/20 flex items-center gap-2 transition-all disabled:opacity-50"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${embeddingGenerating ? 'animate-spin' : ''}`} />
                  <span>{embeddingGenerating ? 'Generating Embeddings...' : 'Generate Embeddings'}</span>
                </button>

                <button
                  onClick={() => handleGenerateEmbeddings(true)}
                  disabled={embeddingGenerating}
                  title="Force re-generation of all vectors even if content hash is unchanged"
                  className="p-2 rounded-xl text-xs bg-[#151D30] border border-[#1F293D] text-gray-400 hover:text-white hover:border-gray-600 transition-all disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${embeddingGenerating ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>

            {/* Model Configuration & Disclaimer Banner */}
            <div className="p-4 rounded-xl bg-[#090D16] border border-[#1F293D] flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <Fingerprint className="w-4 h-4 text-indigo-400 shrink-0" />
                <div>
                  <span className="text-gray-300 font-medium">Model Architecture: </span>
                  <span className="font-mono text-indigo-300">sentence-transformers/all-MiniLM-L6-v2</span>
                  <span className="text-gray-500 mx-2">|</span>
                  <span className="text-gray-300 font-medium">Vector Space: </span>
                  <span className="font-mono text-emerald-300">384 Dimensions (L2-Normalized)</span>
                </div>
              </div>

              <div className="flex items-center gap-1.5 text-[11px] text-gray-400 italic">
                <AlertCircle className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span>Cosine similarity reflects thematic vector proximity, distinct from Phase 4.3 rule-based overlap.</span>
              </div>
            </div>

            {/* Metric Cards Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-xl bg-[#0B0F19] border border-[#1F293D] space-y-1">
                <span className="text-[11px] text-gray-400 font-medium flex items-center gap-1.5">
                  <HardDrive className="w-3.5 h-3.5 text-blue-400" />
                  Vectors Stored
                </span>
                <p className="text-xl font-bold text-white font-mono">
                  {similarityStats?.total_embeddings_stored || 0}
                </p>
                <div className="text-[10px] text-gray-500 font-mono flex items-center gap-2">
                  <span>Proj: {similarityStats?.embeddings_by_source_type?.project || 0}</span>
                  <span>Paper: {similarityStats?.embeddings_by_source_type?.research_paper || 0}</span>
                  <span>Repo: {similarityStats?.embeddings_by_source_type?.github_repository || 0}</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#0B0F19] border border-[#1F293D] space-y-1">
                <span className="text-[11px] text-gray-400 font-medium flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-indigo-400" />
                  Total Matches
                </span>
                <p className="text-xl font-bold text-indigo-300 font-mono">
                  {similarityTotal}
                </p>
                <span className="text-[10px] text-gray-500">Cross-source candidates</span>
              </div>

              <div className="p-3.5 rounded-xl bg-[#0B0F19] border border-[#1F293D] space-y-1">
                <span className="text-[11px] text-gray-400 font-medium flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                  Top Similarity
                </span>
                <p className="text-xl font-bold text-emerald-400 font-mono">
                  {similarityMatches.length > 0 ? `${similarityMatches[0].similarity_percentage}%` : 'N/A'}
                </p>
                <span className="text-[10px] text-gray-500 truncate block">
                  {similarityMatches.length > 0 ? similarityMatches[0].title : 'No matches computed'}
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-[#0B0F19] border border-[#1F293D] space-y-1">
                <span className="text-[11px] text-gray-400 font-medium flex items-center gap-1.5">
                  <Gauge className="w-3.5 h-3.5 text-purple-400" />
                  Idea Vector Status
                </span>
                <p className="text-sm font-semibold mt-1">
                  {similarityStats?.has_project_embedding ? (
                    <span className="inline-flex items-center gap-1 text-emerald-400">
                      <CheckCircle2 className="w-4 h-4" /> Ready (Indexed)
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-amber-400">
                      <AlertTriangle className="w-4 h-4" /> Needs Generation
                    </span>
                  )}
                </p>
                <span className="text-[10px] text-gray-500">Project anchor vector</span>
              </div>
            </div>

            {/* Filter & Threshold Controls Bar */}
            <div className="p-4 rounded-xl bg-[#0B0F19] border border-[#1F293D] flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-3">
                {/* Source Type Filter */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <Filter className="w-3.5 h-3.5 text-gray-500" />
                    Source:
                  </span>
                  <div className="flex rounded-lg bg-[#151D30] border border-[#1F293D] p-0.5 text-xs">
                    {[
                      { id: 'all', label: 'All Sources' },
                      { id: 'research_paper', label: 'Research Papers' },
                      { id: 'github_repository', label: 'GitHub Repos' },
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => {
                          setSimilaritySourceFilter(tab.id);
                          loadSimilarityData(tab.id, similarityMinThreshold);
                        }}
                        className={`px-3 py-1 rounded-md transition-all ${
                          similaritySourceFilter === tab.id
                            ? 'bg-indigo-600 text-white font-medium shadow-sm'
                            : 'text-gray-400 hover:text-white'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Minimum Similarity Threshold Pills */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <Sliders className="w-3.5 h-3.5 text-gray-500" />
                    Min Similarity:
                  </span>
                  <div className="flex rounded-lg bg-[#151D30] border border-[#1F293D] p-0.5 text-xs">
                    {[
                      { value: 0, label: 'All (0%)' },
                      { value: 50, label: 'Moderate+ (50%)' },
                      { value: 70, label: 'High+ (70%)' },
                    ].map((pill) => (
                      <button
                        key={pill.value}
                        onClick={() => {
                          setSimilarityMinThreshold(pill.value);
                          loadSimilarityData(similaritySourceFilter, pill.value);
                        }}
                        className={`px-2.5 py-1 rounded-md transition-all font-mono text-[11px] ${
                          similarityMinThreshold === pill.value
                            ? 'bg-indigo-600 text-white font-medium shadow-sm'
                            : 'text-gray-400 hover:text-white'
                        }`}
                      >
                        {pill.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <button
                onClick={() => loadSimilarityData(similaritySourceFilter, similarityMinThreshold)}
                disabled={similarityLoading}
                className="px-3 py-1.5 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-gray-300 hover:text-white flex items-center gap-1.5 transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-3 h-3 ${similarityLoading ? 'animate-spin' : ''}`} />
                <span>Refresh Results</span>
              </button>
            </div>

            {/* Error Display */}
            {similarityError && (
              <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                <span>{similarityError}</span>
              </div>
            )}

            {/* Matches List or Empty State */}
            {similarityLoading ? (
              <div className="py-12 flex flex-col items-center justify-center space-y-3">
                <RefreshCw className="w-7 h-7 text-indigo-400 animate-spin" />
                <span className="text-xs text-gray-400">Computing dense vector cosine similarities...</span>
              </div>
            ) : similarityMatches.length === 0 ? (
              <div className="py-10 px-4 rounded-xl bg-[#0B0F19] border border-[#1F293D] text-center space-y-3">
                <Binary className="w-8 h-8 text-gray-600 mx-auto" />
                <h3 className="text-sm font-semibold text-gray-300">No Semantic Matches Found</h3>
                <p className="text-xs text-gray-500 max-w-md mx-auto">
                  {similarityStats?.has_project_embedding
                    ? 'No candidates meet the selected filter criteria. Try lowering the minimum similarity threshold.'
                    : 'Vector embeddings have not been generated yet for this project. Click "Generate Embeddings" above to run dense semantic analysis.'}
                </p>
                {!similarityStats?.has_project_embedding && (
                  <button
                    onClick={() => handleGenerateEmbeddings(false)}
                    disabled={embeddingGenerating}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all inline-flex items-center gap-2"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Generate Embeddings Now</span>
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {similarityMatches.map((match) => {
                  const isPaper = match.source_type === 'research_paper';
                  const isHigh = match.similarity_score >= 0.7;
                  const isModerate = match.similarity_score >= 0.5 && match.similarity_score < 0.7;

                  const badgeColor = isHigh
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : isModerate
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    : 'bg-slate-500/10 text-slate-400 border-slate-500/30';

                  const barColor = isHigh
                    ? 'bg-emerald-500'
                    : isModerate
                    ? 'bg-amber-500'
                    : 'bg-slate-500';

                  return (
                    <div
                      key={`${match.source_type}-${match.source_record_id}`}
                      className="p-4 rounded-xl bg-[#0B0F19] border border-[#1F293D] hover:border-indigo-500/40 transition-all space-y-3"
                    >
                      {/* Top Row: Rank, Source Type, Score, Percentage */}
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded-md font-mono text-[11px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                            #{match.rank}
                          </span>

                          <span
                            className={`px-2 py-0.5 rounded-md font-medium text-[11px] flex items-center gap-1.5 ${
                              isPaper
                                ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20'
                                : 'bg-purple-500/10 text-purple-300 border border-purple-500/20'
                            }`}
                          >
                            {isPaper ? <BookOpen className="w-3 h-3" /> : <Github className="w-3 h-3" />}
                            {isPaper ? 'Research Paper' : 'GitHub Repository'}
                          </span>

                          <span className={`px-2 py-0.5 rounded-md font-medium text-[11px] border ${badgeColor}`}>
                            {match.similarity_label}
                          </span>
                        </div>

                        {/* Numerical Metrics */}
                        <div className="flex items-center gap-3 font-mono text-xs">
                          <div className="flex items-center gap-1.5">
                            <span className="text-gray-500 text-[10px] uppercase">Cosine:</span>
                            <span className="text-gray-300 font-semibold">{match.similarity_score.toFixed(4)}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-gray-500 text-[10px] uppercase">Match:</span>
                            <span className={`font-bold text-sm ${isHigh ? 'text-emerald-400' : isModerate ? 'text-amber-400' : 'text-slate-400'}`}>
                              {match.similarity_percentage}%
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Similarity Progress Bar */}
                      <div className="w-full bg-[#151D30] rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                          style={{ width: `${Math.min(100, Math.max(2, match.similarity_percentage))}%` }}
                        />
                      </div>

                      {/* Title & External Link */}
                      <div>
                        {match.url ? (
                          <a
                            href={match.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-semibold text-white hover:text-indigo-400 inline-flex items-center gap-1.5 transition-colors group"
                          >
                            <span>{match.title}</span>
                            <ExternalLink className="w-3.5 h-3.5 text-gray-500 group-hover:text-indigo-400 shrink-0" />
                          </a>
                        ) : (
                          <h4 className="text-sm font-semibold text-white">{match.title}</h4>
                        )}
                      </div>

                      {/* Content Summary / Preview */}
                      <p className="text-xs text-gray-400 leading-relaxed">
                        {match.matching_content_summary}
                      </p>

                      {/* Conceptual Overlapping Aspects */}
                      {match.matched_aspects && match.matched_aspects.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          <span className="text-[10px] uppercase font-semibold text-gray-500 mr-1">
                            Overlapping Concepts:
                          </span>
                          {match.matched_aspects.map((aspect, aIdx) => (
                            <span
                              key={aIdx}
                              className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                            >
                              {aspect}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Source Specific Metadata Tags */}
                      <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[#1F293D]/60 text-[11px] text-gray-400">
                        {isPaper ? (
                          <>
                            {match.metadata.venue && <span>Venue: <strong className="text-gray-300">{match.metadata.venue}</strong></span>}
                            {match.metadata.year && <span>Year: <strong className="text-gray-300">{match.metadata.year}</strong></span>}
                            {match.metadata.open_access && (
                              <span className="text-emerald-400 font-medium flex items-center gap-1">
                                <Unlock className="w-2.5 h-2.5" /> Open Access
                              </span>
                            )}
                          </>
                        ) : (
                          <>
                            {match.metadata.language && <span>Language: <strong className="text-gray-300">{match.metadata.language}</strong></span>}
                            {match.metadata.stargazers_count !== undefined && match.metadata.stargazers_count !== null && (
                              <span className="flex items-center gap-1">
                                <Star className="w-2.5 h-2.5 text-amber-400" />
                                <strong className="text-gray-300">{(match.metadata.stargazers_count ?? 0).toLocaleString()}</strong> stars
                              </span>
                            )}
                            {match.metadata.has_deep_analysis && (
                              <span className="text-indigo-400 font-medium">Deep Analyzed (Phase 4.3)</span>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Phase Clarification Note */}
            <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] text-[11px] text-gray-400 space-y-1">
              <div className="flex items-center gap-1.5 font-semibold text-gray-300">
                <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                <span>Understanding Similarity Metrics in AI ProjectDNA:</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pl-5 text-gray-400">
                <div>
                  <strong className="text-indigo-300">Phase 4.4 Vector Cosine Similarity:</strong> Evaluates deep semantic, conceptual proximity in a 384-dimensional latent embedding space, detecting related ideas even when differing vocabularies are used.
                </div>
                <div>
                  <strong className="text-blue-300">Phase 4.3 Multi-Factor Heuristic:</strong> Evaluates explicit structural overlap across technology stacks, problem statements, and declared features.
                </div>
              </div>
              {similarityDisclaimer && (
                <div className="pt-2 border-t border-[#1F293D]/60 text-[10px] text-gray-500 italic">
                  {similarityDisclaimer}
                </div>
              )}
            </div>
          </div>

          {/* SECTION 16: EVIDENCE-BASED RESEARCH GAP VALIDATION (PHASE 4.5) */}
          <div className="p-6 rounded-2xl bg-[#0E1424] border border-[#1F293D] shadow-xl space-y-6">
            {/* Section Header */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-[#1F293D]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold font-mono tracking-wider bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-purple-300 border border-purple-500/30">
                    PHASE 4.5
                  </span>
                  <div className="flex items-center gap-1.5 text-xs text-gray-400">
                    <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                    <span>RAG Research Gap Validation Engine</span>
                  </div>
                </div>
                <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                  <span>Evidence-Backed Research Gap Dossier</span>
                  {validationReport && (
                    <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-purple-500/10 text-purple-300 border border-purple-500/30">
                      v{validationReport.version}
                    </span>
                  )}
                </h3>
                <p className="text-xs text-gray-400 max-w-2xl leading-relaxed">
                  Retrieval-Augmented Generation (RAG) synthesis comparing project goals against discovered academic literature, GitHub implementations, and multi-factor similarity metrics with strict citation traceability.
                </p>
              </div>

              {/* Action Toolbar */}
              <div className="flex flex-wrap items-center gap-2.5">
                {/* Version Selector */}
                {validationHistory && validationHistory.reports && validationHistory.reports.length > 1 && (
                  <select
                    value={selectedValidationVersion || ''}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      setSelectedValidationVersion(v);
                      loadValidationData(v);
                    }}
                    className="px-2.5 py-1.5 rounded-lg text-xs font-mono bg-[#151D30] border border-[#1F293D] text-gray-300 hover:border-purple-500/40 focus:outline-none transition-colors"
                  >
                    {validationHistory.reports.map((r) => (
                      <option key={r.id} value={r.version}>
                        v{r.version} ({new Date(r.created_at).toLocaleDateString()}) - {r.overall_evidence_coverage}
                      </option>
                    ))}
                  </select>
                )}

                {/* Evidence Manifest Explorer Button */}
                {validationReport && validationReport.evidence_manifest && (
                  <button
                    type="button"
                    onClick={() => setEvidenceModalOpen(true)}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#151D30] hover:bg-[#1E293B] border border-[#1F293D] text-gray-300 hover:text-white flex items-center gap-1.5 transition-colors"
                  >
                    <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                    <span>Evidence Manifest</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-blue-500/20 text-blue-300">
                      {validationReport.evidence_manifest.length}
                    </span>
                  </button>
                )}

                {/* Copy Summary Button */}
                {validationReport && (
                  <button
                    type="button"
                    onClick={handleCopyValidationReport}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#151D30] hover:bg-[#1E293B] border border-[#1F293D] text-gray-300 hover:text-white flex items-center gap-1.5 transition-colors"
                  >
                    {copiedValidationReport ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-300">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5 text-gray-400" />
                        <span>Copy Report</span>
                      </>
                    )}
                  </button>
                )}

                {/* Generate / Re-generate Button */}
                <button
                  type="button"
                  onClick={() => handleGenerateValidationReport(Boolean(validationReport))}
                  disabled={validationGenerating || validationLoading}
                  className="px-4 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white flex items-center gap-2 shadow-lg shadow-purple-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${validationGenerating ? 'animate-spin' : ''}`} />
                  <span>
                    {validationGenerating
                      ? 'Synthesizing RAG Dossier...'
                      : validationReport
                      ? `Re-run Validation (v${validationReport.version + 1})`
                      : 'Generate Validation Dossier'}
                  </span>
                </button>
              </div>
            </div>

            {/* Error Banner */}
            {validationError && (
              <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-red-400" />
                <div>
                  <span className="font-semibold">Validation Error: </span>
                  <span>{validationError}</span>
                </div>
              </div>
            )}

            {/* Loading State */}
            {validationLoading || validationGenerating ? (
              <div className="p-12 rounded-xl bg-[#090D16] border border-[#1F293D] text-center space-y-4">
                <div className="relative w-12 h-12 mx-auto">
                  <div className="absolute inset-0 rounded-full border-2 border-purple-500/20 border-t-purple-500 animate-spin" />
                  <ShieldCheck className="w-6 h-6 text-purple-400 absolute inset-0 m-auto animate-pulse" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-white">Synthesizing Evidence-Backed Validation Dossier</h4>
                  <p className="text-xs text-gray-400 max-w-md mx-auto">
                    Retrieving academic research papers, GitHub repositories, and multi-factor similarity metrics to ground innovation gaps...
                  </p>
                </div>
              </div>
            ) : !validationReport ? (
              /* Empty State */
              <div className="p-10 rounded-xl bg-[#090D16] border border-dashed border-[#1F293D] text-center space-y-3">
                <Scale className="w-10 h-10 text-gray-600 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-gray-300">No Validation Dossier Generated Yet</h4>
                  <p className="text-xs text-gray-500 max-w-md mx-auto">
                    Click "Generate Validation Dossier" to initiate the RAG validation engine. The engine cross-references your project against academic literature and software implementations to identify verified gaps.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleGenerateValidationReport(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white inline-flex items-center gap-2 transition-colors"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Initiate RAG Validation</span>
                </button>
              </div>
            ) : (
              /* Active Validation Report View */
              <div className="space-y-6">
                {/* KPI Overview Bar */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1">
                    <span className="text-[11px] text-gray-400 font-medium">Evidence Coverage</span>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`text-sm font-bold uppercase tracking-wider font-mono ${
                          validationReport.report.final_assessment.overall_evidence_coverage === 'comprehensive'
                            ? 'text-emerald-400'
                            : validationReport.report.final_assessment.overall_evidence_coverage === 'adequate'
                            ? 'text-blue-400'
                            : 'text-amber-400'
                        }`}
                      >
                        {validationReport.report.final_assessment.overall_evidence_coverage}
                      </span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1">
                    <span className="text-[11px] text-gray-400 font-medium">Supported Gaps</span>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-lg font-bold text-white font-mono">
                        {
                          validationReport.report.validated_research_gaps.validated_gaps.filter(
                            (g) => g.validation_status === 'supported_gap'
                          ).length
                        }
                      </span>
                      <span className="text-xs text-gray-500 font-mono">
                        / {validationReport.report.validated_research_gaps.validated_gaps.length} evaluated
                      </span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1">
                    <span className="text-[11px] text-gray-400 font-medium">Retrieved Evidence</span>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-lg font-bold text-blue-400 font-mono">
                        {validationReport.evidence_manifest.length}
                      </span>
                      <span className="text-xs text-gray-500 font-mono">
                        sources
                      </span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1">
                    <span className="text-[11px] text-gray-400 font-medium">Synthesis Model</span>
                    <div className="text-xs font-mono text-purple-300 truncate" title={validationReport.model_name}>
                      {validationReport.model_name}
                    </div>
                  </div>
                </div>

                {/* Sub-Section Navigation Tabs */}
                <div className="flex flex-wrap gap-1.5 p-1 rounded-xl bg-[#090D16] border border-[#1F293D]">
                  {[
                    { id: 'gaps', label: 'Validated Gaps', count: validationReport.report.validated_research_gaps.validated_gaps.length },
                    { id: 'academic', label: 'Academic Literature', count: validationReport.report.academic_research.relevant_papers.length },
                    { id: 'implementations', label: 'Software Implementations', count: validationReport.report.software_implementations.relevant_repositories.length },
                    { id: 'capabilities', label: 'Capability Matrix' },
                    { id: 'opportunities', label: 'Opportunities' },
                    { id: 'recommendations', label: 'Technical Blueprint' },
                    { id: 'risks', label: 'Risks & Limitations' },
                    { id: 'final', label: 'Assessment & Caveats' },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setActiveReportTab(tab.id)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
                        activeReportTab === tab.id
                          ? 'bg-purple-600 text-white shadow-sm'
                          : 'text-gray-400 hover:text-white hover:bg-[#151D30]'
                      }`}
                    >
                      <span>{tab.label}</span>
                      {tab.count !== undefined && (
                        <span
                          className={`px-1.5 py-0.2 rounded text-[10px] font-mono ${
                            activeReportTab === tab.id ? 'bg-purple-800 text-purple-100' : 'bg-[#1F293D] text-gray-400'
                          }`}
                        >
                          {tab.count}
                        </span>
                      )}
                    </button>
                  ))}
                </div>

                {/* TAB 1: VALIDATED RESEARCH GAPS */}
                {activeReportTab === 'gaps' && (
                  <div className="space-y-4">
                    {/* Summary banner */}
                    <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs text-purple-200">
                      <span className="font-semibold">Gap Validation Overview: </span>
                      <span>{validationReport.report.validated_research_gaps.gap_validation_summary}</span>
                    </div>

                    {/* Filter chips */}
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <span className="text-gray-500 text-[11px] font-medium mr-1">Status Filter:</span>
                      {['all', 'supported_gap', 'partially_supported_gap', 'not_supported_gap', 'insufficient_evidence'].map((status) => (
                        <button
                          key={status}
                          type="button"
                          onClick={() => setGapFilterStatus(status)}
                          className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition-colors ${
                            gapFilterStatus === status
                              ? 'bg-purple-600 text-white font-semibold'
                              : 'bg-[#151D30] text-gray-400 hover:text-white border border-[#1F293D]'
                          }`}
                        >
                          {status === 'all'
                            ? 'All Gaps'
                            : status.replace(/_/g, ' ')}
                        </button>
                      ))}
                    </div>

                    {/* Gap Cards Grid */}
                    <div className="grid grid-cols-1 gap-4">
                      {validationReport.report.validated_research_gaps.validated_gaps
                        .filter((g) => gapFilterStatus === 'all' || g.validation_status === gapFilterStatus)
                        .map((gap, gIdx) => {
                          const statusColor =
                            gap.validation_status === 'supported_gap'
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                              : gap.validation_status === 'partially_supported_gap'
                              ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                              : gap.validation_status === 'not_supported_gap'
                              ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                              : 'bg-slate-500/10 text-slate-300 border-slate-500/30';

                          return (
                            <div
                              key={gIdx}
                              className="p-4 rounded-xl bg-[#090D16] border border-[#1F293D] hover:border-purple-500/40 space-y-3 transition-colors"
                            >
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase tracking-wider border ${statusColor}`}>
                                    {gap.validation_status.replace(/_/g, ' ')}
                                  </span>
                                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#151D30] text-gray-400 border border-[#1F293D]">
                                    Category: {gap.category}
                                  </span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
                                    Priority: {gap.priority.toUpperCase()}
                                  </span>
                                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                                    Confidence: {gap.confidence_level}
                                  </span>
                                </div>
                              </div>

                              <h4 className="text-sm font-semibold text-white tracking-tight">
                                {gap.gap_title}
                              </h4>

                              <p className="text-xs text-gray-400 leading-relaxed">
                                {gap.description}
                              </p>

                              {/* Evidence-backed reasoning */}
                              <div className="p-3 rounded-lg bg-[#151D30]/60 border border-[#1F293D] space-y-1.5 text-xs">
                                <div className="flex items-center gap-1.5 font-semibold text-gray-300">
                                  <FileCheck2 className="w-3.5 h-3.5 text-purple-400" />
                                  <span>Grounded Evidence & Reasoning:</span>
                                </div>
                                <p className="text-gray-300 text-xs leading-relaxed">{gap.reasoning}</p>

                                {/* Citations */}
                                <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[#1F293D]/60 text-[11px]">
                                  {gap.supporting_evidence_ids && gap.supporting_evidence_ids.length > 0 && (
                                    <div className="flex flex-wrap items-center gap-1">
                                      <span className="text-emerald-400 font-medium">Supports:</span>
                                      {gap.supporting_evidence_ids.map((id) => (
                                        <button
                                          key={id}
                                          type="button"
                                          onClick={() => setEvidenceModalOpen(true)}
                                          className="px-1.5 py-0.2 rounded font-mono text-[10px] bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 border border-emerald-500/30 transition-colors"
                                        >
                                          {id}
                                        </button>
                                      ))}
                                    </div>
                                  )}

                                  {gap.contradicting_evidence_ids && gap.contradicting_evidence_ids.length > 0 && (
                                    <div className="flex flex-wrap items-center gap-1">
                                      <span className="text-rose-400 font-medium">Addressed By:</span>
                                      {gap.contradicting_evidence_ids.map((id) => (
                                        <button
                                          key={id}
                                          type="button"
                                          onClick={() => setEvidenceModalOpen(true)}
                                          className="px-1.5 py-0.2 rounded font-mono text-[10px] bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 border border-rose-500/30 transition-colors"
                                        >
                                          {id}
                                        </button>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* Suggested direction */}
                              <div className="p-2.5 rounded-lg bg-blue-500/5 border border-blue-500/20 text-xs flex items-start gap-2 text-blue-200">
                                <Compass className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
                                <div>
                                  <strong className="text-blue-300">Suggested Innovation Path: </strong>
                                  <span>{gap.suggested_direction}</span>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}

                {/* TAB 2: ACADEMIC LITERATURE SYNTHESIS */}
                {activeReportTab === 'academic' && (
                  <div className="space-y-4">
                    <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-200">
                      <span className="font-semibold">Literature Landscape: </span>
                      <span>{validationReport.report.academic_research.research_synthesis_summary}</span>
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                      {validationReport.report.academic_research.relevant_papers.map((paper, pIdx) => (
                        <div key={pIdx} className="p-4 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-2">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="px-2 py-0.5 rounded font-mono text-xs bg-purple-500/10 text-purple-300 border border-purple-500/30">
                              {paper.evidence_id}
                            </span>
                            {paper.similarity_score !== undefined && paper.similarity_score !== null && (
                              <span className="text-[11px] font-mono text-blue-300 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                                Semantic Proximity: {(paper.similarity_score * 100).toFixed(1)}%
                              </span>
                            )}
                          </div>

                          <h4 className="text-sm font-semibold text-white">
                            {paper.url ? (
                              <a href={paper.url} target="_blank" rel="noopener noreferrer" className="hover:text-purple-300 inline-flex items-center gap-1.5 transition-colors">
                                <span>{paper.title}</span>
                                <ExternalLink className="w-3.5 h-3.5 text-gray-500" />
                              </a>
                            ) : (
                              paper.title
                            )}
                          </h4>

                          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400">
                            {paper.authors && paper.authors.length > 0 && <span>Authors: {paper.authors.join(', ')}</span>}
                            {paper.publication_year && <span>Year: {paper.publication_year}</span>}
                            {paper.venue && <span>Venue: {paper.venue}</span>}
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs pt-1">
                            <div className="p-2.5 rounded bg-[#151D30] border border-[#1F293D] space-y-1">
                              <span className="font-semibold text-gray-300">Core Findings:</span>
                              <p className="text-gray-400 text-[11px] leading-relaxed">{paper.main_findings}</p>
                            </div>
                            <div className="p-2.5 rounded bg-[#151D30] border border-[#1F293D] space-y-1">
                              <span className="font-semibold text-rose-300">Reported Limitations:</span>
                              <p className="text-gray-400 text-[11px] leading-relaxed">{paper.evidence_supported_limitations}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* TAB 3: SOFTWARE IMPLEMENTATIONS */}
                {activeReportTab === 'implementations' && (
                  <div className="space-y-4">
                    <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-200">
                      <span className="font-semibold">Software Ecosystem: </span>
                      <span>{validationReport.report.software_implementations.implementation_landscape_summary}</span>
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                      {validationReport.report.software_implementations.relevant_repositories.map((repo, rIdx) => (
                        <div key={rIdx} className="p-4 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-2">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded font-mono text-xs bg-blue-500/10 text-blue-300 border border-blue-500/30">
                                {repo.evidence_id}
                              </span>
                              <a
                                href={repo.url || `https://github.com/${repo.repo_full_name}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-semibold text-white hover:text-blue-300 inline-flex items-center gap-1.5 transition-colors"
                              >
                                <span>{repo.repo_full_name}</span>
                                <ExternalLink className="w-3.5 h-3.5 text-gray-500" />
                              </a>
                            </div>
                            {repo.stars_count > 0 && (
                              <span className="flex items-center gap-1 text-xs text-amber-300 font-mono">
                                <Star className="w-3 h-3 text-amber-400" />
                                {repo.stars_count.toLocaleString()}
                              </span>
                            )}
                          </div>

                          {/* Tech stack */}
                          {repo.detected_technologies && repo.detected_technologies.length > 0 && (
                            <div className="flex flex-wrap items-center gap-1 text-[11px]">
                              <span className="text-gray-500">Tech Stack:</span>
                              {repo.detected_technologies.map((t, idx) => (
                                <span key={idx} className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#151D30] text-gray-300 border border-[#1F293D]">
                                  {t}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* Features and limitations */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs pt-1">
                            <div className="p-2.5 rounded bg-[#151D30] border border-[#1F293D] space-y-1">
                              <span className="font-semibold text-gray-300">Documented Features:</span>
                              <ul className="list-disc list-inside text-gray-400 text-[11px] space-y-0.5 pl-1">
                                {repo.documented_features.map((f, fIdx) => (
                                  <li key={fIdx}>{f}</li>
                                ))}
                              </ul>
                            </div>
                            <div className="p-2.5 rounded bg-[#151D30] border border-[#1F293D] space-y-1">
                              <span className="font-semibold text-amber-300">Architectural Gaps:</span>
                              <p className="text-gray-400 text-[11px] leading-relaxed">
                                {repo.implementation_limitations || 'None documented explicitly in README.'}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* TAB 4: CAPABILITY MATRIX */}
                {activeReportTab === 'capabilities' && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Addressed */}
                    <div className="p-4 rounded-xl bg-[#090D16] border border-emerald-500/20 space-y-3">
                      <div className="flex items-center gap-2 pb-2 border-b border-[#1F293D]">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <h4 className="text-xs font-semibold text-white uppercase tracking-wider">Already Addressed</h4>
                      </div>
                      <div className="space-y-2">
                        {validationReport.report.capability_analysis.already_addressed_capabilities.map((c, idx) => (
                          <div key={idx} className="p-2.5 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 text-xs">
                            <div className="font-medium text-emerald-300">{c.capability_name}</div>
                            <p className="text-gray-400 text-[11px]">{c.description}</p>
                            {c.supporting_evidence_ids && (
                              <div className="flex flex-wrap gap-1 pt-1 font-mono text-[10px] text-gray-400">
                                {c.supporting_evidence_ids.map((id) => (
                                  <span key={id} className="px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                    {id}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Partially Addressed */}
                    <div className="p-4 rounded-xl bg-[#090D16] border border-amber-500/20 space-y-3">
                      <div className="flex items-center gap-2 pb-2 border-b border-[#1F293D]">
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                        <h4 className="text-xs font-semibold text-white uppercase tracking-wider">Partially Addressed</h4>
                      </div>
                      <div className="space-y-2">
                        {validationReport.report.capability_analysis.partially_addressed_capabilities.map((c, idx) => (
                          <div key={idx} className="p-2.5 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 text-xs">
                            <div className="font-medium text-amber-300">{c.capability_name}</div>
                            <p className="text-gray-400 text-[11px]">{c.description}</p>
                            {c.supporting_evidence_ids && (
                              <div className="flex flex-wrap gap-1 pt-1 font-mono text-[10px] text-gray-400">
                                {c.supporting_evidence_ids.map((id) => (
                                  <span key={id} className="px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                                    {id}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Insufficient Evidence */}
                    <div className="p-4 rounded-xl bg-[#090D16] border border-slate-500/20 space-y-3">
                      <div className="flex items-center gap-2 pb-2 border-b border-[#1F293D]">
                        <HelpCircle className="w-4 h-4 text-slate-400" />
                        <h4 className="text-xs font-semibold text-white uppercase tracking-wider">Insufficient Evidence</h4>
                      </div>
                      <div className="space-y-2">
                        {validationReport.report.capability_analysis.capabilities_with_insufficient_evidence.map((c, idx) => (
                          <div key={idx} className="p-2.5 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 text-xs">
                            <div className="font-medium text-slate-300">{c.capability_name}</div>
                            <p className="text-gray-400 text-[11px]">{c.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 5: INNOVATION OPPORTUNITIES */}
                {activeReportTab === 'opportunities' && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-3">
                      <h4 className="text-xs font-semibold text-purple-300 uppercase tracking-wider">Differentiating Capabilities</h4>
                      <div className="space-y-2">
                        {validationReport.report.innovation_opportunities.differentiating_capabilities.map((item, idx) => (
                          <div key={idx} className="p-2.5 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 text-xs">
                            <span className="font-semibold text-white">{item.title}</span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">{item.description}</p>
                            <div className="pt-1 text-[11px] text-purple-300">
                              <strong>Expected Impact: </strong>{item.expected_impact}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-3">
                      <h4 className="text-xs font-semibold text-blue-300 uppercase tracking-wider">Technical Improvements</h4>
                      <div className="space-y-2">
                        {validationReport.report.innovation_opportunities.technical_improvements.map((item, idx) => (
                          <div key={idx} className="p-2.5 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 text-xs">
                            <span className="font-semibold text-white">{item.title}</span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">{item.description}</p>
                            <div className="pt-1 text-[11px] text-blue-300">
                              <strong>Expected Impact: </strong>{item.expected_impact}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-3">
                      <h4 className="text-xs font-semibold text-emerald-300 uppercase tracking-wider">Research Directions</h4>
                      <div className="space-y-2">
                        {validationReport.report.innovation_opportunities.research_directions.map((item, idx) => (
                          <div key={idx} className="p-2.5 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1 text-xs">
                            <span className="font-semibold text-white">{item.title}</span>
                            <p className="text-gray-400 text-[11px] leading-relaxed">{item.description}</p>
                            <div className="pt-1 text-[11px] text-emerald-300">
                              <strong>Expected Impact: </strong>{item.expected_impact}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 6: TECHNICAL BLUEPRINT */}
                {activeReportTab === 'recommendations' && (
                  <div className="p-5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-4 text-xs">
                    <div className="space-y-1">
                      <span className="font-semibold text-purple-300">Recommended Architecture:</span>
                      <p className="text-gray-300 leading-relaxed bg-[#151D30] p-3 rounded-lg border border-[#1F293D]">
                        {validationReport.report.technical_recommendations.recommended_architecture}
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-2">
                        <span className="font-semibold text-blue-300">Algorithms & Methods:</span>
                        <ul className="list-disc list-inside text-gray-400 text-[11px] space-y-1 pl-1">
                          {validationReport.report.technical_recommendations.potential_algorithms.map((alg, idx) => (
                            <li key={idx}>{alg}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-2">
                        <span className="font-semibold text-emerald-300">Implementation Considerations:</span>
                        <ul className="list-disc list-inside text-gray-400 text-[11px] space-y-1 pl-1">
                          {validationReport.report.technical_recommendations.implementation_considerations.map((c, idx) => (
                            <li key={idx}>{c}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 7: RISKS & LIMITATIONS */}
                {activeReportTab === 'risks' && (
                  <div className="p-5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-4 text-xs">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1.5">
                        <span className="font-semibold text-amber-300">Evidence Coverage Bounds:</span>
                        <p className="text-gray-400 text-[11px] leading-relaxed">
                          {validationReport.report.risks_and_limitations.evidence_coverage_limitations}
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-1.5">
                        <span className="font-semibold text-rose-300">False Positive/Negative Risks:</span>
                        <p className="text-gray-400 text-[11px] leading-relaxed">
                          {validationReport.report.risks_and_limitations.false_positive_negative_risks}
                        </p>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-[#151D30] border border-[#1F293D] space-y-2">
                      <span className="font-semibold text-gray-300">Explicit Unverified Assumptions:</span>
                      <ul className="list-disc list-inside text-gray-400 text-[11px] space-y-1 pl-1">
                        {validationReport.report.risks_and_limitations.unverified_assumptions.map((assump, idx) => (
                          <li key={idx}>{assump}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* TAB 8: FINAL ASSESSMENT & CAVEATS */}
                {activeReportTab === 'final' && (
                  <div className="space-y-4">
                    <div className="p-5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-3 text-xs">
                      <span className="font-semibold text-purple-300 text-sm">Synthesis Conclusion:</span>
                      <p className="text-gray-300 leading-relaxed">
                        {validationReport.report.final_assessment.existing_work_summary}
                      </p>

                      <div className="pt-2 border-t border-[#1F293D] space-y-2">
                        <span className="font-semibold text-white">Recommended Next Steps:</span>
                        <ul className="list-disc list-inside text-gray-400 text-[11px] space-y-1 pl-1">
                          {validationReport.report.final_assessment.recommended_next_steps.map((step, idx) => (
                            <li key={idx}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Novelty Disclaimer Box */}
                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-2.5">
                      <ShieldCheck className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                      <div className="space-y-1">
                        <h5 className="font-bold text-amber-300 uppercase tracking-wider text-[11px]">
                          Evidence Grounding & Novelty Guardrail
                        </h5>
                        <p className="text-amber-200/90 leading-relaxed text-[11px]">
                          {validationReport.report.final_assessment.explicit_novelty_limitation}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* SECTION 17: PATENT & PRIOR-ART DISCOVERY ENGINE (Phase 4.6) */}
          <div className="rounded-2xl bg-[#0E1424] border border-[#1F293D] p-6 shadow-xl space-y-6">
            {/* Header */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-[#1F293D]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                    PHASE 4.6 ENGINE
                  </span>
                  <span className="flex items-center gap-1.5 text-xs text-gray-400 font-mono">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    USPTO Open Data & EPO OPS Active
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <Scale className="w-5 h-5 text-indigo-400" />
                  <span>Patent & Prior-Art Discovery Engine</span>
                </h3>
                <p className="text-xs text-gray-400">
                  Automated patent retrieval, dense semantic vector comparison, and claims prior-art analysis across global patent registries.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={handleSearchPatents}
                  disabled={patentSearching}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center gap-2 transition-all cursor-pointer"
                >
                  <Search className={`w-3.5 h-3.5 ${patentSearching ? 'animate-spin' : ''}`} />
                  <span>{patentSearching ? 'Discovering Patents...' : 'Search Patents & Prior Art'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleAnalyzePriorArt()}
                  disabled={patentAnalyzing || patents.length === 0}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#151D30] hover:bg-[#1F293D] text-indigo-300 border border-indigo-500/30 disabled:opacity-50 flex items-center gap-2 transition-colors cursor-pointer"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${patentAnalyzing ? 'animate-spin' : ''}`} />
                  <span>{patentAnalyzing ? 'Analyzing Prior Art...' : 'Deep Prior-Art Analysis'}</span>
                </button>
              </div>
            </div>

            {/* Prominent Legal Guardrail & Disclaimer Banner */}
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-3">
              <Scale className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h5 className="font-bold text-amber-300 uppercase tracking-wider text-[11px] flex items-center gap-2">
                  <span>Legal Notice & Prior-Art Research Guardrail</span>
                </h5>
                <p className="text-amber-200/90 leading-relaxed text-[11px]">
                  Preliminary research assistance only. Does not constitute a legal patentability opinion or formal freedom-to-operate search. Patent scope is defined strictly by issued legal claims. Overlap indicates conceptual technology kinship rather than legal infringement.
                </p>
              </div>
            </div>

            {/* Error Banner */}
            {patentSearchError && (
              <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                <span>{patentSearchError}</span>
              </div>
            )}

            {/* KPI Overview Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1">
                <span className="text-[11px] text-gray-400 font-mono">Discovered Patents</span>
                <div className="text-xl font-bold text-white font-mono">
                  {patentStats?.total_patents || patents.length}
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1">
                <span className="text-[11px] text-emerald-400 font-mono">High Similarity (≥70%)</span>
                <div className="text-xl font-bold text-emerald-300 font-mono">
                  {patentStats?.high_similarity_count || patents.filter((p: Patent) => (p.similarity_score || 0) >= 0.7).length}
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1">
                <span className="text-[11px] text-amber-400 font-mono">Moderate (≥50%)</span>
                <div className="text-xl font-bold text-amber-300 font-mono">
                  {patentStats?.moderate_similarity_count || patents.filter((p: Patent) => (p.similarity_score || 0) >= 0.5 && (p.similarity_score || 0) < 0.7).length}
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1">
                <span className="text-[11px] text-indigo-400 font-mono">Top Jurisdictions</span>
                <div className="text-xs font-mono font-bold text-white flex gap-1.5 flex-wrap pt-1">
                  {patentStats?.by_jurisdiction && Object.keys(patentStats.by_jurisdiction).length > 0 ? (
                    Object.entries(patentStats.by_jurisdiction).map(([jur, cnt]) => (
                      <span key={jur} className="px-1.5 py-0.5 rounded bg-[#151D30] border border-[#1F293D] text-[10px]">
                        {jur}: {String(cnt)}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-500">US, EP</span>
                  )}
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1">
                <span className="text-[11px] text-purple-400 font-mono">Discovered CPCs</span>
                <div className="text-xs font-mono text-gray-300 truncate pt-1">
                  {patentStats?.top_classifications && Object.keys(patentStats.top_classifications).length > 0 ? (
                    Object.keys(patentStats.top_classifications).slice(0, 3).join(', ')
                  ) : (
                    'G06F, G06N'
                  )}
                </div>
              </div>
            </div>

            {/* Prior-Art Landscape Synthesis (if available) */}
            {patentAnalysis && (
              <div className="p-5 rounded-xl bg-[#090D16] border border-indigo-500/30 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    <span>Prior-Art Landscape Synthesis</span>
                  </h4>
                  <span className="text-[11px] font-mono text-indigo-300">
                    {patentAnalysis.total_analyzed} publications analyzed
                  </span>
                </div>
                <p className="text-xs text-gray-300 leading-relaxed">
                  {patentAnalysis.overall_prior_art_summary}
                </p>
                {patentAnalysis.technical_differentiation_opportunities.length > 0 && (
                  <div className="pt-2 border-t border-[#1F293D] space-y-2">
                    <span className="text-xs font-semibold text-emerald-400">Technical Differentiation Angles:</span>
                    <ul className="space-y-1">
                      {patentAnalysis.technical_differentiation_opportunities.map((opp: string, idx: number) => (
                        <li key={idx} className="text-xs text-gray-300 flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                          <span>{opp}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Toolbar: Search, Filters, Sort */}
            <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D]">
              {/* Search query input */}
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter by title, keywords or publication number..."
                  value={patentSearchQuery}
                  onChange={(e) => setPatentSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadPatents(1, patentJurisdiction, patentProvider, patentSortBy, patentSearchQuery)}
                  className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>

              {/* Jurisdiction Filter */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 hidden sm:inline">Jurisdiction:</span>
                <select
                  value={patentJurisdiction}
                  onChange={(e) => {
                    setPatentJurisdiction(e.target.value);
                    loadPatents(1, e.target.value, patentProvider, patentSortBy, patentSearchQuery);
                  }}
                  className="px-2.5 py-1.5 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-gray-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="all">All Jurisdictions</option>
                  <option value="US">United States (US)</option>
                  <option value="EP">European Union (EP)</option>
                  <option value="WO">WIPO / International (WO)</option>
                </select>

                {/* Provider Filter */}
                <select
                  value={patentProvider}
                  onChange={(e) => {
                    setPatentProvider(e.target.value);
                    loadPatents(1, patentJurisdiction, e.target.value, patentSortBy, patentSearchQuery);
                  }}
                  className="px-2.5 py-1.5 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-gray-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="all">All Providers</option>
                  <option value="uspto">USPTO</option>
                  <option value="epo">EPO</option>
                </select>

                {/* Sort Filter */}
                <select
                  value={patentSortBy}
                  onChange={(e) => {
                    const val = e.target.value as any;
                    setPatentSortBy(val);
                    loadPatents(1, patentJurisdiction, patentProvider, val, patentSearchQuery);
                  }}
                  className="px-2.5 py-1.5 rounded-lg bg-[#151D30] border border-[#1F293D] text-xs text-gray-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="similarity">Sort: Semantic Similarity</option>
                  <option value="publication_date">Sort: Publication Date</option>
                  <option value="created_at">Sort: Discovery Date</option>
                </select>
              </div>
            </div>

            {/* Patent Cards List */}
            {patentLoading ? (
              <div className="p-12 text-center space-y-3">
                <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin mx-auto" />
                <p className="text-xs text-gray-400 font-mono">Loading patents & prior-art disclosures...</p>
              </div>
            ) : patents.length === 0 ? (
              <div className="p-10 rounded-xl bg-[#090D16] border border-dashed border-[#1F293D] text-center space-y-3">
                <Scale className="w-8 h-8 text-gray-600 mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-white">No Patent Prior-Art Discovered Yet</h4>
                  <p className="text-xs text-gray-400 max-w-md mx-auto">
                    Click "Search Patents & Prior Art" to retrieve matching patents from USPTO Open Data and EPO OPS based on your project idea.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleSearchPatents}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors cursor-pointer"
                >
                  Search Patents Now
                </button>
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  {patents.map((pat: Patent) => {
                    const simScore = pat.similarity_score !== undefined && pat.similarity_score !== null ? pat.similarity_score : 0;
                    const isHigh = simScore >= 0.7;
                    const isModerate = simScore >= 0.5 && simScore < 0.7;
                    const bandLabel = pat.similarity_band || (isHigh ? 'High semantic similarity' : isModerate ? 'Moderate semantic similarity' : 'Low semantic similarity');
                    const isExpanded = !!expandedPatentAbstracts[pat.id];

                    return (
                      <div
                        key={pat.id}
                        className="p-5 rounded-xl bg-[#090D16] border border-[#1F293D] hover:border-indigo-500/40 transition-all space-y-3 group"
                      >
                        {/* Top Bar */}
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="px-2.5 py-0.5 rounded font-mono font-bold text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                              {pat.publication_number}
                            </span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-[#151D30] text-gray-300 border border-[#1F293D]">
                              {pat.jurisdiction || 'US'}
                            </span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono text-gray-400 bg-[#151D30] border border-[#1F293D]">
                              {pat.provider.toUpperCase()}
                            </span>
                            {pat.legal_status && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20">
                                {pat.legal_status}
                              </span>
                            )}
                          </div>

                          {/* Similarity Meter Badge */}
                          <div className="flex items-center gap-2">
                            <div className="text-right">
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                                  isHigh
                                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                    : isModerate
                                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                    : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                                }`}
                              >
                                {(simScore * 100).toFixed(1)}% • {bandLabel}
                              </span>
                            </div>
                            {pat.source_url && (
                              <a
                                href={pat.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-2 py-1 rounded-lg text-[11px] font-mono text-gray-400 hover:text-white bg-[#151D30] hover:bg-[#1F293D] border border-[#1F293D] flex items-center gap-1 transition-colors"
                                title="View official record on Google Patents"
                              >
                                <span>Google Patents</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                        </div>

                        {/* Title */}
                        <h4 className="text-base font-semibold text-white group-hover:text-indigo-300 transition-colors">
                          {pat.title}
                        </h4>

                        {/* Metadata Strip */}
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-gray-400">
                          {pat.assignees && pat.assignees.length > 0 && (
                            <div>
                              <span className="text-gray-500">Assignee: </span>
                              <span className="text-gray-300 font-medium">{pat.assignees.join(', ')}</span>
                            </div>
                          )}
                          {pat.inventors && pat.inventors.length > 0 && (
                            <div>
                              <span className="text-gray-500">Inventors: </span>
                              <span className="text-gray-300">{pat.inventors.slice(0, 2).join(', ')}{pat.inventors.length > 2 ? ' et al.' : ''}</span>
                            </div>
                          )}
                          {pat.publication_date && (
                            <div>
                              <span className="text-gray-500">Published: </span>
                              <span className="font-mono text-gray-300">{pat.publication_date}</span>
                            </div>
                          )}
                        </div>

                        {/* CPC Classifications */}
                        {pat.cpc_classifications && pat.cpc_classifications.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1.5 pt-1">
                            <span className="text-[10px] text-gray-500 font-mono">CPC Classes:</span>
                            {pat.cpc_classifications.slice(0, 5).map((cpc: string, cIdx: number) => (
                              <span
                                key={cIdx}
                                className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#151D30] text-indigo-300 border border-indigo-500/20"
                              >
                                {cpc}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Abstract snippet with Expand/Collapse */}
                        {pat.abstract && (
                          <div className="space-y-1.5 pt-1">
                            <p className={`text-xs text-gray-300 leading-relaxed font-sans ${isExpanded ? '' : 'line-clamp-2'}`}>
                              {pat.abstract}
                            </p>
                            {pat.abstract.length > 180 && (
                              <button
                                type="button"
                                onClick={() => togglePatentAbstract(pat.id)}
                                className="text-[11px] font-mono text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors cursor-pointer"
                              >
                                {isExpanded ? (
                                  <>
                                    <span>Collapse Abstract</span>
                                    <ChevronUp className="w-3 h-3" />
                                  </>
                                ) : (
                                  <>
                                    <span>Read Full Abstract</span>
                                    <ChevronDown className="w-3 h-3" />
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                        )}

                        {/* Card Action Footer */}
                        <div className="pt-2 border-t border-[#1F293D] flex items-center justify-between">
                          <span className="text-[10px] text-gray-500 font-mono">
                            Prior-Art Reference: {pat.publication_number}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleOpenSinglePriorArt(pat)}
                            className="px-3 py-1 rounded-lg text-xs font-semibold bg-[#151D30] hover:bg-indigo-600/30 text-indigo-300 hover:text-white border border-indigo-500/30 flex items-center gap-1.5 transition-colors cursor-pointer"
                          >
                            <FileText className="w-3.5 h-3.5" />
                            <span>Prior-Art Analysis</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Patent Pagination Controls */}
                {patentTotal > 10 && (
                  <div className="flex items-center justify-between text-xs text-gray-400 pt-3 border-t border-[#1F293D]">
                    <span>Showing {patents.length} of {patentTotal} patents</span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        disabled={patentPage <= 1}
                        onClick={() => loadPatents(patentPage - 1)}
                        className="px-3 py-1 rounded-lg bg-[#151D30] hover:bg-[#1F293D] disabled:opacity-40 text-gray-300 border border-[#1F293D] transition-colors cursor-pointer"
                      >
                        Previous
                      </button>
                      <span className="px-2 py-1 font-mono text-gray-300">Page {patentPage}</span>
                      <button
                        type="button"
                        disabled={patentPage * 10 >= patentTotal}
                        onClick={() => loadPatents(patentPage + 1)}
                        className="px-3 py-1 rounded-lg bg-[#151D30] hover:bg-[#1F293D] disabled:opacity-40 text-gray-300 border border-[#1F293D] transition-colors cursor-pointer"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* PRIOR-ART DEEP ANALYSIS MODAL */}
          {priorArtModalOpen && selectedPatentPriorArt && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
              <div className="w-full max-w-3xl max-h-[85vh] rounded-2xl bg-[#0E1424] border border-[#1F293D] shadow-2xl flex flex-col overflow-hidden">
                {/* Modal Header */}
                <div className="p-5 border-b border-[#1F293D] flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded font-mono font-bold text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {selectedPatentPriorArt.publication_number}
                      </span>
                      <span className="text-xs text-gray-400 font-mono">
                        Prior-Art Technical Deep Dive
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-white pt-1">
                      {selectedPatentPriorArt.title}
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setPriorArtModalOpen(false)}
                    className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-[#151D30] transition-colors"
                  >
                    ✕
                  </button>
                </div>

                {/* Modal Body */}
                <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
                  {/* Problem & Solution Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1.5">
                      <span className="font-semibold text-amber-300 text-xs">Technical Problem Disclosed:</span>
                      <p className="text-gray-300 leading-relaxed text-[11px]">
                        {selectedPatentPriorArt.technical_problem}
                      </p>
                    </div>
                    <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1.5">
                      <span className="font-semibold text-emerald-300 text-xs">Proposed Technical Solution:</span>
                      <p className="text-gray-300 leading-relaxed text-[11px]">
                        {selectedPatentPriorArt.proposed_solution}
                      </p>
                    </div>
                  </div>

                  {/* Similarities & Differences */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1.5">
                      <span className="font-semibold text-blue-300 text-xs">Conceptual Kinship with Project:</span>
                      <ul className="list-disc list-inside text-gray-300 text-[11px] space-y-1 pl-1">
                        {selectedPatentPriorArt.similarities_with_idea.map((sim: string, sIdx: number) => (
                          <li key={sIdx}>{sim}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1.5">
                      <span className="font-semibold text-purple-300 text-xs">Distinguishing Technical Differences:</span>
                      <ul className="list-disc list-inside text-gray-300 text-[11px] space-y-1 pl-1">
                        {selectedPatentPriorArt.differences_from_idea.map((diff: string, dIdx: number) => (
                          <li key={dIdx}>{diff}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Claims Scope Analysis */}
                  <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1.5">
                    <span className="font-semibold text-indigo-300 text-xs">Technical Claims Conceptual Scope:</span>
                    <p className="text-gray-300 text-[11px] leading-relaxed">
                      {selectedPatentPriorArt.claims_overlap_analysis}
                    </p>
                  </div>

                  {/* Limitations */}
                  <div className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-1.5">
                    <span className="font-semibold text-gray-400 text-xs">Disclosed Limitations:</span>
                    <p className="text-gray-400 text-[11px] leading-relaxed">
                      {selectedPatentPriorArt.limitation_observations}
                    </p>
                  </div>

                  {/* Legal Notice */}
                  <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200/90 text-[11px] leading-relaxed">
                    Legal Notice: This prior-art analysis is generated for research exploration and idea validation only. It does not constitute a legal freedom-to-operate opinion.
                  </div>
                </div>

                {/* Modal Footer */}
                <div className="p-3 bg-[#090D16] border-t border-[#1F293D] flex justify-end">
                  <button
                    type="button"
                    onClick={() => setPriorArtModalOpen(false)}
                    className="px-4 py-1.5 rounded-lg text-xs font-medium bg-[#151D30] hover:bg-[#1E293B] text-white border border-[#1F293D] transition-colors cursor-pointer"
                  >
                    Close Analysis
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* EVIDENCE MANIFEST EXPLORER MODAL */}
          {evidenceModalOpen && validationReport && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
              <div className="w-full max-w-4xl max-h-[85vh] rounded-2xl bg-[#0E1424] border border-[#1F293D] shadow-2xl flex flex-col overflow-hidden">
                {/* Modal Header */}
                <div className="p-5 border-b border-[#1F293D] flex items-center justify-between">
                  <div className="space-y-0.5">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-blue-400" />
                      <span>Traceable Evidence Manifest</span>
                      <span className="px-2 py-0.5 rounded text-xs font-mono bg-blue-500/20 text-blue-300">
                        {validationReport.evidence_manifest.length} Sources
                      </span>
                    </h3>
                    <p className="text-xs text-gray-400">
                      Underlying grounded citations retrieved and normalized for report v{validationReport.version}.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setEvidenceModalOpen(false)}
                    className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-[#151D30] transition-colors"
                  >
                    ✕
                  </button>
                </div>

                {/* Filter Bar */}
                <div className="p-3 bg-[#090D16] border-b border-[#1F293D] flex flex-wrap gap-2 text-xs">
                  {['all', 'research_paper', 'github_repository', 'patent', 'innovation_gap'].map((src) => (
                    <button
                      key={src}
                      type="button"
                      onClick={() => setEvidenceFilterType(src)}
                      className={`px-3 py-1 rounded-lg text-xs font-mono transition-colors ${
                        evidenceFilterType === src
                          ? 'bg-blue-600 text-white font-semibold'
                          : 'bg-[#151D30] text-gray-400 hover:text-white border border-[#1F293D]'
                      }`}
                    >
                      {src === 'all'
                        ? 'All Evidence'
                        : src === 'research_paper'
                        ? 'Academic Papers'
                        : src === 'github_repository'
                        ? 'GitHub Repositories'
                        : src === 'patent'
                        ? 'Patents & Prior Art'
                        : 'Candidate Gaps'}
                    </button>
                  ))}
                </div>

                {/* Evidence Items Scrollable List */}
                <div className="flex-1 overflow-y-auto p-5 space-y-3">
                  {validationReport.evidence_manifest
                    .filter((e) => evidenceFilterType === 'all' || e.source_type === evidenceFilterType)
                    .map((item, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-[#090D16] border border-[#1F293D] space-y-2 text-xs"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded font-mono font-bold text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30">
                              {item.evidence_id}
                            </span>
                            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#151D30] text-gray-400 border border-[#1F293D]">
                              {item.source_type.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase ${
                                item.evidence_strength === 'strong'
                                  ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                                  : item.evidence_strength === 'moderate'
                                  ? 'bg-blue-500/10 text-blue-300 border border-blue-500/30'
                                  : 'bg-amber-500/10 text-amber-300 border border-amber-500/30'
                              }`}
                            >
                              {item.evidence_strength}
                            </span>
                            {item.similarity_score !== undefined && item.similarity_score !== null && (
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
                                sim: {(item.similarity_score * 100).toFixed(1)}%
                              </span>
                            )}
                          </div>
                        </div>

                        <h4 className="text-sm font-semibold text-white">
                          {item.source_url ? (
                            <a
                              href={item.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:text-blue-300 inline-flex items-center gap-1.5 transition-colors"
                            >
                              <span>{item.source_title}</span>
                              <ExternalLink className="w-3.5 h-3.5 text-gray-500" />
                            </a>
                          ) : (
                            item.source_title
                          )}
                        </h4>

                        <div className="p-2.5 rounded bg-[#151D30] border border-[#1F293D] font-mono text-[11px] text-gray-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                          {item.evidence_content}
                        </div>
                      </div>
                    ))}
                </div>

                {/* Modal Footer */}
                <div className="p-3 bg-[#090D16] border-t border-[#1F293D] flex justify-end">
                  <button
                    type="button"
                    onClick={() => setEvidenceModalOpen(false)}
                    className="px-4 py-1.5 rounded-lg text-xs font-medium bg-[#151D30] hover:bg-[#1E293B] text-white border border-[#1F293D] transition-colors"
                  >
                    Close Explorer
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
};
