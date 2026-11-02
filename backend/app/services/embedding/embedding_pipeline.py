import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.core.config import settings
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.research_paper import ResearchPaper
from app.models.github_repo import GitHubRepository
from app.models.repository_analysis import RepositoryAnalysis
from app.models.patent import Patent
from app.models.project_embedding import ProjectEmbedding
from app.schemas.embedding import EmbeddingGenerateResponse
from app.services.embedding.text_preprocessor import TextPreprocessor
from app.services.embedding.embedding_service import EmbeddingService, EmbeddingModelError

logger = logging.getLogger("uvicorn.error")

class EmbeddingPipeline:
    """
    Orchestrates batch dense embedding generation and lifecycle management
    for project ideas, academic research papers, and GitHub repositories.
    """

    def __init__(self, db: Session, model_name: Optional[str] = None):
        self.db = db
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.embedding_service = EmbeddingService.get_instance(self.model_name)

    def generate_all_project_embeddings(
        self,
        project: Project,
        force_regenerate: bool = False,
        include_papers: bool = True,
        include_repos: bool = True,
        include_patents: bool = True,
    ) -> EmbeddingGenerateResponse:
        """
        Executes end-to-end embedding pipeline for a project and its discovered sources.
        """
        total_generated = 0
        total_skipped = 0
        total_failed = 0
        counts_by_source: Dict[str, int] = {
            "project": 0,
            "research_paper": 0,
            "github_repository": 0,
            "patent": 0,
        }
        errors: Dict[str, str] = {}

        # 1. Fetch Candidates & Prepare Text
        prepared_items: List[Tuple[str, str, Dict[str, Any]]] = []
        # Tuples of (source_type, source_record_id, prepared_dict)

        # 1A. Project Idea
        latest_analysis = (
            self.db.query(ProjectAnalysis)
            .filter(ProjectAnalysis.project_id == project.id)
            .order_by(ProjectAnalysis.version.desc())
            .first()
        )
        try:
            proj_prep = TextPreprocessor.prepare_project_text(project, latest_analysis)
            prepared_items.append(("project", project.id, proj_prep))
        except Exception as e:
            logger.error(f"Failed to prepare project text for project {project.id}: {e}")
            errors[f"project:{project.id}"] = str(e)
            total_failed += 1

        # 1B. Academic Research Papers
        if include_papers:
            papers = self.db.query(ResearchPaper).filter(ResearchPaper.project_id == project.id).all()
            for p in papers:
                try:
                    p_prep = TextPreprocessor.prepare_paper_text(p)
                    prepared_items.append(("research_paper", p.id, p_prep))
                except Exception as e:
                    logger.error(f"Failed to prepare paper text for {p.id}: {e}")
                    errors[f"research_paper:{p.id}"] = str(e)
                    total_failed += 1

        # 1C. GitHub Repositories (incorporating Phase 4.3 Deep Analysis if present)
        if include_repos:
            repos = self.db.query(GitHubRepository).filter(GitHubRepository.project_id == project.id).all()
            # Prefetch analyses
            analyses = (
                self.db.query(RepositoryAnalysis)
                .filter(RepositoryAnalysis.project_id == project.id)
                .all()
            )
            analysis_by_repo_id = {a.github_repo_id: a for a in analyses}

            for r in repos:
                try:
                    repo_analysis = analysis_by_repo_id.get(r.id)
                    r_prep = TextPreprocessor.prepare_repo_text(r, repo_analysis)
                    prepared_items.append(("github_repository", r.id, r_prep))
                except Exception as e:
                    logger.error(f"Failed to prepare repo text for {r.id}: {e}")
                    errors[f"github_repository:{r.id}"] = str(e)
                    total_failed += 1

        # 1D. Patents (Phase 4.6)
        if include_patents:
            patents = self.db.query(Patent).filter(Patent.project_id == project.id).all()
            for pat in patents:
                try:
                    pat_prep = TextPreprocessor.prepare_patent_text(pat)
                    prepared_items.append(("patent", pat.id, pat_prep))
                except Exception as e:
                    logger.error(f"Failed to prepare patent text for {pat.id}: {e}")
                    errors[f"patent:{pat.id}"] = str(e)
                    total_failed += 1

        # 2. Check Existing Embeddings for Content Hash Matches (Avoid Duplicate Work)
        existing_records = (
            self.db.query(ProjectEmbedding)
            .filter(
                ProjectEmbedding.project_id == project.id,
                ProjectEmbedding.model_name == self.model_name,
            )
            .all()
        )
        existing_map: Dict[Tuple[str, str], ProjectEmbedding] = {
            (e.source_type, e.source_record_id): e for e in existing_records
        }

        items_to_embed: List[Tuple[str, str, Dict[str, Any]]] = []

        for stype, srec_id, prep in prepared_items:
            existing = existing_map.get((stype, srec_id))
            if existing and not force_regenerate and existing.content_hash == prep["content_hash"]:
                # Content has not changed and same model: Skip
                total_skipped += 1
                counts_by_source[stype] = counts_by_source.get(stype, 0) + 1
            else:
                items_to_embed.append((stype, srec_id, prep))

        # 3. Batch Encode Unembedded or Changed Items
        if items_to_embed:
            texts_to_encode = [prep["text"] for _, _, prep in items_to_embed]
            try:
                vectors = self.embedding_service.encode_texts(texts_to_encode)
            except EmbeddingModelError as eme:
                logger.error(f"Batch embedding generation failed: {eme}")
                for stype, srec_id, _ in items_to_embed:
                    errors[f"{stype}:{srec_id}"] = str(eme)
                    total_failed += 1
                vectors = []

            # 4. Upsert Generated Vectors
            for (stype, srec_id, prep), vec in zip(items_to_embed, vectors):
                try:
                    existing = existing_map.get((stype, srec_id))
                    if existing:
                        # Update in-place
                        existing.embedding = vec
                        existing.content_hash = prep["content_hash"]
                        existing.metadata_json = prep["metadata"]
                        existing.generated_at = func.now()
                    else:
                        new_record = ProjectEmbedding(
                            project_id=project.id,
                            user_id=project.user_id,
                            source_type=stype,
                            source_record_id=srec_id,
                            embedding=vec,
                            model_name=self.model_name,
                            embedding_dimension=len(vec),
                            content_hash=prep["content_hash"],
                            metadata_json=prep["metadata"],
                        )
                        self.db.add(new_record)

                    total_generated += 1
                    counts_by_source[stype] = counts_by_source.get(stype, 0) + 1
                except Exception as save_err:
                    logger.error(f"Failed to persist embedding for {stype}:{srec_id}: {save_err}")
                    errors[f"{stype}:{srec_id}"] = str(save_err)
                    total_failed += 1

            # Commit batch changes
            try:
                self.db.commit()
            except Exception as commit_err:
                self.db.rollback()
                logger.error(f"Database commit failed during embedding persistence: {commit_err}")
                errors["db_commit"] = str(commit_err)

        # 5. Determine Overall Pipeline Status
        status = "completed"
        if errors and total_generated > 0:
            status = "partial_success"
        elif errors and total_generated == 0:
            status = "failed"

        return EmbeddingGenerateResponse(
            status=status,
            project_id=project.id,
            model_name=self.model_name,
            embedding_dimension=self.dimension,
            total_generated=total_generated,
            total_skipped=total_skipped,
            total_failed=total_failed,
            counts_by_source=counts_by_source,
            errors=errors,
            generated_at=datetime.utcnow(),
        )

