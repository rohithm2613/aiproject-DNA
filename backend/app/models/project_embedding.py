import uuid
from typing import Any, List, Optional, Dict
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

try:
    from pgvector.sqlalchemy import Vector as PgVector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

class VectorType(TypeDecorator):
    """
    Dual-compatibility vector type:
    When running on PostgreSQL with the pgvector extension and library, uses PgVector(dim).
    When running on SQLite or standard PostgreSQL, transparently falls back to JSON.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 384, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return dialect.type_descriptor(PgVector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if hasattr(value, "tolist"):
            return value.tolist()
        return list(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if hasattr(value, "tolist"):
            return value.tolist()
        return list(value)

class ProjectEmbedding(Base):
    __tablename__ = "project_embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    source_type = Column(String(50), nullable=False, index=True)  # project, research_paper, github_repository
    source_record_id = Column(String(100), nullable=False, index=True)
    
    embedding = Column(VectorType(384), nullable=False)
    model_name = Column(String(100), nullable=False, default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dimension = Column(Integer, nullable=False, default=384)
    content_hash = Column(String(64), nullable=False, index=True)
    
    metadata_json = Column(JSON, nullable=False, default=dict)

    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "source_type", "source_record_id", "model_name", name="uq_project_embedding_source"),
    )

    # Relationships
    project = relationship("Project", back_populates="embeddings")
    user = relationship("User")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "source_type": self.source_type,
            "source_record_id": self.source_record_id,
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "content_hash": self.content_hash,
            "metadata": self.metadata_json or {},
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

