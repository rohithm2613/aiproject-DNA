from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.github import (
    GitHubSearchRequest,
    GitHubSearchResponse,
    GitHubRepositoryListResponse,
    GitHubStatsResponse,
)
from app.services.project_service import ProjectService
from app.services.github.github_service import github_service

router = APIRouter(tags=["GitHub Repository Discovery"])

def _verify_project_ownership(db: Session, project_id: str, current_user_id: str):
    """Verifies that project exists and belongs strictly to the authenticated user."""
    project = ProjectService.get_project_by_id(db=db, project_id=project_id, user_id=current_user_id)
    if not project:
        if ProjectService.check_project_exists(db=db, project_id=project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to access GitHub repositories for this project."
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    return project

@router.post(
    "/projects/{project_id}/github/search",
    response_model=GitHubSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover existing GitHub repositories related to project idea"
)
async def search_github_repositories(
    project_id: str,
    payload: Optional[GitHubSearchRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes repository discovery across GitHub Search API using queries derived
    from the project title, problem statement, keywords, and technical domain.
    Deduplicates results and persists/updates records.
    """
    project = _verify_project_ownership(db, project_id, current_user.id)

    req = payload or GitHubSearchRequest()
    response = await github_service.search_and_persist(
        db=db,
        project=project,
        user_id=current_user.id,
        analysis_id=req.analysis_id,
        max_results=req.max_results,
        sort=req.sort or "stars",
        order=req.order or "desc",
    )
    return response

@router.get(
    "/projects/{project_id}/github",
    response_model=GitHubRepositoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve stored GitHub repositories with filtering and pagination"
)
def get_stored_repositories(
    project_id: str,
    language: Optional[str] = Query(None, description="Filter by programming language"),
    min_stars: Optional[int] = Query(None, description="Minimum star count"),
    topic: Optional[str] = Query(None, description="Filter by repository topic keyword"),
    archived: Optional[bool] = Query(None, description="Filter by archived status"),
    fork: Optional[bool] = Query(None, description="Filter by fork status"),
    search: Optional[str] = Query(None, description="Search keyword in repository name or description"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves previously stored GitHub repositories for a project.
    Supports filtering by language, minimum stars, topic, archived/fork flag, text search, and pagination.
    """
    _verify_project_ownership(db, project_id, current_user.id)

    # Sanitize direct function invocation parameter defaults (if called outside FastAPI runner)
    safe_language = language if isinstance(language, str) else None
    safe_min_stars = min_stars if isinstance(min_stars, int) else None
    safe_topic = topic if isinstance(topic, str) else None
    safe_archived = archived if isinstance(archived, bool) else None
    safe_fork = fork if isinstance(fork, bool) else None
    safe_search = search if isinstance(search, str) else None
    safe_page = page if isinstance(page, int) else 1
    safe_page_size = page_size if isinstance(page_size, int) else 20

    return github_service.get_stored_repositories(
        db=db,
        project_id=project_id,
        language=safe_language,
        min_stars=safe_min_stars,
        topic=safe_topic,
        archived=safe_archived,
        fork=safe_fork,
        search_text=safe_search,
        page=safe_page,
        page_size=safe_page_size,
    )

@router.get(
    "/projects/{project_id}/github/stats",
    response_model=GitHubStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve summary discovery statistics for stored GitHub repositories"
)
def get_repository_stats(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns discovery statistics for the project, including language distribution,
    total stars, total forks, and archived/fork counts.
    """
    _verify_project_ownership(db, project_id, current_user.id)

    return github_service.get_repository_stats(db=db, project_id=project_id)

