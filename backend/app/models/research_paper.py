import uuid
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class ResearchPaper(Base):
    __tablename__ = "research_papers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(String(36), ForeignKey("project_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    provider = Column(String(50), nullable=False, index=True)  # arxiv, semantic_scholar, openalex
    provider_paper_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=True)
    authors = Column(JSON, nullable=False, default=list)
    publication_year = Column(Integer, nullable=True)
    publication_date = Column(String(50), nullable=True)
    venue = Column(String(255), nullable=True)
    doi = Column(String(255), nullable=True, index=True)
    arxiv_id = Column(String(100), nullable=True)
    citation_count = Column(Integer, nullable=True)
    paper_url = Column(String(500), nullable=True)
    pdf_url = Column(String(500), nullable=True)
    open_access = Column(Boolean, nullable=True)
    primary_category = Column(String(100), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "provider", "provider_paper_id", name="uq_project_provider_paper"),
    )

    # Relationships
    project = relationship("Project", back_populates="research_papers")
    analysis = relationship("ProjectAnalysis", back_populates="research_papers")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "analysis_id": self.analysis_id,
            "user_id": self.user_id,
            "provider": self.provider,
            "provider_paper_id": self.provider_paper_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors or [],
            "publication_year": self.publication_year,
            "publication_date": self.publication_date,
            "venue": self.venue,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "citation_count": self.citation_count,
            "paper_url": self.paper_url,
            "pdf_url": self.pdf_url,
            "open_access": self.open_access,
            "primary_category": self.primary_category,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

