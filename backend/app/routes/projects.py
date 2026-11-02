from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=ProjectListResponse)
def list_projects(
    search: Optional[str] = Query(None, description="Search term for title or description"),
    domain: Optional[str] = Query(None, description="Filter by domain category"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve list of projects owned by the currently authenticated user.
    Supports search, domain/status filtering, and pagination.
    """
    skip = (page - 1) * limit
    projects, total = ProjectService.get_projects(
        db=db,
        user_id=current_user.id,
        search=search,
        domain=domain,
        status=status,
        skip=skip,
        limit=limit
    )
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        limit=limit
    )

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project associated with the authenticated user."""
    new_project = ProjectService.create_project(
        db=db,
        project_in=project_in,
        user_id=current_user.id
    )
    return ProjectResponse.model_validate(new_project)

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch a project by ID, verifying that the project belongs to the authenticated user.
    Returns 403 Forbidden if the project belongs to another user, or 404 if it does not exist.
    """
    project = ProjectService.get_project_by_id(db=db, project_id=project_id, user_id=current_user.id)
    if not project:
        # Check if project exists under another user to distinguish 403 from 404
        if ProjectService.check_project_exists(db=db, project_id=project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to view or manage this project."
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    return ProjectResponse.model_validate(project)

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing project owned by the authenticated user."""
    if not ProjectService.get_project_by_id(db=db, project_id=project_id, user_id=current_user.id):
        if ProjectService.check_project_exists(db=db, project_id=project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to modify this project."
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    updated = ProjectService.update_project(
        db=db,
        project_id=project_id,
        project_in=project_in,
        user_id=current_user.id
    )
    return ProjectResponse.model_validate(updated)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project owned by the authenticated user."""
    if not ProjectService.get_project_by_id(db=db, project_id=project_id, user_id=current_user.id):
        if ProjectService.check_project_exists(db=db, project_id=project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to delete this project."
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    ProjectService.delete_project(db=db, project_id=project_id, user_id=current_user.id)
    return None
