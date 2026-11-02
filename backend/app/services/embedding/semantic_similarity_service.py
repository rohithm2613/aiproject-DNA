import math
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.project_embedding import ProjectEmbedding
from app.schemas.embedding import SemanticMatchItem, CrossSourceSimilarityResponse

logger = logging.getLogger("uvicorn.error")

def dot_product(v1: List[float], v2: List[float]) -> float:
    """Computes the dot product of two numerical vectors."""
    if len(v1) != len(v2):
        raise ValueError(f"Vector dimension mismatch: {len(v1)} vs {len(v2)}")
    return sum(a * b for a, b in zip(v1, v2))

def compute_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Computes cosine similarity between two vectors.
    Assumes vectors are L2-normalized; if not, computes standard cosine formula.
    """
    if not v1 or not v2:
        return 0.0
    if len(v1) != len(v2):
        raise ValueError(f"Vector dimension mismatch: {len(v1)} vs {len(v2)}")

    dot = dot_product(v1, v2)
    norm1 = math.sqrt(sum(x * x for x in v1))
    norm2 = math.sqrt(sum(y * y for y in v2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    score = dot / (norm1 * norm2)
    # Clip numerical floating-point inaccuracies
    return max(-1.0, min(1.0, float(score)))

def get_similarity_label(score: float) -> str:
    """Maps continuous cosine similarity score to standardized category label."""
    if score >= settings.SIMILARITY_HIGH_THRESHOLD:
        return "High semantic similarity"
    if score >= settings.SIMILARITY_MODERATE_THRESHOLD:
        return "Moderate semantic similarity"
    return "Low semantic similarity"

def extract_overlapping_aspects(project_meta: Dict[str, Any], match_meta: Dict[str, Any]) -> List[str]:
    """Identifies overlapping conceptual tokens and keywords between project and source."""
    p_text = f"{project_meta.get('title', '')} {project_meta.get('domain', '')} {project_meta.get('preview', '')}".lower()
    m_text = f"{match_meta.get('title', '')} {match_meta.get('preview', '')}".lower()

    stopwords = {
        "and", "the", "for", "with", "this", "that", "from", "using", "into", "over", "system",
        "project", "based", "approach", "novel", "framework", "real", "time", "high", "data"
    }

    import re
    p_words = set(w for w in re.findall(r'[a-zA-Z0-9_\-\+]{3,}', p_text) if w not in stopwords)
    m_words = set(w for w in re.findall(r'[a-zA-Z0-9_\-\+]{3,}', m_text) if w not in stopwords)

    shared = sorted(list(p_words.intersection(m_words)), key=lambda w: len(w), reverse=True)
    return [w.capitalize() for w in shared[:6]]

class SemanticSimilarityService:
    """
    Evaluates and ranks semantic proximity between a project idea's vector embedding
    and all discovered academic research papers and GitHub repositories.
    """

    @classmethod
    def rank_similarities(
        cls,
        project_id: str,
        project_embedding_record: ProjectEmbedding,
        candidate_embeddings: List[ProjectEmbedding],
        source_type_filter: Optional[str] = None,
        min_similarity: Optional[float] = None,
        limit: int = 50,
    ) -> CrossSourceSimilarityResponse:
        """
        Ranks candidates by cosine similarity against project embedding.
        """
        proj_vector = project_embedding_record.embedding
        if not proj_vector:
            return CrossSourceSimilarityResponse(
                project_id=project_id,
                model_name=project_embedding_record.model_name,
                embedding_dimension=project_embedding_record.embedding_dimension,
                total_matches=0,
                matches=[],
            )

        items: List[SemanticMatchItem] = []

        for candidate in candidate_embeddings:
            # Skip project's own self-embedding
            if candidate.source_type == "project" and candidate.source_record_id == project_id:
                continue

            if source_type_filter and source_type_filter != "all":
                if candidate.source_type != source_type_filter:
                    continue

            cand_vector = candidate.embedding
            if not cand_vector:
                continue

            score = compute_cosine_similarity(proj_vector, cand_vector)
            # Map score to positive 0-1 scale for UI readability
            pct = round(max(0.0, score) * 100.0, 1)

            if min_similarity is not None and score < min_similarity:
                continue

            meta = candidate.metadata_json or {}
            label = get_similarity_label(score)
            matched_aspects = extract_overlapping_aspects(
                project_embedding_record.metadata_json or {},
                meta,
            )

            items.append(
                SemanticMatchItem(
                    source_type=candidate.source_type,
                    source_record_id=candidate.source_record_id,
                    title=meta.get("title") or f"Record {candidate.source_record_id}",
                    url=meta.get("url"),
                    similarity_score=round(score, 4),
                    similarity_percentage=pct,
                    similarity_label=label,
                    matching_content_summary=meta.get("preview") or "No preview content available.",
                    matched_aspects=matched_aspects,
                    model_name=candidate.model_name,
                    metadata=meta,
                )
            )

        # Sort descending by similarity score
        items.sort(key=lambda m: m.similarity_score, reverse=True)

        # Truncate to limit and assign ranks
        truncated = items[:limit]
        for idx, item in enumerate(truncated):
            item.rank = idx + 1

        return CrossSourceSimilarityResponse(
            project_id=project_id,
            model_name=project_embedding_record.model_name,
            embedding_dimension=project_embedding_record.embedding_dimension,
            total_matches=len(truncated),
            matches=truncated,
        )
