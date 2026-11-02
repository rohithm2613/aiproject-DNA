import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.project import Project
from app.models.user import User
from app.models.analysis import ProjectAnalysis
from app.schemas.analysis import ProjectAnalysisSchema, DashboardAnalyticsResponse
from app.services.ai_service import AIService
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

class ProjectAnalysisService:
    @staticmethod
    def analyze_project(
        db: Session,
        project: Project,
        user: User,
        ai_service_cls=AIService
    ) -> ProjectAnalysis:
        """
        Runs AI analysis via Google Gemini API, validates the result,
        persists a new versioned record, and updates project status.
        """
        # Determine next analysis version number for this project
        current_max = db.query(func.max(ProjectAnalysis.version)).filter(
            ProjectAnalysis.project_id == project.id
        ).scalar()
        next_version = (current_max or 0) + 1

        # Invoke Gemini AI analysis
        analysis_data: ProjectAnalysisSchema = ai_service_cls.analyze_project_idea(
            title=project.title,
            description=project.description,
            domain=project.domain,
            user_technologies=project.technologies or [],
            objectives=project.objectives
        )

        # Determine model name safely
        used_model = getattr(ai_service_cls, "last_model_used", None)
        model_name_str = used_model if isinstance(used_model, str) else (settings.GEMINI_MODEL or "gemini-2.5-flash")

        # Create persistent database record
        analysis_record = ProjectAnalysis(
            project_id=project.id,
            user_id=user.id,
            version=next_version,
            project_summary=analysis_data.project_summary,
            problem_statement=analysis_data.problem_statement,
            proposed_solution=analysis_data.proposed_solution,
            primary_domain=analysis_data.primary_domain,
            secondary_domains=analysis_data.secondary_domains,
            keywords=analysis_data.keywords,
            user_technologies=project.technologies or [],
            recommended_technologies=analysis_data.recommended_technologies.model_dump(),
            objectives=analysis_data.objectives,
            target_users=analysis_data.target_users,
            project_type=analysis_data.project_type,
            difficulty_level=analysis_data.difficulty_level,
            difficulty_reasoning=analysis_data.difficulty_reasoning,
            requirements=analysis_data.requirements.model_dump(),
            assumptions=analysis_data.assumptions,
            risks=analysis_data.risks.model_dump(),
            model_name=model_name_str,
            analysis_status="completed"
        )

        db.add(analysis_record)

        # Update parent project state
        project.status = "analysis_completed"
        db.commit()
        db.refresh(analysis_record)
        db.refresh(project)

        logger.info(f"Persisted analysis version {next_version} for project '{project.title}' (ID: {analysis_record.id}).")
        return analysis_record

    @staticmethod
    def get_analysis_for_project(
        db: Session,
        project_id: str,
        user_id: str,
        version: Optional[int] = None
    ) -> Optional[ProjectAnalysis]:
        """Fetch analysis by project ID and optional version, scoped to the user."""
        query = db.query(ProjectAnalysis).filter(
            ProjectAnalysis.project_id == project_id,
            ProjectAnalysis.user_id == user_id
        )
        if version is not None and isinstance(version, int):
            return query.filter(ProjectAnalysis.version == version).first()
        return query.order_by(desc(ProjectAnalysis.version)).first()

    @staticmethod
    def get_all_analyses_for_project(
        db: Session,
        project_id: str,
        user_id: str
    ) -> List[ProjectAnalysis]:
        """Retrieve all version history of analyses for a given project."""
        return db.query(ProjectAnalysis).filter(
            ProjectAnalysis.project_id == project_id,
            ProjectAnalysis.user_id == user_id
        ).order_by(desc(ProjectAnalysis.version)).all()

    @staticmethod
    def get_analysis_by_id(
        db: Session,
        analysis_id: str,
        user_id: str
    ) -> Optional[ProjectAnalysis]:
        """Fetch specific analysis record by ID, verifying ownership."""
        return db.query(ProjectAnalysis).filter(
            ProjectAnalysis.id == analysis_id,
            ProjectAnalysis.user_id == user_id
        ).first()

    @staticmethod
    def get_dashboard_analytics(db: Session, user_id: str) -> DashboardAnalyticsResponse:
        """
        Computes real user-specific platform and AI analytics from actual database records.
        """
        total_projects = db.query(Project).filter(Project.user_id == user_id).count()

        # Count of distinct projects with at least one completed analysis
        ideas_analyzed = db.query(func.count(func.distinct(ProjectAnalysis.project_id))).filter(
            ProjectAnalysis.user_id == user_id,
            ProjectAnalysis.analysis_status == "completed"
        ).scalar() or 0

        pending_analyses = db.query(Project).filter(
            Project.user_id == user_id,
            Project.status == "pending_validation"
        ).count()

        completed_analyses = db.query(ProjectAnalysis).filter(
            ProjectAnalysis.user_id == user_id,
            ProjectAnalysis.analysis_status == "completed"
        ).count()

        # Recent analysis timeline
        recent_records = db.query(ProjectAnalysis, Project.title).join(
            Project, ProjectAnalysis.project_id == Project.id
        ).filter(
            ProjectAnalysis.user_id == user_id
        ).order_by(desc(ProjectAnalysis.created_at)).limit(5).all()

        recent_list = []
        for analysis, proj_title in recent_records:
            recent_list.append({
                "id": analysis.id,
                "project_id": analysis.project_id,
                "project_title": proj_title,
                "version": analysis.version,
                "primary_domain": analysis.primary_domain,
                "difficulty_level": analysis.difficulty_level,
                "project_type": analysis.project_type,
                "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            })

        return DashboardAnalyticsResponse(
            total_projects=total_projects,
            ideas_analyzed=ideas_analyzed,
            pending_analyses=pending_analyses,
            completed_analyses=completed_analyses,
            recent_analyses=recent_list
        )

