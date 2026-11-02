from typing import Any, Dict
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    phase: str
    database: Dict[str, Any]

