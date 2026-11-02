export interface EvidenceItem {
  evidence_id: string;
  project_id: string;
  source_type: 'research_paper' | 'github_repository' | 'repository_analysis' | 'innovation_gap';
  source_record_id: string;
  source_title: string;
  source_url?: string | null;
  source_author?: string | null;
  publication_year?: number | null;
  evidence_content: string;
  evidence_category: string;
  similarity_score?: number | null;
  evidence_strength: 'strong' | 'moderate' | 'weak' | 'insufficient';
  documented_or_inferred: 'documented' | 'inferred';
  retrieved_at: string;
}

export interface ProjectOverviewSection {
  project_title: string;
  problem_statement: string;
  proposed_solution: string;
  primary_domain: string;
  secondary_domains: string[];
  target_users: string[];
}

export interface AcademicResearchItem {
  evidence_id: string;
  title: string;
  authors: string[];
  publication_year?: number | null;
  venue?: string | null;
  doi?: string | null;
  url?: string | null;
  research_objectives: string;
  methods_and_technologies: string[];
  main_findings: string;
  evidence_supported_limitations: string;
  similarity_score?: number | null;
}

export interface ExistingAcademicResearchSection {
  relevant_papers: AcademicResearchItem[];
  research_synthesis_summary: string;
}

export interface SoftwareImplementationItem {
  evidence_id: string;
  repo_full_name: string;
  url?: string | null;
  stars_count: number;
  documented_features: string[];
  detected_technologies: string[];
  architecture_findings?: string | null;
  implementation_limitations?: string | null;
  similarity_score?: number | null;
}

export interface ExistingImplementationsSection {
  relevant_repositories: SoftwareImplementationItem[];
  implementation_landscape_summary: string;
}

export interface SimilarityAssessmentSection {
  top_research_papers: Array<{
    evidence_id?: string;
    title?: string;
    score?: number | null;
  }>;
  top_github_repositories: Array<{
    evidence_id?: string;
    name?: string;
    score?: number | null;
  }>;
  semantic_similarity_overview: string;
  structural_alignment_overview: string;
  score_divergence_explanation: string;
}

export interface CapabilityItem {
  capability_name: string;
  description: string;
  supporting_evidence_ids: string[];
  status: string;
}

export interface ExistingCapabilityAnalysisSection {
  already_addressed_capabilities: CapabilityItem[];
  partially_addressed_capabilities: CapabilityItem[];
  capabilities_with_insufficient_evidence: CapabilityItem[];
}

export interface ValidatedResearchGapItem {
  gap_title: string;
  description: string;
  category: string;
  validation_status: 'supported_gap' | 'partially_supported_gap' | 'not_supported_gap' | 'insufficient_evidence';
  priority: 'high' | 'medium' | 'low';
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  reasoning: string;
  confidence_level: 'strong' | 'moderate' | 'weak' | 'insufficient';
  suggested_direction: string;
}

export interface ValidatedResearchGapsSection {
  validated_gaps: ValidatedResearchGapItem[];
  gap_validation_summary: string;
}

export interface InnovationOpportunityItem {
  title: string;
  description: string;
  opportunity_type: string;
  supporting_evidence_ids: string[];
  expected_impact: string;
}

export interface InnovationOpportunitiesSection {
  differentiating_capabilities: InnovationOpportunityItem[];
  technical_improvements: InnovationOpportunityItem[];
  research_directions: InnovationOpportunityItem[];
}

export interface TechnicalRecommendationsSection {
  recommended_architecture: string;
  potential_algorithms: string[];
  suitable_technologies: string[];
  implementation_considerations: string[];
  citations: string[];
}

export interface RisksAndLimitationsSection {
  evidence_coverage_limitations: string;
  missing_metadata_impact: string;
  search_and_retrieval_limitations: string;
  unverified_assumptions: string[];
  false_positive_negative_risks: string;
}

export interface FinalAssessmentSection {
  overall_evidence_coverage: 'comprehensive' | 'adequate' | 'partial' | 'sparse';
  existing_work_summary: string;
  strongest_supported_gaps: string[];
  recommended_next_steps: string[];
  explicit_novelty_limitation: string;
}

export interface ProjectValidationReportSchema {
  project_overview: ProjectOverviewSection;
  academic_research: ExistingAcademicResearchSection;
  software_implementations: ExistingImplementationsSection;
  similarity_assessment: SimilarityAssessmentSection;
  capability_analysis: ExistingCapabilityAnalysisSection;
  validated_research_gaps: ValidatedResearchGapsSection;
  innovation_opportunities: InnovationOpportunitiesSection;
  technical_recommendations: TechnicalRecommendationsSection;
  risks_and_limitations: RisksAndLimitationsSection;
  final_assessment: FinalAssessmentSection;
  evidence_summary: Record<string, any>;
}

export interface ValidationGenerateRequest {
  force_regenerate?: boolean;
  max_papers?: number;
  max_repos?: number;
  max_gaps?: number;
  include_embeddings?: boolean;
}

export interface ValidationReportResponse {
  id: string;
  project_id: string;
  analysis_id?: string | null;
  user_id: string;
  version: number;
  report_status: string;
  model_name: string;
  report: ProjectValidationReportSchema;
  evidence_manifest: EvidenceItem[];
  retrieval_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ValidationReportSummary {
  id: string;
  project_id: string;
  analysis_id?: string | null;
  version: number;
  report_status: string;
  model_name: string;
  total_evidence_items: number;
  supported_gaps_count: number;
  overall_evidence_coverage: string;
  created_at: string;
}

export interface ValidationHistoryResponse {
  project_id: string;
  total_reports: number;
  reports: ValidationReportSummary[];
}

export interface EvidenceManifestResponse {
  project_id: string;
  report_id: string;
  version: number;
  total_evidence_items: number;
  evidence_items: EvidenceItem[];
  counts_by_source: Record<string, number>;
  retrieval_metadata: Record<string, any>;
}

