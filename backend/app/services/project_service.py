import logging
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger("uvicorn.error")

class ProjectService:
    @staticmethod
    def get_projects(
        db: Session,
        user_id: str,
        search: Optional[str] = None,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Project], int]:
        """
        Retrieve projects strictly scoped to the authenticated user.
        Supports search, domain filtering, status filtering, and pagination.
        """
        query = db.query(Project).filter(Project.user_id == user_id)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Project.title.ilike(search_term),
                    Project.description.ilike(search_term),
                    Project.domain.ilike(search_term),
                )
            )

        if domain and domain.lower() != "all":
            query = query.filter(Project.domain.ilike(domain.strip()))

        if status and status.lower() != "all":
            query = query.filter(Project.status == status.strip())

        total = query.count()
        projects = query.order_by(desc(Project.created_at)).offset(skip).limit(limit).all()
        return projects, total

    @staticmethod
    def get_project_by_id(
        db: Session,
        project_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Project]:
        """
        Fetch a single project by primary key ID.
        If user_id is provided, strictly enforces that the project belongs to the user.
        """
        query = db.query(Project).filter(Project.id == project_id)
        if user_id:
            query = query.filter(Project.user_id == user_id)
        return query.first()

    @staticmethod
    def check_project_exists(db: Session, project_id: str) -> bool:
        """Check if a project ID exists in the database regardless of owner."""
        return db.query(Project.id).filter(Project.id == project_id).first() is not None

    @staticmethod
    def create_project(
        db: Session,
        project_in: ProjectCreate,
        user_id: str
    ) -> Project:
        """Create and persist a new project record bound to the authenticated creator."""
        project = Project(
            user_id=user_id,
            title=project_in.title.strip(),
            description=project_in.description.strip(),
            domain=project_in.domain.strip(),
            technologies=project_in.technologies or [],
            objectives=project_in.objectives.strip() if project_in.objectives else None,
            status="pending_validation"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def update_project(
        db: Session,
        project_id: str,
        project_in: ProjectUpdate,
        user_id: str
    ) -> Optional[Project]:
        """Update an existing project record owned by the user."""
        project = ProjectService.get_project_by_id(db, project_id, user_id=user_id)
        if not project:
            return None

        update_data = project_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(
        db: Session,
        project_id: str,
        user_id: str
    ) -> bool:
        """Delete a project record owned by the user."""
        project = ProjectService.get_project_by_id(db, project_id, user_id=user_id)
        if not project:
            return False
        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def seed_initial_samples_if_empty(db: Session):
        """
        Safely seeds sample projects if database is empty.
        Sample projects retain user_id=None (system/legacy data)
        so they are preserved without leaking into registered users' personal dashboards.
        """
        try:
            count = db.query(Project).count()
            if count > 0:
                return

            samples = [
                Project(
                    user_id=None,
                    title="MedScanAI: Multimodal Radiology Assistant",
                    description="An intelligent medical imaging assistant that cross-references chest X-rays with patient EHR history to detect early pulmonary abnormalities.",
                    domain="Healthcare & AI",
                    technologies=["PyTorch", "FastAPI", "React", "Docker", "DICOM"],
                    objectives="Reduce radiologist diagnosis review time by 35% while maintaining a 98% specificity rate on priority anomalies.",
                    status="ready_for_analysis"
                ),
                Project(
                    user_id=None,
                    title="EcoGrid: Decentralized Microgrid Load Balancer",
                    description="Autonomous smart-meter orchestration utilizing distributed edge controllers to optimize neighborhood solar power exchange.",
                    domain="CleanTech & IoT",
                    technologies=["Python", "MQTT", "TimeScaleDB", "React", "Tailwind CSS"],
                    objectives="Minimize peak fossil fuel drawdown across residential microgrid clusters using predictive load forecasting.",
                    status="validated"
                ),
                Project(
                    user_id=None,
                    title="CodeGuardian: Zero-Day Smart Contract Fuzzer",
                    description="Deep reinforcement learning powered security analysis pipeline for EVM smart contracts to detect reentrancy and logic exploits before mainnet deployment.",
                    domain="Cybersecurity & Web3",
                    technologies=["Solidity", "Rust", "Python", "React", "PostgreSQL"],
                    objectives="Automate exploit sequence generation and provide formal verification proofs for high-value DeFi protocols.",
                    status="pending_validation"
                ),
                Project(
                    user_id=None,
                    title="EduTutor: Real-Time Socratic Code Mentor",
                    description="An interactive programming instructor that provides guided questioning instead of answers to help computer science students build deep algorithmic intuition.",
                    domain="EdTech",
                    technologies=["TypeScript", "FastAPI", "React", "WebSockets", "Node.js"],
                    objectives="Enhance student problem-solving retention without relying on code generation crutches.",
                    status="ready_for_analysis"
                )
            ]

            db.add_all(samples)
            db.commit()
            logger.info("Successfully seeded initial sample projects into database (user_id=None).")
        except Exception as e:
            db.rollback()
            logger.warning(f"Initial sample seeding skipped or encountered error: {e}")
