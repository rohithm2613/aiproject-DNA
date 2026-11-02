import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class InnovationGap(Base):
    __tablename__ = "innovation_gaps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    gap_title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # missing_feature, partially_implemented, improvement_opportunity, differentiating_feature
    description = Column(Text, nullable=False)
    why_it_matters = Column(Text, nullable=False)
    suggested_implementation = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, index=True)  # high, medium, low
    confidence_level = Column(String(20), nullable=False)      # high, medium, low
    supporting_evidence = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="innovation_gaps")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "gap_title": self.gap_title,
            "category": self.category,
            "description": self.description,
            "why_it_matters": self.why_it_matters,
            "suggested_implementation": self.suggested_implementation,
            "priority": self.priority,
            "confidence_level": self.confidence_level,
            "supporting_evidence": self.supporting_evidence or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

