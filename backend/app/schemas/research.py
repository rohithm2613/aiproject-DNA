from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ResearchPaperSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    project_id: Optional[str] = None
    analysis_id: Optional[str] = None
    user_id: Optional[str] = None
    provider: str  # 'arxiv', 'semantic_scholar', 'openalex'
    provider_paper_id: str
    title: str
    abstract: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    citation_count: Optional[int] = None
    paper_url: Optional[str] = None
    pdf_url: Optional[str] = None
    open_access: Optional[bool] = None
    primary_category: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class ResearchSearchRequest(BaseModel):
    analysis_id: Optional[str] = None
    max_results: int = Field(default=20, ge=1, le=50, description="Max results per provider")
    providers: Optional[List[str]] = Field(
        default=None,
        description="List of providers to query. Defaults to ['arxiv', 'semantic_scholar', 'openalex']"
    )

class ResearchSearchResponse(BaseModel):
    status: str  # 'completed', 'partial_success', 'failed'
    project_id: str
    analysis_id: Optional[str] = None
    queries_executed: List[str] = Field(default_factory=list)
    provider_counts: Dict[str, int] = Field(default_factory=dict)
    new_stored: int = 0
    duplicates_skipped: int = 0
    provider_errors: Dict[str, str] = Field(default_factory=dict)
    total_stored_papers: int = 0
    papers: List[ResearchPaperSchema] = Field(default_factory=list)

class ResearchListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ResearchPaperSchema] = Field(default_factory=list)

class ResearchStatsResponse(BaseModel):
    project_id: str
    total_papers: int = 0
    by_provider: Dict[str, int] = Field(default_factory=dict)
    open_access_count: int = 0
    year_distribution: Dict[str, int] = Field(default_factory=dict)
    most_recent_retrieval: Optional[str] = None

