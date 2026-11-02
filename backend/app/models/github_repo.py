import uuid
from sqlalchemy import Column, String, Text, Integer, BigInteger, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class GitHubRepository(Base):
    __tablename__ = "github_repositories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(String(36), ForeignKey("project_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    github_repository_id = Column(BigInteger, nullable=False, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    owner_login = Column(String(150), nullable=False)
    owner_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    html_url = Column(String(500), nullable=False)
    homepage = Column(String(500), nullable=True)
    language = Column(String(100), nullable=True, index=True)
    languages = Column(JSON, nullable=False, default=dict)
    topics = Column(JSON, nullable=False, default=list)
    stargazers_count = Column(Integer, nullable=False, default=0)
    forks_count = Column(Integer, nullable=False, default=0)
    watchers_count = Column(Integer, nullable=False, default=0)
    open_issues_count = Column(Integer, nullable=False, default=0)
    default_branch = Column(String(100), nullable=True)
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)
    pushed_at = Column(String(50), nullable=True)
    license_name = Column(String(150), nullable=True)
    archived = Column(Boolean, nullable=False, default=False)
    fork = Column(Boolean, nullable=False, default=False)
    visibility = Column(String(50), nullable=False, default="public")
    size = Column(Integer, nullable=True)
    search_query = Column(String(255), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at_db = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "github_repository_id", name="uq_project_github_repo"),
    )

    # Relationships
    project = relationship("Project", back_populates="github_repositories")
    analysis = relationship("ProjectAnalysis", back_populates="github_repositories")
    user = relationship("User")
    analysis_record = relationship(
        "RepositoryAnalysis",
        back_populates="github_repo",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "analysis_id": self.analysis_id,
            "user_id": self.user_id,
            "github_repository_id": self.github_repository_id,
            "full_name": self.full_name,
            "name": self.name,
            "owner_login": self.owner_login,
            "owner_type": self.owner_type,
            "description": self.description,
            "html_url": self.html_url,
            "homepage": self.homepage,
            "language": self.language,
            "languages": self.languages or {},
            "topics": self.topics or [],
            "stargazers_count": self.stargazers_count,
            "forks_count": self.forks_count,
            "watchers_count": self.watchers_count,
            "open_issues_count": self.open_issues_count,
            "default_branch": self.default_branch,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "pushed_at": self.pushed_at,
            "license_name": self.license_name,
            "archived": self.archived,
            "fork": self.fork,
            "visibility": self.visibility,
            "size": self.size,
            "search_query": self.search_query,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "created_at_db": self.created_at_db.isoformat() if self.created_at_db else None,
        }

