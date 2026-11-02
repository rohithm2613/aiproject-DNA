import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class Patent(Base):
    __tablename__ = "patents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(String(36), ForeignKey("project_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    provider = Column(String(50), nullable=False, index=True)  # uspto, epo
    provider_patent_id = Column(String(255), nullable=False)
    publication_number = Column(String(100), nullable=False, index=True)
    application_number = Column(String(100), nullable=True)
    patent_number = Column(String(100), nullable=True)
    title = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    claims = Column(JSON, nullable=False, default=list)
    inventors = Column(JSON, nullable=False, default=list)
    assignees = Column(JSON, nullable=False, default=list)
    filing_date = Column(String(50), nullable=True)
    publication_date = Column(String(50), nullable=True)
    grant_date = Column(String(50), nullable=True)
    priority_date = Column(String(50), nullable=True)
    jurisdiction = Column(String(10), nullable=True, index=True)  # US, EP, WO, etc.
    patent_type = Column(String(50), nullable=True)  # Utility, Design, Plant, etc.
    cpc_classifications = Column(JSON, nullable=False, default=list)
    ipc_classifications = Column(JSON, nullable=False, default=list)
    patent_family_id = Column(String(100), nullable=True)
    legal_status = Column(String(50), nullable=True)  # Active, Granted, Pending, Expired, Unknown
    source_url = Column(String(500), nullable=True)
    raw_metadata = Column(JSON, nullable=False, default=dict)

    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "publication_number", name="uq_project_patent_publication"),
    )

    # Relationships
    project = relationship("Project", back_populates="patents")
    analysis = relationship("ProjectAnalysis", back_populates="patents")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "analysis_id": self.analysis_id,
            "user_id": self.user_id,
            "provider": self.provider,
            "provider_patent_id": self.provider_patent_id,
            "publication_number": self.publication_number,
            "application_number": self.application_number,
            "patent_number": self.patent_number,
            "title": self.title,
            "abstract": self.abstract,
            "description": self.description,
            "claims": self.claims or [],
            "inventors": self.inventors or [],
            "assignees": self.assignees or [],
            "filing_date": self.filing_date,
            "publication_date": self.publication_date,
            "grant_date": self.grant_date,
            "priority_date": self.priority_date,
            "jurisdiction": self.jurisdiction,
            "patent_type": self.patent_type,
            "cpc_classifications": self.cpc_classifications or [],
            "ipc_classifications": self.ipc_classifications or [],
            "patent_family_id": self.patent_family_id,
            "legal_status": self.legal_status,
            "source_url": self.source_url,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

