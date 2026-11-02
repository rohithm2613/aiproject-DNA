from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.analysis import (
    ProjectAnalysisResponse,
    ProjectAnalysisListResponse,
    DashboardAnalyticsResponse,
)
from app.services.project_service import ProjectService
from app.services.project_analysis_service import ProjectAnalysisService
from app.services.ai_service import AIService

router = APIRouter(tags=["AI Idea Analysis"])

@router.get(
    "/analysis/diagnostics"
)
def get_ai_diagnostics(
    current_user: User = Depends(get_current_user)
):
    """
    Safe diagnostic endpoint reporting Gemini API configuration status.
    Protected by user authentication. Never exposes actual secret keys.
    """
    return AIService.get_diagnostics()

@router.post(
    "/projects/{project_id}/analyze",
    response_model=ProjectAnalysisResponse,
    status_code=status.HTTP_201_CREATED
)
def trigger_project_analysis(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits the project concept to Google Gemini API to generate structured technical analysis,
    persisting a new analysis version in the database.
    """
    project = ProjectService.get_project_by_id(db=db, project_id=project_id, user_id=current_user.id)
    if not project:
        if ProjectService.check_project_exists(db=db, project_id=project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to analyze this project."
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    analysis_record = ProjectAnalysisService.analyze_project(
        db=db,
        project=project,
        user=current_user
    )
    return ProjectAnalysisResponse.model_validate(analysis_record)

@router.get(
    "/projects/{project_id}/analysis",
    response_model=ProjectAnalysisResponse
)
def get_project_analysis(
    project_id: str,
    version: Optional[int] = Query(None, description="Specific analysis version number (defaults to latest)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the latest (or specified version) structured AI analysis for a project.
    """
    project = ProjectService.get_project_by_id(db=db, project_id=project_id, user_id=current_user.id)
    if not project:
        if ProjectService.check_project_exists(db=db, project_id=project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to view analysis for this project."
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    analysis = ProjectAnalysisService.get_analysis_for_project(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        version=version if isinstance(version, int) else None
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AI analysis found for project '{project.title}'" + (f" (version {version})" if version else "") + ". Please initiate an analysis run."
        )

    return ProjectAnalysisResponse.model_validate(analysis)

@router.get(
    "/projects/{project_id}/analyses",
    response_model=ProjectAnalysisListResponse
)
def get_project_analysis_history(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves complete historical versions of all AI analyses conducted on this project.
    """
    project = ProjectService.get_project_by_id(db=db, project_id=project_id, user_id=current_user.id)
    if not project:
        if ProjectService.check_project_exists(db=db, project_id=project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to view analysis history for this project."
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    analyses = ProjectAnalysisService.get_all_analyses_for_project(
        db=db,
        project_id=project_id,
        user_id=current_user.id
    )

    return ProjectAnalysisListResponse(
        project_id=project_id,
        total_versions=len(analyses),
        analyses=[ProjectAnalysisResponse.model_validate(a) for a in analyses]
    )

@router.get(
    "/analyses/dashboard/stats",
    response_model=DashboardAnalyticsResponse
)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns live personalized metrics for the dashboard (total projects, ideas analyzed, pending, recent runs).
    """
    return ProjectAnalysisService.get_dashboard_analytics(db=db, user_id=current_user.id)

@router.get(
    "/analyses/{analysis_id}",
    response_model=ProjectAnalysisResponse
)
def get_analysis_by_id(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch a single analysis record by its primary key ID.
    """
    analysis = ProjectAnalysisService.get_analysis_by_id(
        db=db,
        analysis_id=analysis_id,
        user_id=current_user.id
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' not found."
        )
    return ProjectAnalysisResponse.model_validate(analysis)

