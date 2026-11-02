from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

LEGAL_DISCLAIMER = (
    "Preliminary research assistance only. Does not constitute a legal patentability opinion "
    "or formal freedom-to-operate search. Patent scope is defined strictly by issued legal claims."
)

class PatentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    project_id: Optional[str] = None
    analysis_id: Optional[str] = None
    user_id: Optional[str] = None
    provider: str  # 'uspto', 'epo'
    provider_patent_id: str
    publication_number: str
    application_number: Optional[str] = None
    patent_number: Optional[str] = None
    title: str
    abstract: Optional[str] = None
    description: Optional[str] = None
    claims: List[str] = Field(default_factory=list)
    inventors: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    filing_date: Optional[str] = None
    publication_date: Optional[str] = None
    grant_date: Optional[str] = None
    priority_date: Optional[str] = None
    jurisdiction: Optional[str] = None
    patent_type: Optional[str] = None
    cpc_classifications: List[str] = Field(default_factory=list)
    ipc_classifications: List[str] = Field(default_factory=list)
    patent_family_id: Optional[str] = None
    legal_status: Optional[str] = None
    source_url: Optional[str] = None
    similarity_score: Optional[float] = None
    similarity_band: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class PatentSearchRequest(BaseModel):
    analysis_id: Optional[str] = None
    max_results: int = Field(default=25, ge=1, le=50, description="Max results per provider")
    providers: Optional[List[str]] = Field(
        default=None,
        description="List of providers to query. Defaults to ['uspto', 'epo']"
    )
    jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="Filter jurisdictions, e.g. ['US', 'EP', 'WO']"
    )
    query_override: Optional[str] = Field(
        default=None,
        description="Optional custom keyword query to search instead of generating from analysis"
    )

class PatentSearchResponse(BaseModel):
    status: str  # 'completed', 'partial_success', 'failed'
    project_id: str
    analysis_id: Optional[str] = None
    queries_executed: List[str] = Field(default_factory=list)
    provider_counts: Dict[str, int] = Field(default_factory=dict)
    new_stored: int = 0
    duplicates_skipped: int = 0
    provider_errors: Dict[str, str] = Field(default_factory=dict)
    total_stored_patents: int = 0
    patents: List[PatentSchema] = Field(default_factory=list)
    disclaimer: str = LEGAL_DISCLAIMER

class PatentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[PatentSchema] = Field(default_factory=list)
    disclaimer: str = LEGAL_DISCLAIMER

class PatentStatsResponse(BaseModel):
    project_id: str
    total_patents: int = 0
    by_provider: Dict[str, int] = Field(default_factory=dict)
    by_jurisdiction: Dict[str, int] = Field(default_factory=dict)
    top_classifications: Dict[str, int] = Field(default_factory=dict)
    top_assignees: Dict[str, int] = Field(default_factory=dict)
    high_similarity_count: int = 0
    moderate_similarity_count: int = 0
    low_similarity_count: int = 0
    most_recent_retrieval: Optional[str] = None
    disclaimer: str = LEGAL_DISCLAIMER

class PriorArtAnalysisItem(BaseModel):
    patent_id: str
    publication_number: str
    title: str
    jurisdiction: Optional[str] = None
    technical_problem: str
    proposed_solution: str
    key_features: List[str] = Field(default_factory=list)
    similarities_with_idea: List[str] = Field(default_factory=list)
    differences_from_idea: List[str] = Field(default_factory=list)
    claims_overlap_analysis: str
    limitation_observations: str
    similarity_score: Optional[float] = None
    similarity_band: Optional[str] = None

class PatentAnalyzeRequest(BaseModel):
    patent_ids: Optional[List[str]] = Field(default=None, description="Optional subset of patent IDs to analyze")
    max_patents: int = Field(default=10, ge=1, le=25)

class PatentAnalysisResponse(BaseModel):
    project_id: str
    total_analyzed: int
    prior_art_analyses: List[PriorArtAnalysisItem] = Field(default_factory=list)
    overall_prior_art_summary: str
    technical_differentiation_opportunities: List[str] = Field(default_factory=list)
    disclaimer: str = LEGAL_DISCLAIMER

class PatentEvidenceManifestItem(BaseModel):
    evidence_id: str
    patent_id: str
    publication_number: str
    title: str
    jurisdiction: Optional[str] = None
    similarity_score: Optional[float] = None
    snippet: str

