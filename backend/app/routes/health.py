from fastapi import APIRouter
from app.core.config import settings
from app.database.session import check_db_health
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=HealthResponse)
def get_health():
    """Health check endpoint providing application and database connectivity status."""
    db_health = check_db_health()
    status = "healthy" if db_health.get("status") == "connected" else "degraded"
    
    return HealthResponse(
        status=status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        phase="Phase 1 - Foundation & UI Development",
        database=db_health
    )

