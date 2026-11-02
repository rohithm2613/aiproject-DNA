from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TechnologyStackResponse(BaseModel):
    """Categorized technologies detected with evidence."""
    programming_languages: List[str] = Field(default_factory=list)
    frontend_frameworks: List[str] = Field(default_factory=list)
    backend_frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    ai_ml_libraries: List[str] = Field(default_factory=list)
    cloud_deployment: List[str] = Field(default_factory=list)
    devops_tools: List[str] = Field(default_factory=list)
    evidence: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Maps detected technology name to supporting evidence (e.g. dependency file, README citation)"
    )

class ExtractedFeatureResponse(BaseModel):
    """Individual feature extracted from repository documentation."""
    feature_name: str
    description: str
    evidence_source: str
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    is_documented: bool = Field(default=True, description="True if documented in README/docs, False if inferred")

class ArchitectureAnalysisResponse(BaseModel):
    """Architectural components and system topology."""
    frontend_components: List[str] = Field(default_factory=list)
    backend_services: List[str] = Field(default_factory=list)
    database_technologies: List[str] = Field(default_factory=list)
    external_integrations: List[str] = Field(default_factory=list)
    ai_ml_components: List[str] = Field(default_factory=list)
    deployment_configuration: List[str] = Field(default_factory=list)
    architecture_summary: Optional[str] = None

class SimilarityAnalysisResponse(BaseModel):
    """Multi-factor similarity comparison between user project idea and repository."""
    overall_score: float = Field(ge=0.0, le=100.0, description="Weighted composite score (0-100)")
    problem_similarity_score: float = Field(ge=0.0, le=100.0, description="Problem statement alignment")
    feature_similarity_score: float = Field(ge=0.0, le=100.0, description="Feature capability overlap")
    technology_overlap_score: float = Field(ge=0.0, le=100.0, description="Technology stack intersection")
    domain_similarity_score: float = Field(ge=0.0, le=100.0, description="Domain and category alignment")
    explanation: str = Field(description="Transparent breakdown of similarity rationale")

class RepositoryAnalysisSchema(BaseModel):
    """Deep analysis record for an individual discovered repository."""
    id: Optional[str] = None
    project_id: str
    github_repo_id: str
    user_id: Optional[str] = None
    repo_full_name: str
    readme_present: bool = False
    readme_url: Optional[str] = None
    readme_size: Optional[int] = None
    summary: Optional[str] = None
    problem_statement: Optional[str] = None
    detected_technologies: TechnologyStackResponse = Field(default_factory=TechnologyStackResponse)
    architecture: ArchitectureAnalysisResponse = Field(default_factory=ArchitectureAnalysisResponse)
    features: List[ExtractedFeatureResponse] = Field(default_factory=list)
    similarity: Optional[SimilarityAnalysisResponse] = None
    analysis_status: str = "completed"  # completed, failed, partial
    analysis_mode: str = "ai_enhanced"  # ai_enhanced, deterministic_fallback
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class InnovationGapResponse(BaseModel):
    """Identified market, research, or capability gap relative to analyzed repositories."""
    id: Optional[str] = None
    project_id: str
    user_id: Optional[str] = None
    gap_title: str
    category: str = Field(
        description="missing_feature | partially_implemented | improvement_opportunity | differentiating_feature"
    )
    description: str
    why_it_matters: str
    suggested_implementation: str
    priority: str = Field(default="medium", description="high | medium | low")
    confidence_level: str = Field(default="medium", description="high | medium | low")
    supporting_evidence: List[str] = Field(default_factory=list, description="Citations to analyzed repositories")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RepositoryAnalysisRequest(BaseModel):
    """Parameters for triggering repository deep analysis."""
    max_repositories: int = Field(default=10, ge=1, le=30, description="Max repositories to analyze in this batch")
    force_refresh: bool = Field(default=False, description="Whether to re-analyze already analyzed repositories")

class RepositoryAnalysisBatchResponse(BaseModel):
    """Result of batch repository deep analysis and innovation gap detection."""
    status: str = "completed"  # completed, partial_success, failed
    project_id: str
    total_discovered_repositories: int = 0
    total_analyzed: int = 0
    analyzed_repositories: List[RepositoryAnalysisSchema] = Field(default_factory=list)
    innovation_gaps: List[InnovationGapResponse] = Field(default_factory=list)
    errors: Dict[str, str] = Field(default_factory=dict)
    analysis_mode: str = "ai_enhanced"

class RepositoryAnalysisListResponse(BaseModel):
    """Paginated list of stored repository analyses."""
    total: int
    page: int
    page_size: int
    items: List[RepositoryAnalysisSchema] = Field(default_factory=list)

class InnovationGapListResponse(BaseModel):
    """List of identified innovation gaps."""
    total: int
    items: List[InnovationGapResponse] = Field(default_factory=list)

class RepositoryAnalysisStatsResponse(BaseModel):
    """Aggregated statistics across analyzed repositories and innovation gaps."""
    project_id: str
    total_analyzed_repositories: int = 0
    average_similarity_score: float = 0.0
    technology_distribution: Dict[str, int] = Field(default_factory=dict)
    total_features_extracted: int = 0
    innovation_gaps_count: int = 0
    gaps_by_priority: Dict[str, int] = Field(default_factory=dict)
    gaps_by_category: Dict[str, int] = Field(default_factory=dict)

