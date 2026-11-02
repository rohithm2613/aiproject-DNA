from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ProjectEmbeddingResponse(BaseModel):
    """Schema representing an individual stored embedding record (omits raw vector)."""
    id: str
    project_id: str
    source_type: str
    source_record_id: str
    model_name: str
    embedding_dimension: int
    content_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class EmbeddingGenerateRequest(BaseModel):
    """Parameters for triggering embedding generation for a project."""
    force_regenerate: bool = Field(default=False, description="Whether to re-embed items whose content has not changed")
    include_papers: bool = Field(default=True, description="Whether to embed stored academic research papers")
    include_repos: bool = Field(default=True, description="Whether to embed stored GitHub repositories")

class EmbeddingGenerateResponse(BaseModel):
    """Result of embedding generation pipeline."""
    status: str = "completed"  # completed, partial_success, failed
    project_id: str
    model_name: str
    embedding_dimension: int
    total_generated: int = 0
    total_skipped: int = 0
    total_failed: int = 0
    counts_by_source: Dict[str, int] = Field(default_factory=dict)
    errors: Dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class SemanticMatchItem(BaseModel):
    """Ranked semantic match between project idea and a research paper or repository."""
    rank: int = Field(default=1, description="Ordinal rank ordered by similarity descending")
    source_type: str = Field(description="research_paper | github_repository")
    source_record_id: str
    title: str
    url: Optional[str] = None
    similarity_score: float = Field(description="Cosine similarity between 0.0 and 1.0 (or -1.0 to 1.0)")
    similarity_percentage: float = Field(description="Similarity formatted as a percentage 0.0 - 100.0%")
    similarity_label: str = Field(description="High semantic similarity | Moderate semantic similarity | Low semantic similarity")
    matching_content_summary: str = Field(description="Summary of the matched document content used for embedding")
    matched_aspects: List[str] = Field(default_factory=list, description="Key conceptual facets identified in both sources")
    model_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CrossSourceSimilarityResponse(BaseModel):
    """Ranked cross-source semantic similarity search results."""
    project_id: str
    model_name: str
    embedding_dimension: int
    total_matches: int
    matches: List[SemanticMatchItem] = Field(default_factory=list)
    disclaimer: str = (
        "Semantic similarity reflects conceptual proximity in dense vector space under the designated model. "
        "It does not constitute conclusive proof of duplication or novelty."
    )

class SimilarityStatsResponse(BaseModel):
    """Aggregated statistics for project embeddings and similarity potential."""
    project_id: str
    model_name: str
    embedding_dimension: int
    total_embeddings_stored: int = 0
    embeddings_by_source_type: Dict[str, int] = Field(default_factory=dict)
    latest_generation_timestamp: Optional[datetime] = None
    total_matches_available: int = 0
    has_project_embedding: bool = False
    processing_failures: Dict[str, str] = Field(default_factory=dict)
