export interface TechnologyStack {
  programming_languages: string[];
  frontend_frameworks: string[];
  backend_frameworks: string[];
  databases: string[];
  ai_ml_libraries: string[];
  cloud_deployment: string[];
  devops_tools: string[];
  evidence_sources?: Record<string, string>;
}

export interface ExtractedFeature {
  feature_name: string;
  description: string;
  evidence_source: string;
  confidence_score: number;
  is_documented: boolean;
}

export interface ArchitectureAnalysis {
  frontend_architecture?: string | null;
  backend_architecture?: string | null;
  database_layer?: string | null;
  external_apis?: string[];
  ai_ml_pipeline?: string | null;
  deployment_infrastructure?: string | null;
  architecture_summary?: string | null;
}

export interface SimilarityAnalysis {
  overall_score: number;
  problem_overlap: number;
  feature_overlap: number;
  tech_stack_overlap: number;
  domain_similarity: number;
  similarity_explanation: string;
}

export interface RepositoryAnalysis {
  id?: string;
  project_id: string;
  github_repo_id: string;
  user_id?: string | null;
  repo_full_name: string;
  readme_present: boolean;
  readme_url?: string | null;
  readme_size?: number | null;
  summary?: string | null;
  problem_statement?: string | null;
  detected_technologies: TechnologyStack;
  architecture: ArchitectureAnalysis;
  features: ExtractedFeature[];
  similarity?: SimilarityAnalysis | null;
  analysis_status: 'completed' | 'failed' | 'partial' | string;
  analysis_mode: 'ai_enhanced' | 'deterministic_fallback' | string;
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export type InnovationGapCategory = 
  | 'missing_feature' 
  | 'partially_implemented' 
  | 'improvement_opportunity' 
  | 'differentiating_feature';

export type InnovationGapPriority = 'high' | 'medium' | 'low';

export interface InnovationGap {
  id?: string;
  project_id: string;
  user_id?: string | null;
  gap_title: string;
  category: InnovationGapCategory;
  description: string;
  why_it_matters: string;
  suggested_implementation: string;
  priority: InnovationGapPriority;
  confidence_level: 'high' | 'medium' | 'low' | string;
  supporting_evidence: string[];
  created_at?: string | null;
  updated_at?: string | null;
}

export interface RepositoryAnalysisRequest {
  max_repositories?: number;
  force_refresh?: boolean;
}

export interface RepositoryAnalysisBatchResponse {
  status: 'completed' | 'partial_success' | 'failed' | string;
  project_id: string;
  total_discovered_repositories: number;
  total_analyzed: number;
  analyzed_repositories: RepositoryAnalysis[];
  innovation_gaps: InnovationGap[];
  errors: Record<string, string>;
  analysis_mode: 'ai_enhanced' | 'deterministic_fallback' | string;
}

export interface RepositoryAnalysisListResponse {
  total: number;
  page: number;
  page_size: number;
  items: RepositoryAnalysis[];
}

export interface InnovationGapListResponse {
  total: number;
  items: InnovationGap[];
}

export interface RepositoryAnalysisStats {
  project_id: string;
  total_analyzed_repositories: number;
  average_similarity_score: number;
  technology_distribution: Record<string, number>;
  total_features_extracted: number;
  innovation_gaps_count: number;
  gaps_by_priority: Record<string, number>;
  gaps_by_category: Record<string, number>;
}

