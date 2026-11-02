export interface RecommendedTechnologies {
  languages: string[];
  frameworks: string[];
  algorithms: string[];
  hardware: string[];
  tools: string[];
  infrastructure: string[];
}

export interface ProjectRequirements {
  possible_datasets: string[];
  hardware_requirements: string[];
  software_requirements: string[];
  external_dependencies: string[];
  technical_constraints: string[];
}

export interface ProjectRisks {
  technical_challenges: string[];
  implementation_risks: string[];
}

export interface ProjectAnalysis {
  id: string;
  project_id: string;
  user_id: string;
  version: number;
  project_summary: string;
  problem_statement: string;
  proposed_solution: string;
  primary_domain: string;
  secondary_domains: string[];
  keywords: string[];
  user_technologies: string[];
  recommended_technologies: RecommendedTechnologies;
  objectives: string[];
  target_users: string[];
  project_type: string;
  difficulty_level: string;
  difficulty_reasoning: string;
  requirements: ProjectRequirements;
  assumptions: string[];
  risks: ProjectRisks;
  model_name: string;
  analysis_status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectAnalysisListResponse {
  project_id: string;
  total_versions: number;
  analyses: ProjectAnalysis[];
}

export interface RecentAnalysisItem {
  id: string;
  project_id: string;
  project_title: string;
  version: number;
  primary_domain: string;
  difficulty_level: string;
  project_type: string;
  created_at: string;
}

export interface DashboardAnalytics {
  total_projects: number;
  ideas_analyzed: number;
  pending_analyses: number;
  completed_analyses: number;
  recent_analyses: RecentAnalysisItem[];
}

