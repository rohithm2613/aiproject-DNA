import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class RepositoryAnalysis(Base):
    __tablename__ = "repository_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    github_repo_id = Column(String(36), ForeignKey("github_repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    repo_full_name = Column(String(255), nullable=False, index=True)
    readme_present = Column(Boolean, nullable=False, default=False)
    readme_url = Column(String(500), nullable=True)
    readme_size = Column(Integer, nullable=True)

    summary = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=True)

    detected_technologies = Column(JSON, nullable=False, default=dict)
    architecture = Column(JSON, nullable=False, default=dict)
    features = Column(JSON, nullable=False, default=list)
    similarity = Column(JSON, nullable=False, default=dict)

    analysis_status = Column(String(50), nullable=False, default="completed", index=True)  # completed, failed, partial
    analysis_mode = Column(String(50), nullable=False, default="ai_enhanced")  # ai_enhanced, deterministic_fallback
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("project_id", "github_repo_id", name="uq_project_repo_analysis"),
    )

    # Relationships
    project = relationship("Project", back_populates="repository_analyses")
    github_repo = relationship("GitHubRepository", back_populates="analysis_record")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "github_repo_id": self.github_repo_id,
            "user_id": self.user_id,
            "repo_full_name": self.repo_full_name,
            "readme_present": self.readme_present,
            "readme_url": self.readme_url,
            "readme_size": self.readme_size,
            "summary": self.summary,
            "problem_statement": self.problem_statement,
            "detected_technologies": self.detected_technologies or {},
            "architecture": self.architecture or {},
            "features": self.features or [],
            "similarity": self.similarity or {},
            "analysis_status": self.analysis_status,
            "analysis_mode": self.analysis_mode,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

