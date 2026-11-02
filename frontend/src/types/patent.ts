export type PatentProviderName = 'uspto' | 'epo' | string;

export interface Patent {
  id: string;
  project_id: string;
  analysis_id?: string | null;
  user_id: string;
  provider: PatentProviderName;
  provider_patent_id: string;
  publication_number: string;
  application_number?: string | null;
  patent_number?: string | null;
  title: string;
  abstract?: string | null;
  description?: string | null;
  claims: string[];
  inventors: string[];
  assignees: string[];
  filing_date?: string | null;
  publication_date?: string | null;
  grant_date?: string | null;
  priority_date?: string | null;
  jurisdiction?: string | null;
  patent_type?: string | null;
  cpc_classifications: string[];
  ipc_classifications: string[];
  patent_family_id?: string | null;
  legal_status?: string | null;
  source_url?: string | null;
  similarity_score?: number | null;
  similarity_band?: string | null;
  retrieved_at: string;
  created_at?: string;
}

export interface PatentSearchRequest {
  analysis_id?: string;
  max_results?: number;
  providers?: string[];
  jurisdictions?: string[];
  query_override?: string;
}

export interface PatentSearchResponse {
  status: 'completed' | 'partial_success' | 'failed' | string;
  project_id: string;
  analysis_id?: string | null;
  queries_executed: string[];
  provider_counts: Record<string, number>;
  new_stored: number;
  duplicates_skipped: number;
  provider_errors: Record<string, string>;
  total_stored_patents: number;
  patents: Patent[];
  disclaimer: string;
}

export interface PatentListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Patent[];
  disclaimer: string;
}

export interface PatentStatsResponse {
  project_id: string;
  total_patents: number;
  by_provider: Record<string, number>;
  by_jurisdiction: Record<string, number>;
  top_classifications: Record<string, number>;
  top_assignees: Record<string, number>;
  high_similarity_count: number;
  moderate_similarity_count: number;
  low_similarity_count: number;
  most_recent_retrieval?: string | null;
  disclaimer: string;
}

export interface PriorArtAnalysisItem {
  patent_id: string;
  publication_number: string;
  title: string;
  jurisdiction?: string | null;
  technical_problem: string;
  proposed_solution: string;
  key_features: string[];
  similarities_with_idea: string[];
  differences_from_idea: string[];
  claims_overlap_analysis: string;
  limitation_observations: string;
  similarity_score?: number | null;
  similarity_band?: string | null;
}

export interface PatentAnalyzeRequest {
  patent_ids?: string[];
  max_patents?: number;
}

export interface PatentAnalysisResponse {
  project_id: string;
  total_analyzed: number;
  prior_art_analyses: PriorArtAnalysisItem[];
  overall_prior_art_summary: string;
  technical_differentiation_opportunities: string[];
  disclaimer: string;
}

export interface PatentEvidenceManifestItem {
  evidence_id: string;
  patent_id: string;
  publication_number: string;
  title: string;
  jurisdiction?: string | null;
  similarity_score?: number | null;
  snippet: string;
}

