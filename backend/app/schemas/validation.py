from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field

# ============================================================================
# Normalized Evidence Schemas
# ============================================================================

class EvidenceItem(BaseModel):
    """Normalized evidence unit retrieved from papers, repos, analyses, or patents."""
    evidence_id: str = Field(description="Unique deterministic ID, e.g. EVID-PAP-01, EVID-REP-01, EVID-GAP-01, EVID-PAT-01")
    project_id: str
    source_type: Literal["research_paper", "github_repository", "repository_analysis", "innovation_gap", "patent"]
    source_record_id: str = Field(description="Underlying database record UUID or ID")
    source_title: str
    source_url: Optional[str] = None
    source_author: Optional[str] = None
    publication_year: Optional[int] = None
    evidence_content: str = Field(description="Sanitized text excerpt or summary used as grounded evidence")
    evidence_category: str = Field(description="Domain category, methodology, feature capability, or architecture")
    similarity_score: Optional[float] = Field(default=None, description="Cosine similarity score (0.0 to 1.0) if available")
    evidence_strength: Literal["strong", "moderate", "weak", "insufficient"] = "moderate"
    documented_or_inferred: Literal["documented", "inferred"] = "documented"
    retrieved_at: str

# ============================================================================
# Section Sub-Schemas for Structured RAG Validation Report
# ============================================================================

class ProjectOverviewSection(BaseModel):
    project_title: str
    problem_statement: str
    proposed_solution: str
    primary_domain: str
    secondary_domains: List[str] = Field(default_factory=list)
    target_users: List[str] = Field(default_factory=list)

class AcademicResearchItem(BaseModel):
    evidence_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    publication_year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    research_objectives: str
    methods_and_technologies: List[str] = Field(default_factory=list)
    main_findings: str
    evidence_supported_limitations: str
    similarity_score: Optional[float] = None

class ExistingAcademicResearchSection(BaseModel):
    relevant_papers: List[AcademicResearchItem] = Field(default_factory=list)
    research_synthesis_summary: str

class SoftwareImplementationItem(BaseModel):
    evidence_id: str
    repo_full_name: str
    url: Optional[str] = None
    stars_count: int = 0
    documented_features: List[str] = Field(default_factory=list)
    detected_technologies: List[str] = Field(default_factory=list)
    architecture_findings: Optional[str] = None
    implementation_limitations: Optional[str] = None
    similarity_score: Optional[float] = None

class ExistingImplementationsSection(BaseModel):
    relevant_repositories: List[SoftwareImplementationItem] = Field(default_factory=list)
    implementation_landscape_summary: str

class SimilarityAssessmentSection(BaseModel):
    top_research_papers: List[Dict[str, Any]] = Field(default_factory=list)
    top_github_repositories: List[Dict[str, Any]] = Field(default_factory=list)
    top_patents: List[Dict[str, Any]] = Field(default_factory=list)
    semantic_similarity_overview: str
    structural_alignment_overview: str
    score_divergence_explanation: str

class CapabilityItem(BaseModel):
    capability_name: str
    description: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    status: str = "addressed"

class ExistingCapabilityAnalysisSection(BaseModel):
    already_addressed_capabilities: List[CapabilityItem] = Field(default_factory=list)
    partially_addressed_capabilities: List[CapabilityItem] = Field(default_factory=list)
    capabilities_with_insufficient_evidence: List[CapabilityItem] = Field(default_factory=list)

class ValidatedResearchGapItem(BaseModel):
    gap_title: str
    description: str
    category: str
    validation_status: Literal["supported_gap", "partially_supported_gap", "not_supported_gap", "insufficient_evidence"]
    priority: Literal["high", "medium", "low"]
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    reasoning: str
    confidence_level: Literal["strong", "moderate", "weak", "insufficient"]
    suggested_direction: str

class ValidatedResearchGapsSection(BaseModel):
    validated_gaps: List[ValidatedResearchGapItem] = Field(default_factory=list)
    gap_validation_summary: str

class InnovationOpportunityItem(BaseModel):
    title: str
    description: str
    opportunity_type: str = "differentiating_feature"
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    expected_impact: str

class InnovationOpportunitiesSection(BaseModel):
    differentiating_capabilities: List[InnovationOpportunityItem] = Field(default_factory=list)
    technical_improvements: List[InnovationOpportunityItem] = Field(default_factory=list)
    research_directions: List[InnovationOpportunityItem] = Field(default_factory=list)

class TechnicalRecommendationsSection(BaseModel):
    recommended_architecture: str
    potential_algorithms: List[str] = Field(default_factory=list)
    suitable_technologies: List[str] = Field(default_factory=list)
    implementation_considerations: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)

class RisksAndLimitationsSection(BaseModel):
    evidence_coverage_limitations: str
    missing_metadata_impact: str
    search_and_retrieval_limitations: str
    unverified_assumptions: List[str] = Field(default_factory=list)
    false_positive_negative_risks: str

class FinalAssessmentSection(BaseModel):
    overall_evidence_coverage: Literal["comprehensive", "adequate", "partial", "sparse"]
    existing_work_summary: str
    strongest_supported_gaps: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    explicit_novelty_limitation: str = (
        "This validation report reflects evidence found in the analyzed sample of academic research papers "
        "and GitHub repositories. It does not certify global originality or complete absence of similar prior art."
    )

# ============================================================================
# Complete Structured RAG Validation Report Schema
# ============================================================================

class ProjectValidationReportSchema(BaseModel):
    """Structured 10-section RAG validation dossier output."""
    project_overview: ProjectOverviewSection
    academic_research: ExistingAcademicResearchSection
    software_implementations: ExistingImplementationsSection
    similarity_assessment: SimilarityAssessmentSection
    capability_analysis: ExistingCapabilityAnalysisSection
    validated_research_gaps: ValidatedResearchGapsSection
    innovation_opportunities: InnovationOpportunitiesSection
    technical_recommendations: TechnicalRecommendationsSection
    risks_and_limitations: RisksAndLimitationsSection
    final_assessment: FinalAssessmentSection
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)

# ============================================================================
# Request / Response Schemas for API Endpoints
# ============================================================================

class ValidationGenerateRequest(BaseModel):
    force_regenerate: bool = Field(default=False, description="Re-run RAG pipeline and increment report version")
    max_papers: int = Field(default=15, ge=1, le=50)
    max_repos: int = Field(default=15, ge=1, le=50)
    max_gaps: int = Field(default=20, ge=1, le=50)
    include_embeddings: bool = Field(default=True, description="Use semantic similarity to rank evidence")

class ValidationReportResponse(BaseModel):
    id: str
    project_id: str
    analysis_id: Optional[str] = None
    user_id: str
    version: int
    report_status: str
    model_name: str
    report: ProjectValidationReportSchema
    evidence_manifest: List[EvidenceItem] = Field(default_factory=list)
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

class ValidationReportSummary(BaseModel):
    id: str
    project_id: str
    analysis_id: Optional[str] = None
    version: int
    report_status: str
    model_name: str
    total_evidence_items: int = 0
    supported_gaps_count: int = 0
    overall_evidence_coverage: str = "adequate"
    created_at: datetime

class ValidationHistoryResponse(BaseModel):
    project_id: str
    total_reports: int
    reports: List[ValidationReportSummary] = Field(default_factory=list)

class EvidenceManifestResponse(BaseModel):
    project_id: str
    report_id: str
    version: int
    total_evidence_items: int
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    counts_by_source: Dict[str, int] = Field(default_factory=dict)
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)

