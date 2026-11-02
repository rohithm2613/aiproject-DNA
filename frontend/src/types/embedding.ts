export interface EmbeddingGenerateRequest {
  force_regenerate?: boolean;
  include_papers?: boolean;
  include_repos?: boolean;
}

export interface EmbeddingGenerateResponse {
  status: 'completed' | 'partial_success' | 'failed' | string;
  project_id: string;
  model_name: string;
  embedding_dimension: number;
  total_generated: number;
  total_skipped: number;
  total_failed: number;
  counts_by_source: Record<string, number>;
  errors: Record<string, string>;
  generated_at: string;
}

export interface SemanticMatchItem {
  rank: number;
  source_type: 'research_paper' | 'github_repository' | string;
  source_record_id: string;
  title: string;
  url?: string | null;
  similarity_score: number;
  similarity_percentage: number;
  similarity_label: 'High semantic similarity' | 'Moderate semantic similarity' | 'Low semantic similarity' | string;
  matching_content_summary: string;
  matched_aspects: string[];
  model_name: string;
  metadata: {
    title?: string;
    url?: string | null;
    venue?: string | null;
    year?: number | null;
    language?: string | null;
    stargazers_count?: number | null;
    provider?: string | null;
    open_access?: boolean | null;
    preview?: string;
    has_deep_analysis?: boolean;
    [key: string]: any;
  };
}

export interface CrossSourceSimilarityResponse {
  project_id: string;
  model_name: string;
  embedding_dimension: number;
  total_matches: number;
  matches: SemanticMatchItem[];
  disclaimer: string;
}

export interface SimilarityStatsResponse {
  project_id: string;
  model_name: string;
  embedding_dimension: number;
  total_embeddings_stored: number;
  embeddings_by_source_type: Record<string, number>;
  latest_generation_timestamp?: string | null;
  total_matches_available: number;
  has_project_embedding: boolean;
}

