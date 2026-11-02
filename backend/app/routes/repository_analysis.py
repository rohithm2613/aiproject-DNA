import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.github_repo import GitHubRepository
from app.models.repository_analysis import RepositoryAnalysis
from app.models.innovation_gap import InnovationGap
from app.schemas.repository_analysis import (
    RepositoryAnalysisRequest,
    RepositoryAnalysisBatchResponse,
    RepositoryAnalysisListResponse,
    RepositoryAnalysisSchema,
    InnovationGapListResponse,
    InnovationGapResponse,
    RepositoryAnalysisStatsResponse,
    TechnologyStackResponse,
    ExtractedFeatureResponse,
    ArchitectureAnalysisResponse,
    SimilarityAnalysisResponse,
)
from app.services.github.repository_analyzer import RepositoryAnalyzer
from app.services.github.innovation_gap_service import InnovationGapService

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/projects/{project_id}/github", tags=["GitHub Deep Analysis & Innovation Gaps"])

def _get_validated_project(project_id: str, current_user: User, db: Session) -> Project:
    """Helper to enforce multi-tenant project ownership."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not have permission to access repository analysis for this project."
        )
    return project

def _map_model_to_schema(model: RepositoryAnalysis) -> RepositoryAnalysisSchema:
    """Converts a database RepositoryAnalysis model to a validated Pydantic schema."""
    return RepositoryAnalysisSchema(
        id=model.id,
        project_id=model.project_id,
        github_repo_id=model.github_repo_id,
        user_id=model.user_id,
        repo_full_name=model.repo_full_name,
        readme_present=model.readme_present,
        readme_url=model.readme_url,
        readme_size=model.readme_size,
        summary=model.summary,
        problem_statement=model.problem_statement,
        detected_technologies=TechnologyStackResponse(**(model.detected_technologies or {})),
        architecture=ArchitectureAnalysisResponse(**(model.architecture or {})),
        features=[ExtractedFeatureResponse(**f) for f in (model.features or [])],
        similarity=SimilarityAnalysisResponse(**(model.similarity or {})) if model.similarity else None,
        analysis_status=model.analysis_status,
        analysis_mode=model.analysis_mode,
        error_message=model.error_message,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

@router.post("/analyze", response_model=RepositoryAnalysisBatchResponse)
async def analyze_repositories(
    project_id: str,
    payload: RepositoryAnalysisRequest = RepositoryAnalysisRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Triggers in-depth technical analysis across discovered GitHub repositories for the project,
    evaluating READMEs, architecture, technology stacks, similarity, and innovation gaps.
    """
    project = _get_validated_project(project_id, current_user, db)

    # Fetch latest Phase 3 analysis for richer project grounding
    analysis = (
        db.query(ProjectAnalysis)
        .filter(ProjectAnalysis.project_id == project_id)
        .order_by(desc(ProjectAnalysis.version))
        .first()
    )

    # Fetch discovered GitHub repositories from Phase 4.2
    discovered_repos = (
        db.query(GitHubRepository)
        .filter(GitHubRepository.project_id == project_id)
        .order_by(desc(GitHubRepository.stargazers_count))
        .limit(payload.max_repositories)
        .all()
    )

    if not discovered_repos:
        return RepositoryAnalysisBatchResponse(
            status="completed",
            project_id=project_id,
            total_discovered_repositories=0,
            total_analyzed=0,
            analyzed_repositories=[],
            innovation_gaps=[],
            errors={},
            analysis_mode="none",
        )

    analyzer = RepositoryAnalyzer()
    gap_service = InnovationGapService()

    analyzed_results = []
    errors = {}
    analysis_modes = []

    for repo in discovered_repos:
        try:
            res = await analyzer.analyze_single_repository(
                project=project,
                analysis=analysis,
                repo=repo,
                user_id=current_user.id,
                db=db,
                force_refresh=payload.force_refresh,
            )
            analyzed_results.append(res)
            analysis_modes.append(res.analysis_mode)
        except Exception as exc:
            logger.error(f"Error analyzing repository {repo.full_name}: {exc}")
            errors[repo.full_name] = str(exc)

    # Detect and persist innovation gaps
    gaps: list = []
    if analyzed_results:
        try:
            gaps = await gap_service.detect_and_persist_gaps(
                project=project,
                analysis=analysis,
                analyzed_repos=analyzed_results,
                user_id=current_user.id,
                db=db,
            )
        except Exception as exc:
            logger.error(f"Error detecting innovation gaps: {exc}")
            errors["innovation_gap_detection"] = str(exc)

    # Determine composite batch status
    if not analyzed_results:
        batch_status = "failed"
    elif errors:
        batch_status = "partial_success"
    else:
        batch_status = "completed"

    overall_mode = "ai_enhanced" if any(m == "ai_enhanced" for m in analysis_modes) else "deterministic_fallback"

    return RepositoryAnalysisBatchResponse(
        status=batch_status,
        project_id=project_id,
        total_discovered_repositories=len(discovered_repos),
        total_analyzed=len(analyzed_results),
        analyzed_repositories=analyzed_results,
        innovation_gaps=gaps,
        errors=errors,
        analysis_mode=overall_mode,
    )

