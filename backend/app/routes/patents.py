import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.project import Project
from app.core.deps import get_current_user
from app.schemas.patent import (
    PatentSchema,
    PatentSearchRequest,
    PatentSearchResponse,
    PatentListResponse,
    PatentStatsResponse,
    PatentAnalyzeRequest,
    PatentAnalysisResponse,
    PatentEvidenceManifestItem,
)
from app.services.patents.patent_discovery_service import PatentDiscoveryService
from app.services.patents.patent_analysis_service import PatentAnalysisService

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/projects/{project_id}/patents", tags=["Patent & Prior-Art Discovery Engine"])

def verify_project_ownership(project_id: str, current_user: User, db: Session) -> Project:
    """Verifies that the project exists and belongs to the authenticated user."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project"
        )
    return project

@router.post("/search", response_model=PatentSearchResponse)
async def search_patents(
    project_id: str,
    payload: Optional[PatentSearchRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Searches for patents and prior art across USPTO Open Data and EPO OPS,
    deduplicates against existing records, stores new patents in PostgreSQL,
    and computes dense semantic embeddings and similarity scores.
    """
    verify_project_ownership(project_id, current_user, db)
    req = payload or PatentSearchRequest()
    service = PatentDiscoveryService()

    try:
        response = await service.search_and_persist_patents(
            db=db,
            project_id=project_id,
            user_id=current_user.id,
            analysis_id=req.analysis_id,
            max_results=req.max_results,
            providers=req.providers,
            jurisdictions=req.jurisdictions,
            query_override=req.query_override,
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as exc:
        logger.error(f"Error during patent search for project {project_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Patent search failed: {str(exc)}"
        )

@router.get("", response_model=PatentListResponse)
def get_patents(
    project_id: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    jurisdiction: Optional[str] = Query(default=None, description="Jurisdiction filter (e.g. US, EP, WO)"),
    provider: Optional[str] = Query(default=None, description="Provider filter (uspto, epo)"),
    search_query: Optional[str] = Query(default=None, description="Keyword search filter"),
    sort_by: str = Query(default="similarity", description="Sorting field: similarity, publication_date, created_at"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves paginated and filtered patents discovered for the specified project,
    enriched with cosine similarity scores and semantic similarity bands.
    """
    verify_project_ownership(project_id, current_user, db)
    service = PatentDiscoveryService()
    return service.get_patents(
        db=db,
        project_id=project_id,
        page=page,
        page_size=page_size,
        jurisdiction=jurisdiction,
        provider=provider,
        search_query=search_query,
        sort_by=sort_by,
    )

@router.get("/stats", response_model=PatentStatsResponse)
def get_patent_stats(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves aggregated statistical metrics across discovered patents,
    including provider breakdown, jurisdiction distribution, top CPC classifications,
    top assignees, and semantic similarity counts.
    """
    verify_project_ownership(project_id, current_user, db)
    service = PatentDiscoveryService()
    return service.get_patent_stats(db=db, project_id=project_id)

@router.get("/evidence", response_model=List[PatentEvidenceManifestItem])
def get_patent_evidence(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves deterministic patent evidence items (EVID-PAT-01..N) formatted
    for the Phase 4.5 Evidence Explorer modal.
    """
    verify_project_ownership(project_id, current_user, db)
    service = PatentDiscoveryService()
    return service.get_patent_evidence_manifest(db=db, project_id=project_id)

@router.post("/analyze", response_model=PatentAnalysisResponse)
def analyze_patents(
    project_id: str,
    payload: Optional[PatentAnalyzeRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes in-depth prior-art deep analysis for discovered patents against
    the user's project idea, extracting problems, solutions, similarities,
    differences, claims overlap, and technical differentiation opportunities.
    """
    verify_project_ownership(project_id, current_user, db)
    req = payload or PatentAnalyzeRequest()
    service = PatentAnalysisService(db)
    try:
        return service.analyze_prior_art(
            project_id=project_id,
            user_id=current_user.id,
            patent_ids=req.patent_ids,
            max_patents=req.max_patents,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as exc:
        logger.error(f"Error during prior-art analysis for project {project_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prior-art analysis failed: {str(exc)}"
        )

@router.get("/analysis", response_model=PatentAnalysisResponse)
def get_patent_analysis(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the prior-art deep analysis for the project's discovered patents.
    """
    verify_project_ownership(project_id, current_user, db)
    service = PatentAnalysisService(db)
    try:
        return service.analyze_prior_art(
            project_id=project_id,
            user_id=current_user.id,
            max_patents=10,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.get("/{patent_id}", response_model=PatentSchema)
def get_patent_by_id(
    project_id: str,
    patent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves complete details of a single discovered patent publication.
    """
    verify_project_ownership(project_id, current_user, db)
    service = PatentDiscoveryService()
    patent = service.get_patent_by_id(db=db, project_id=project_id, patent_id=patent_id)
    if not patent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patent not found")
    return patent

