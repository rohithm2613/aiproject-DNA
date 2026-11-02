export type ResearchProviderName = 'arxiv' | 'semantic_scholar' | 'openalex';

export interface ResearchPaper {
  id: string;
  project_id: string;
  analysis_id?: string | null;
  user_id: string;
  provider: ResearchProviderName | string;
  provider_paper_id: string;
  title: string;
  abstract?: string | null;
  authors: string[];
  publication_year?: number | null;
  publication_date?: string | null;
  venue?: string | null;
  doi?: string | null;
  arxiv_id?: string | null;
  citation_count?: number | null;
  paper_url?: string | null;
  pdf_url?: string | null;
  open_access?: boolean | null;
  primary_category?: string | null;
  retrieved_at: string;
  created_at?: string;
}

export interface ResearchSearchRequest {
  analysis_id?: string;
  max_results?: number;
  providers?: string[];
}

export interface ResearchSearchResponse {
  status: 'completed' | 'partial_success' | 'failed' | string;
  project_id: string;
  analysis_id?: string | null;
  queries_executed: string[];
  provider_counts: Record<string, number>;
  new_stored: number;
  duplicates_skipped: number;
  provider_errors: Record<string, string>;
  total_stored_papers: number;
  papers: ResearchPaper[];
}

export interface ResearchListResponse {
  total: number;
  page: number;
  page_size: number;
  items: ResearchPaper[];
}

export interface ResearchStatsResponse {
  project_id: string;
  total_papers: number;
  by_provider: Record<string, number>;
  open_access_count: number;
  year_distribution: Record<string, number>;
  most_recent_retrieval?: string | null;
}

export interface ResearchFilterParams {
  provider?: string;
  year?: number;
  open_access?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

