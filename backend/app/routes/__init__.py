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

__all__ = [
    "health_router",
    "projects_router",
    "auth_router",
    "analysis_router",
    "research_router",
    "github_router",
    "repo_analysis_router",
    "similarity_router",
    "validation_router",
    "patents_router",
]
