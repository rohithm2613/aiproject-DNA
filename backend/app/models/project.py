import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    domain = Column(String(100), nullable=False, index=True)
    technologies = Column(JSON, nullable=False, default=list)
    objectives = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending_validation")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Owner relationship
    user = relationship("User", back_populates="projects")
    analyses = relationship(
        "ProjectAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(ProjectAnalysis.version)"
    )
    research_papers = relationship(
        "ResearchPaper",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    github_repositories = relationship(
        "GitHubRepository",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    repository_analyses = relationship(
        "RepositoryAnalysis",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    innovation_gaps = relationship(
        "InnovationGap",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    embeddings = relationship(
        "ProjectEmbedding",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    validation_reports = relationship(
        "ProjectValidationReport",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(ProjectValidationReport.version)"
    )
    patents = relationship(
        "Patent",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain,
            "technologies": self.technologies or [],
            "objectives": self.objectives,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
