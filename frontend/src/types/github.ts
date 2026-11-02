export interface GitHubRepository {
  id?: string;
  project_id?: string;
  analysis_id?: string | null;
  github_repository_id: number;
  full_name: string;
  name: string;
  owner_login: string;
  owner_avatar_url?: string | null;
  owner_html_url?: string | null;
  html_url: string;
  description?: string | null;
  homepage?: string | null;
  language?: string | null;
  topics: string[];
  stargazers_count: number;
  forks_count: number;
  watchers_count: number;
  open_issues_count: number;
  license_name?: string | null;
  license_spdx?: string | null;
  default_branch?: string;
  archived: boolean;
  fork: boolean;
  created_at_repo?: string | null;
  updated_at_repo?: string | null;
  pushed_at_repo?: string | null;
  visibility?: string;
  size?: number | null;
  search_query?: string | null;
  retrieved_at?: string | null;
  created_at_db?: string | null;
}

export interface GitHubRateLimitInfo {
  limit?: number | null;
  remaining?: number | null;
  reset?: number | null;
  used?: number | null;
}

export interface GitHubSearchRequest {
  analysis_id?: string;
  max_results?: number;
  sort?: 'stars' | 'forks' | 'updated' | string;
  order?: 'desc' | 'asc' | string;
}

export interface GitHubSearchResponse {
  status: 'completed' | 'partial_success' | 'failed' | string;
  project_id: string;
  analysis_id?: string | null;
  queries_executed: string[];
  total_retrieved: number;
  new_stored: number;
  existing_updated: number;
  duplicates_skipped: number;
  per_query_counts: Record<string, number>;
  rate_limit?: GitHubRateLimitInfo | null;
  errors: Record<string, string>;
  total_stored_repositories: number;
  repositories: GitHubRepository[];
}

export interface GitHubRepositoryListResponse {
  total: number;
  page: number;
  page_size: number;
  items: GitHubRepository[];
}

export interface GitHubStatsResponse {
  project_id: string;
  total_repositories: number;
  language_distribution: Record<string, number>;
  total_stars: number;
  total_forks: number;
  archived_count: number;
  fork_count: number;
}

export interface GitHubFilterParams {
  language?: string;
  min_stars?: number;
  topic?: string;
  archived?: boolean;
  fork?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
  sort_by?: 'stars' | 'forks' | 'updated' | string;
  sort_order?: 'desc' | 'asc' | string;
}

