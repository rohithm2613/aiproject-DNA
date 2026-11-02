import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.validation import (
    ValidationGenerateRequest,
    ValidationReportResponse,
    ValidationHistoryResponse,
    EvidenceManifestResponse,
)
from app.services.rag.rag_service import RAGService
from app.core.deps import get_current_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/projects/{project_id}", tags=["RAG Research Gap Validation"])

@router.post("/validation/generate", response_model=ValidationReportResponse)
def generate_validation_report(
    project_id: str,
    payload: Optional[ValidationGenerateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Triggers RAG-based Research Gap Validation comparing the project idea against
    retrieved academic papers, GitHub repositories, and repository analyses.
    Generates a structured, evidence-backed 10-section report.
    """
    request_data = payload or ValidationGenerateRequest()
    service = RAGService(db)
    return service.generate_validation_report(
        project_id=project_id,
        user_id=current_user.id,
        request=request_data,
    )

@router.get("/validation", response_model=ValidationReportResponse)
def get_latest_validation_report(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the latest generated RAG validation report for the specified project.
    """
    service = RAGService(db)
    return service.get_latest_report(
        project_id=project_id,
        user_id=current_user.id,
    )

@router.get("/validation/history", response_model=ValidationHistoryResponse)
def get_validation_report_history(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves version history and summary metrics for all validation reports
    generated for this project.
    """
    service = RAGService(db)
    return service.get_report_history(
        project_id=project_id,
        user_id=current_user.id,
    )

@router.get("/validation/evidence", response_model=EvidenceManifestResponse)
def get_validation_evidence_manifest(
    project_id: str,
    report_id: Optional[str] = Query(None, description="Optional specific report ID; defaults to latest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the normalized, traceable evidence manifest cited in the validation report.
    """
    service = RAGService(db)
    return service.get_evidence_manifest(
        project_id=project_id,
        user_id=current_user.id,
        report_id=report_id,
    )

@router.get("/validation/{report_id}", response_model=ValidationReportResponse)
def get_validation_report_by_id(
    project_id: str,
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a specific historical validation report by ID.
    """
    service = RAGService(db)
    return service.get_report_by_id(
        project_id=project_id,
        report_id=report_id,
        user_id=current_user.id,
    )

