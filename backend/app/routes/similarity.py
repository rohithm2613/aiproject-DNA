import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.user import User
from app.models.project import Project
from app.models.project_embedding import ProjectEmbedding
from app.schemas.embedding import (
    EmbeddingGenerateRequest,
    EmbeddingGenerateResponse,
    CrossSourceSimilarityResponse,
    SimilarityStatsResponse,
)
from app.services.embedding.embedding_pipeline import EmbeddingPipeline
from app.services.embedding.semantic_similarity_service import SemanticSimilarityService
from app.core.config import settings
from app.core.deps import get_current_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/projects/{project_id}", tags=["Semantic Similarity & Embeddings"])

def _get_validated_project(project_id: str, current_user: User, db: Session) -> Project:
    """Verifies that the requested project exists and belongs to the authenticated user."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not have permission to access embeddings or similarity for this project."
        )
    return project

@router.post("/embeddings/generate", response_model=EmbeddingGenerateResponse)
def generate_project_embeddings(
    project_id: str,
    payload: Optional[EmbeddingGenerateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates normalized dense vector embeddings for the project idea,
    its stored research papers, and its discovered GitHub repositories.
    """
    project = _get_validated_project(project_id, current_user, db)

    force_regenerate = payload.force_regenerate if payload else False
    include_papers = payload.include_papers if payload else True
    include_repos = payload.include_repos if payload else True

    pipeline = EmbeddingPipeline(db=db)
    result = pipeline.generate_all_project_embeddings(
        project=project,
        force_regenerate=force_regenerate,
        include_papers=include_papers,
        include_repos=include_repos,
    )

    return result

@router.get("/similarity", response_model=CrossSourceSimilarityResponse)
def get_semantic_similarities(
    project_id: str,
    source_type: Optional[str] = Query(default=None, description="research_paper | github_repository | None for all"),
    min_similarity: Optional[float] = Query(default=None, description="Minimum cosine similarity threshold (e.g. 0.5)"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of ranked results to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Computes and ranks cross-source semantic similarity between the user's project
    idea and stored academic research papers and GitHub repositories.
    """
    _get_validated_project(project_id, current_user, db)

    # 1. Fetch project's own idea embedding
    proj_embedding = (
        db.query(ProjectEmbedding)
        .filter(
            ProjectEmbedding.project_id == project_id,
            ProjectEmbedding.source_type == "project",
        )
        .first()
    )

    if not proj_embedding:
        return CrossSourceSimilarityResponse(
            project_id=project_id,
            model_name=settings.EMBEDDING_MODEL_NAME,
            embedding_dimension=settings.EMBEDDING_DIMENSION,
            total_matches=0,
            matches=[],
            disclaimer=(
                "No project idea embedding found. Please trigger embedding generation first "
                "via POST /api/projects/{id}/embeddings/generate."
            ),
        )

    # 2. Fetch candidate source embeddings
    candidates = (
        db.query(ProjectEmbedding)
        .filter(
            ProjectEmbedding.project_id == project_id,
            ProjectEmbedding.source_type != "project",
            ProjectEmbedding.model_name == proj_embedding.model_name,
        )
        .all()
    )

    # 3. Compute and rank similarities
    response = SemanticSimilarityService.rank_similarities(
        project_id=project_id,
        project_embedding_record=proj_embedding,
        candidate_embeddings=candidates,
        source_type_filter=source_type,
        min_similarity=min_similarity,
        limit=limit,
    )

    return response

@router.get("/similarity/stats", response_model=SimilarityStatsResponse)
def get_similarity_stats(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves statistics on stored embeddings, source breakdown, model configuration,
    and available similarity candidates.
    """
    _get_validated_project(project_id, current_user, db)

    embeddings = (
        db.query(ProjectEmbedding)
        .filter(ProjectEmbedding.project_id == project_id)
        .all()
    )

    total_count = len(embeddings)
    by_source: dict = {}
    latest_ts = None
    has_proj = False

    for e in embeddings:
        by_source[e.source_type] = by_source.get(e.source_type, 0) + 1
        if e.source_type == "project":
            has_proj = True
        if e.generated_at:
            if latest_ts is None or e.generated_at > latest_ts:
                latest_ts = e.generated_at

    candidate_count = sum(count for stype, count in by_source.items() if stype != "project")

    return SimilarityStatsResponse(
        project_id=project_id,
        model_name=settings.EMBEDDING_MODEL_NAME,
        embedding_dimension=settings.EMBEDDING_DIMENSION,
        total_embeddings_stored=total_count,
        embeddings_by_source_type=by_source,
        latest_generation_timestamp=latest_ts,
        total_matches_available=candidate_count,
        has_project_embedding=has_proj,
    )
