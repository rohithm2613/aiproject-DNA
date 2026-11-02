from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.research import (
    ResearchSearchRequest,
    ResearchSearchResponse,
    ResearchListResponse,
    ResearchStatsResponse,
)
from app.services.project_service import ProjectService
from app.services.research.research_discovery_service import research_discovery_service

router = APIRouter(tags=["Research Paper Discovery"])

def _verify_project_ownership(db: Session, project_id: str, current_user_id: str):
    """Verifies that project exists and belongs strictly to the authenticated user."""
    project = ProjectService.get_project_by_id(db=db, project_id=project_id, user_id=current_user_id)
    if not project:
        if ProjectService.check_project_exists(db=db, project_id=project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to access research for this project."
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    return project

@router.post(
    "/projects/{project_id}/research/search",
    response_model=ResearchSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover academic research papers across arXiv, Semantic Scholar, and OpenAlex"
)
async def search_research_papers(
    project_id: str,
    payload: Optional[ResearchSearchRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes academic paper discovery for the user's project across arXiv, Semantic Scholar,
    and OpenAlex using search queries derived from the project and its Phase 3 AI analysis.
    Normalizes metadata, deduplicates papers, and persists unique records.
    """
    project = _verify_project_ownership(db, project_id, current_user.id)

    req = payload or ResearchSearchRequest()
    response = await research_discovery_service.search_and_persist(
        db=db,
        project=project,
        user_id=current_user.id,
        analysis_id=req.analysis_id,
        max_results=req.max_results,
        selected_providers=req.providers,
    )
    return response

@router.get(
    "/projects/{project_id}/research",
    response_model=ResearchListResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve stored research papers with filtering and pagination"
)
def get_stored_research(
    project_id: str,
    provider: Optional[str] = Query(None, description="Filter by provider: arxiv, semantic_scholar, openalex"),
    year: Optional[int] = Query(None, description="Filter by publication year"),
    open_access: Optional[bool] = Query(None, description="Filter by open access availability"),
    search: Optional[str] = Query(None, description="Search keyword in title, abstract, or venue"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves previously stored research papers for a project.
    Supports filtering by provider, year, open access status, text search, and pagination.
    """
    _verify_project_ownership(db, project_id, current_user.id)

    # Sanitize direct function invocation parameter defaults (if called outside FastAPI runner)
    safe_provider = provider if isinstance(provider, str) else None
    safe_year = year if isinstance(year, int) else None
    safe_open_access = open_access if isinstance(open_access, bool) else None
    safe_search = search if isinstance(search, str) else None
    safe_page = page if isinstance(page, int) else 1
    safe_page_size = page_size if isinstance(page_size, int) else 20

    return research_discovery_service.get_stored_papers(
        db=db,
        project_id=project_id,
        provider=safe_provider,
        year=safe_year,
        open_access=safe_open_access,
        search_query=safe_search,
        page=safe_page,
        page_size=safe_page_size,
    )

@router.get(
    "/projects/{project_id}/research/stats",
    response_model=ResearchStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve summary discovery statistics for stored papers"
)
def get_research_stats(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns discovery statistics for the project, including provider distribution,
    open access paper count, and year breakdown.
    """
    _verify_project_ownership(db, project_id, current_user.id)

    return research_discovery_service.get_research_stats(db=db, project_id=project_id)
