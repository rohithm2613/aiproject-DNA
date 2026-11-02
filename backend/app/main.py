import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.routes.health import router as health_router
from app.routes.projects import router as projects_router
from app.routes.auth import router as auth_router
from app.routes.analysis import router as analysis_router
from app.routes.research import router as research_router
from app.routes.github import router as github_router
from app.routes.repository_analysis import router as repo_analysis_router
from app.routes.similarity import router as similarity_router
from app.routes.validation import router as validation_router
from app.routes.patents import router as patents_router
from app.services.project_service import ProjectService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("projectdna")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: initializes database tables and sample records."""
    logger.info("Initializing AI ProjectDNA database schema...")
    try:
        # Import models so Base has all metadata registered
        import app.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        
        # Apply safe migrations for Phase 2 user_id column
        from app.database.session import apply_safe_schema_migrations
        apply_safe_schema_migrations()
        
        logger.info("Database schema validated and synchronized successfully.")

        # Seed initial data if empty
        db = SessionLocal()
        try:
            ProjectService.seed_initial_samples_if_empty(db)
        finally:
            db.close()

        # Safe Gemini AI configuration diagnostic
        from app.services.ai_service import AIService
        diag = AIService.get_diagnostics()
        logger.info(
            f"Gemini AI Configuration: status={diag['status']}, detected={diag['detected']}, "
            f"configured={diag['configured']}, client_init={diag['client_initialized']}, "
            f"model={diag['configured_model']}"
        )
    except Exception as exc:
        logger.error(f"Database initialization error: {exc}")

    yield

    logger.info("AI ProjectDNA application shutting down gracefully.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Innovation & Project Validation Platform - Backend API (Phase 4.6 Patent & Prior-Art Discovery Engine)",
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# CORS configuration with credentials support for HttpOnly cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(projects_router, prefix=settings.API_PREFIX)
app.include_router(analysis_router, prefix=settings.API_PREFIX)
app.include_router(research_router, prefix=settings.API_PREFIX)
app.include_router(github_router, prefix=settings.API_PREFIX)
app.include_router(repo_analysis_router, prefix=settings.API_PREFIX)
app.include_router(similarity_router, prefix=settings.API_PREFIX)
app.include_router(validation_router, prefix=settings.API_PREFIX)
app.include_router(patents_router, prefix=settings.API_PREFIX)

@app.get("/")
def root():
    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "phase": "Phase 4.6 - Patent & Prior-Art Discovery Engine",
        "documentation": f"{settings.API_PREFIX}/docs",
        "health_check": f"{settings.API_PREFIX}/health",
        "status": "operational"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred. Please check backend logs."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
