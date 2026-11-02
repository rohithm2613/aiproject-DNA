import uuid
from typing import Dict, Any, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class ProjectValidationReport(Base):
    __tablename__ = "project_validation_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(String(36), ForeignKey("project_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    version = Column(Integer, default=1, nullable=False)
    report_status = Column(String(50), default="completed", nullable=False)  # completed, partial_coverage, failed
    
    report_json = Column(JSON, nullable=False, default=dict)
    evidence_manifest = Column(JSON, nullable=False, default=list)
    model_name = Column(String(100), default="gemini-2.5-flash", nullable=False)
    retrieval_metadata = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        Index("ix_project_validation_reports_proj_version", "project_id", "version"),
    )

    # Relationships
    project = relationship("Project", back_populates="validation_reports")
    analysis = relationship("ProjectAnalysis")
    user = relationship("User")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "analysis_id": self.analysis_id,
            "user_id": self.user_id,
            "version": self.version,
            "report_status": self.report_status,
            "report": self.report_json,
            "evidence_manifest": self.evidence_manifest,
            "model_name": self.model_name,
            "retrieval_metadata": self.retrieval_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

