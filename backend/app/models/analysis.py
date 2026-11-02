import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class ProjectAnalysis(Base):
    __tablename__ = "project_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)

    # Core Understanding
    project_summary = Column(Text, nullable=False)
    problem_statement = Column(Text, nullable=False)
    proposed_solution = Column(Text, nullable=False)

    # Domain Identification
    primary_domain = Column(String(100), nullable=False)
    secondary_domains = Column(JSON, nullable=False, default=list)

    # Keywords & Technologies
    keywords = Column(JSON, nullable=False, default=list)
    user_technologies = Column(JSON, nullable=False, default=list)
    recommended_technologies = Column(JSON, nullable=False, default=dict)

    # Project Scope & Classification
    objectives = Column(JSON, nullable=False, default=list)
    target_users = Column(JSON, nullable=False, default=list)
    project_type = Column(String(50), nullable=False)
    difficulty_level = Column(String(50), nullable=False)
    difficulty_reasoning = Column(Text, nullable=False)

    # Requirements, Assumptions & Risks
    requirements = Column(JSON, nullable=False, default=dict)
    assumptions = Column(JSON, nullable=False, default=list)
    risks = Column(JSON, nullable=False, default=dict)

    # Metadata
    model_name = Column(String(100), nullable=False, default="gemini-2.5-flash")
    analysis_status = Column(String(50), nullable=False, default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    project = relationship("Project", back_populates="analyses")
    user = relationship("User", back_populates="analyses")
    research_papers = relationship("ResearchPaper", back_populates="analysis")
    github_repositories = relationship("GitHubRepository", back_populates="analysis")
    patents = relationship("Patent", back_populates="analysis")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "version": self.version,
            "project_summary": self.project_summary,
            "problem_statement": self.problem_statement,
            "proposed_solution": self.proposed_solution,
            "primary_domain": self.primary_domain,
            "secondary_domains": self.secondary_domains or [],
            "keywords": self.keywords or [],
            "user_technologies": self.user_technologies or [],
            "recommended_technologies": self.recommended_technologies or {},
            "objectives": self.objectives or [],
            "target_users": self.target_users or [],
            "project_type": self.project_type,
            "difficulty_level": self.difficulty_level,
            "difficulty_reasoning": self.difficulty_reasoning,
            "requirements": self.requirements or {},
            "assumptions": self.assumptions or [],
            "risks": self.risks or {},
            "model_name": self.model_name,
            "analysis_status": self.analysis_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

