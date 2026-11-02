from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class GitHubRateLimitInfo(BaseModel):
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset: Optional[int] = None
    used: Optional[int] = None

class GitHubRepositorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    project_id: Optional[str] = None
    analysis_id: Optional[str] = None
    user_id: Optional[str] = None
    github_repository_id: int
    full_name: str
    name: str
    owner_login: str
    owner_type: Optional[str] = None
    description: Optional[str] = None
    html_url: str
    homepage: Optional[str] = None
    language: Optional[str] = None
    languages: Dict[str, int] = Field(default_factory=dict)
    topics: List[str] = Field(default_factory=list)
    stargazers_count: int = 0
    forks_count: int = 0
    watchers_count: int = 0
    open_issues_count: int = 0
    default_branch: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None
    license_name: Optional[str] = None
    archived: bool = False
    fork: bool = False
    visibility: str = "public"
    size: Optional[int] = None
    search_query: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    created_at_db: Optional[datetime] = None

class GitHubSearchRequest(BaseModel):
    analysis_id: Optional[str] = None
    max_results: int = Field(default=30, ge=1, le=100, description="Max repositories to retrieve in total")
    sort: Optional[str] = Field(default="stars", description="stars, forks, or updated")
    order: Optional[str] = Field(default="desc", description="desc or asc")

class GitHubSearchResponse(BaseModel):
    status: str  # 'completed', 'partial_success', 'failed'
    project_id: str
    analysis_id: Optional[str] = None
    queries_executed: List[str] = Field(default_factory=list)
    total_retrieved: int = 0
    new_stored: int = 0
    existing_updated: int = 0
    duplicates_skipped: int = 0
    per_query_counts: Dict[str, int] = Field(default_factory=dict)
    rate_limit: Optional[GitHubRateLimitInfo] = None
    errors: Dict[str, str] = Field(default_factory=dict)
    total_stored_repositories: int = 0
    repositories: List[GitHubRepositorySchema] = Field(default_factory=list)

class GitHubRepositoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[GitHubRepositorySchema] = Field(default_factory=list)

class GitHubStatsResponse(BaseModel):
    project_id: str
    total_repositories: int = 0
    language_distribution: Dict[str, int] = Field(default_factory=dict)
    total_stars: int = 0
    total_forks: int = 0
    archived_count: int = 0
    fork_count: int = 0
    latest_discovery_at: Optional[str] = None

