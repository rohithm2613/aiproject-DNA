import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.project import Project
from app.models.patent import Patent
from app.models.project_embedding import ProjectEmbedding
from app.schemas.patent import PatentSchema
from app.services.embedding.embedding_service import EmbeddingService
from app.services.embedding.text_preprocessor import TextPreprocessor
from app.services.embedding.semantic_similarity_service import compute_cosine_similarity, get_similarity_label

logger = logging.getLogger("uvicorn.error")

class PatentEmbeddingService:
    """
    Handles dense vector embedding generation and cosine similarity calculation
    for Patent records against the project idea anchor vector.
    """

    def __init__(self, db: Session, model_name: Optional[str] = None):
        self.db = db
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.embedding_service = EmbeddingService.get_instance(self.model_name)

    def ensure_patent_embeddings(self, project_id: str, patents: List[Patent]) -> None:
        """
        Generates and stores embeddings for any patents that lack an up-to-date embedding record.
        """
        if not patents:
            return

        existing_embeddings = (
            self.db.query(ProjectEmbedding)
            .filter(
                ProjectEmbedding.project_id == project_id,
                ProjectEmbedding.source_type == "patent",
                ProjectEmbedding.model_name == self.model_name
            )
            .all()
        )
        existing_map = {e.source_record_id: e for e in existing_embeddings}

        to_embed: List[Tuple[Patent, Dict[str, Any]]] = []
        for p in patents:
            prep = TextPreprocessor.prepare_patent_text(p)
            existing = existing_map.get(p.id)
            if not existing or existing.content_hash != prep["content_hash"]:
                to_embed.append((p, prep))

        if not to_embed:
            return

        texts = [prep["text"] for _, prep in to_embed]
        try:
            vectors = self.embedding_service.encode_texts(texts)
            for (p, prep), vec in zip(to_embed, vectors):
                existing = existing_map.get(p.id)
                if existing:
                    existing.embedding = vec
                    existing.content_hash = prep["content_hash"]
                    existing.metadata_json = prep["metadata"]
                    existing.generated_at = func.now()
                else:
                    new_emb = ProjectEmbedding(
                        project_id=project_id,
                        user_id=p.user_id,
                        source_type="patent",
                        source_record_id=p.id,
                        embedding=vec,
                        model_name=self.model_name,
                        embedding_dimension=len(vec),
                        content_hash=prep["content_hash"],
                        metadata_json=prep["metadata"]
                    )
                    self.db.add(new_emb)
            self.db.commit()
            logger.info(f"Persisted {len(to_embed)} patent embeddings for project {project_id}")
        except Exception as exc:
            self.db.rollback()
            logger.error(f"Failed to generate patent embeddings: {exc}", exc_info=True)

    def get_patent_similarities(
        self,
        project_id: str,
        patents: List[Patent]
    ) -> Dict[str, Tuple[float, str]]:
        """
        Computes cosine similarities between project idea embedding and patents.
        Returns a map: {patent_id: (similarity_score, similarity_band)}
        """
        if not patents:
            return {}

        # 1. Fetch project vector
        project_emb = (
            self.db.query(ProjectEmbedding)
            .filter(
                ProjectEmbedding.project_id == project_id,
                ProjectEmbedding.source_type == "project",
                ProjectEmbedding.model_name == self.model_name
            )
            .first()
        )

        if not project_emb or not project_emb.embedding:
            # If project embedding doesn't exist yet, generate it
            proj = self.db.query(Project).filter(Project.id == project_id).first()
            if not proj:
                return {}
            prep = TextPreprocessor.prepare_project_text(proj)
            try:
                vec = self.embedding_service.encode_text(prep["text"])
                project_emb = ProjectEmbedding(
                    project_id=project_id,
                    user_id=proj.user_id,
                    source_type="project",
                    source_record_id=proj.id,
                    embedding=vec,
                    model_name=self.model_name,
                    embedding_dimension=len(vec),
                    content_hash=prep["content_hash"],
                    metadata_json=prep["metadata"]
                )
                self.db.add(project_emb)
                self.db.commit()
            except Exception as exc:
                self.db.rollback()
                logger.warning(f"Could not generate project embedding for similarity: {exc}")
                return {}

        proj_vec = project_emb.embedding

        # 2. Fetch patent embeddings
        patent_ids = [p.id for p in patents]
        embeddings = (
            self.db.query(ProjectEmbedding)
            .filter(
                ProjectEmbedding.project_id == project_id,
                ProjectEmbedding.source_type == "patent",
                ProjectEmbedding.source_record_id.in_(patent_ids),
                ProjectEmbedding.model_name == self.model_name
            )
            .all()
        )
        emb_map = {e.source_record_id: e.embedding for e in embeddings}

        results: Dict[str, Tuple[float, str]] = {}
        for p in patents:
            pat_vec = emb_map.get(p.id)
            if pat_vec:
                try:
                    score = compute_cosine_similarity(proj_vec, pat_vec)
                    # Round to 4 decimal places
                    clean_score = round(max(0.0, score), 4)
                    band = get_similarity_label(clean_score)
                    results[p.id] = (clean_score, band)
                except Exception as e:
                    logger.warning(f"Cosine similarity error for patent {p.id}: {e}")
                    results[p.id] = (0.0, "Low semantic similarity")
            else:
                results[p.id] = (0.0, "Low semantic similarity")

        return results

    def populate_schema_similarities(
        self,
        project_id: str,
        schemas: List[PatentSchema],
        patents: List[Patent]
    ) -> List[PatentSchema]:
        """Enriches PatentSchema items with computed similarity scores and bands."""
        sim_map = self.get_patent_similarities(project_id, patents)
        for schema in schemas:
            if schema.id in sim_map:
                score, band = sim_map[schema.id]
                schema.similarity_score = score
                schema.similarity_band = band
        return schemas

