from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ProjectBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Project title")
    description: str = Field(..., min_length=10, description="Project idea description")
    domain: str = Field(..., min_length=2, max_length=100, description="Domain/industry category")
    technologies: List[str] = Field(default_factory=list, description="Target technologies or stack preferences")
    objectives: Optional[str] = Field(None, description="Primary project objectives or expected outcomes")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    domain: Optional[str] = Field(None, min_length=2, max_length=100)
    technologies: Optional[List[str]] = None
    objectives: Optional[str] = None
    status: Optional[str] = Field(None, description="Project status (e.g. pending_validation, validated, draft)")

class ProjectResponse(ProjectBase):
    id: str
    user_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int = 1
    limit: int = 50