@router.get("/analysis", response_model=RepositoryAnalysisListResponse)
def get_stored_repository_analyses(
    project_id: str,
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves stored repository analysis records with pagination.
    """
    _get_validated_project(project_id, current_user, db)

    query = db.query(RepositoryAnalysis).filter(RepositoryAnalysis.project_id == project_id)
    total = query.count()
    records = query.order_by(desc(RepositoryAnalysis.updated_at)).offset((page - 1) * page_size).limit(page_size).all()

    items = [_map_model_to_schema(r) for r in records]

    return RepositoryAnalysisListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )

@router.get("/analysis/stats", response_model=RepositoryAnalysisStatsResponse)
def get_analysis_stats(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Aggregated deep analysis metrics: total analyzed, average similarity,
    technology distributions, total features extracted, and innovation gap metrics.
    """
    _get_validated_project(project_id, current_user, db)

    analyses = db.query(RepositoryAnalysis).filter(RepositoryAnalysis.project_id == project_id).all()
    gaps = db.query(InnovationGap).filter(InnovationGap.project_id == project_id).all()

    total_analyzed = len(analyses)
    total_similarity = 0.0
    total_features = 0
    tech_dist: dict = {}

    for a in analyses:
        sim = a.similarity or {}
        overall = sim.get("overall_score", 0.0)
        total_similarity += float(overall)

        feats = a.features or []
        total_features += len(feats)

        techs = a.detected_technologies or {}
        for cat_list in techs.values():
            if isinstance(cat_list, list):
                for tech in cat_list:
                    tech_dist[tech] = tech_dist.get(tech, 0) + 1

    avg_similarity = round(total_similarity / total_analyzed, 1) if total_analyzed > 0 else 0.0

    gaps_by_priority: dict = {}
    gaps_by_category: dict = {}
    for g in gaps:
        p = (g.priority or "medium").lower()
        gaps_by_priority[p] = gaps_by_priority.get(p, 0) + 1

        c = (g.category or "other").lower()
        gaps_by_category[c] = gaps_by_category.get(c, 0) + 1

    return RepositoryAnalysisStatsResponse(
        project_id=project_id,
        total_analyzed_repositories=total_analyzed,
        average_similarity_score=avg_similarity,
        technology_distribution=tech_dist,
        total_features_extracted=total_features,
        innovation_gaps_count=len(gaps),
        gaps_by_priority=gaps_by_priority,
        gaps_by_category=gaps_by_category,
    )

@router.get("/analysis/{analysis_id}", response_model=RepositoryAnalysisSchema)
def get_single_repository_analysis(
    project_id: str,
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves detailed deep analysis for a specific repository analysis ID.
    """
    _get_validated_project(project_id, current_user, db)

    record = db.query(RepositoryAnalysis).filter(
        RepositoryAnalysis.id == analysis_id,
        RepositoryAnalysis.project_id == project_id,
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository analysis with ID '{analysis_id}' not found for this project."
        )

    return _map_model_to_schema(record)

@router.get("/innovation-gaps", response_model=InnovationGapListResponse)
def get_innovation_gaps(
    project_id: str,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves persisted innovation gaps with optional priority or category filters.
    """
    _get_validated_project(project_id, current_user, db)

    query = db.query(InnovationGap).filter(InnovationGap.project_id == project_id)

    if priority and isinstance(priority, str):
        query = query.filter(func.lower(InnovationGap.priority) == priority.lower())
    if category and isinstance(category, str):
        query = query.filter(func.lower(InnovationGap.category) == category.lower())

    records = query.order_by(desc(InnovationGap.created_at)).all()

    items = [
        InnovationGapResponse(
            id=g.id,
            project_id=g.project_id,
            user_id=g.user_id,
            gap_title=g.gap_title,
            category=g.category,
            description=g.description,
            why_it_matters=g.why_it_matters,
            suggested_implementation=g.suggested_implementation,
            priority=g.priority,
            confidence_level=g.confidence_level,
            supporting_evidence=g.supporting_evidence or [],
            created_at=g.created_at,
            updated_at=g.updated_at,
        )
        for g in records
    ]

    return InnovationGapListResponse(
        total=len(items),
        items=items,
    )

