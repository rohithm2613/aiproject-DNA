import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def get_engine():
    """
    Creates SQLAlchemy engine for PostgreSQL.
    If PostgreSQL is unreachable and fallback is enabled, uses SQLite.
    """
    primary_url = settings.DATABASE_URL
    if primary_url.startswith("postgresql://"):
        primary_url = primary_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    try:
        engine = create_engine(
            primary_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3} if "postgresql" in primary_url else {}
        )
        # Test connection immediately
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Successfully connected to primary database: {engine.url.render_as_string(hide_password=True)}")
        return engine
    except Exception as exc:
        logger.warning(f"Could not connect to primary database ({exc}).")
        if settings.FALLBACK_TO_SQLITE:
            logger.info(f"Falling back to local SQLite database: {settings.SQLITE_URL}")
            fallback_engine = create_engine(
                settings.SQLITE_URL,
                connect_args={"check_same_thread": False}
            )
            return fallback_engine
        raise exc

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency for database sessions."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_health() -> dict:
    """Verifies database connectivity for health check."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        dialect = engine.dialect.name
        return {
            "status": "connected",
            "dialect": dialect,
            "database": engine.url.database or "local"
        }
    except Exception as exc:
        return {
            "status": "disconnected",
            "error": str(exc)
        }

def apply_safe_schema_migrations():
    """
    Safely verifies and applies Phase 2 & Phase 3 schema modifications to existing databases.
    Ensures 'users' and 'project_analyses' tables exist and 'projects.user_id' column is present.
    """
    from sqlalchemy import inspect
    try:
        # Import models so Base has all metadata registered
        import app.models  # noqa: F401
        from app.database.base import Base
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Check projects table for user_id column
        if "projects" in tables:
            columns = [c["name"] for c in inspector.get_columns("projects")]
            if "user_id" not in columns:
                logger.info("Migrating schema: Adding missing 'user_id' column to 'projects' table...")
                with engine.begin() as conn:
                    # Generic ALTER TABLE compatible with both SQLite and PostgreSQL
                    conn.execute(text("ALTER TABLE projects ADD COLUMN user_id VARCHAR(36)"))
                    try:
                        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id)"))
                    except Exception:
                        pass
                logger.info("Successfully added 'user_id' column to projects table.")
    except Exception as exc:
        logger.warning(f"Safe schema migration notice: {exc}")

