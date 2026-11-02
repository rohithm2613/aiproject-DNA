from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class RecommendedTechnologiesSchema(BaseModel):
    languages: List[str] = Field(default_factory=list, description="Suggested programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Suggested frameworks and libraries")
    algorithms: List[str] = Field(default_factory=list, description="Relevant AI/ML algorithms or computational methods")
    hardware: List[str] = Field(default_factory=list, description="Hardware or acceleration components")
    tools: List[str] = Field(default_factory=list, description="Developer, testing, or deployment tools")
    infrastructure: List[str] = Field(default_factory=list, description="Cloud, database, or container infrastructure")

class ProjectRequirementsSchema(BaseModel):
    possible_datasets: List[str] = Field(default_factory=list, description="Potential candidate datasets (unverified availability)")
    hardware_requirements: List[str] = Field(default_factory=list, description="Compute, memory, or sensor hardware needs")
    software_requirements: List[str] = Field(default_factory=list, description="Operating system, runtime, or protocol requirements")
    external_dependencies: List[str] = Field(default_factory=list, description="External APIs or third-party services")
    technical_constraints: List[str] = Field(default_factory=list, description="Latency, bandwidth, compute, or ethical constraints")

class ProjectRisksSchema(BaseModel):
    technical_challenges: List[str] = Field(default_factory=list, description="Core technical and algorithmic hurdles")
    implementation_risks: List[str] = Field(default_factory=list, description="Execution, data scarcity, or deployment risks")

class ProjectAnalysisSchema(BaseModel):
    """Structured Pydantic model for Gemini AI analysis output."""
    project_summary: str = Field(..., description="Comprehensive technical synopsis of the project idea")
    problem_statement: str = Field(..., description="Precise formulation of the specific problem being addressed")
    proposed_solution: str = Field(..., description="Detailed description of the proposed architectural/engineering solution")
    primary_domain: str = Field(..., description="Main scientific or industrial vertical")
    secondary_domains: List[str] = Field(default_factory=list, description="Cross-disciplinary domains and secondary fields")
    keywords: List[str] = Field(default_factory=list, description="10 to 20 precise technical and research keywords")
    recommended_technologies: RecommendedTechnologiesSchema = Field(..., description="AI-recommended technology stack")
    objectives: List[str] = Field(default_factory=list, description="4 to 6 measurable, actionable project objectives")
    target_users: List[str] = Field(default_factory=list, description="Potential users, stakeholders, and beneficiaries")
    project_type: str = Field(..., description="Classification: Research-oriented, Application-oriented, Hardware-oriented, Software-oriented, or Hybrid")
    difficulty_level: str = Field(..., description="Complexity rating: Beginner, Intermediate, Advanced, or Expert")
    difficulty_reasoning: str = Field(..., description="Justification explaining the assigned difficulty level")
    requirements: ProjectRequirementsSchema = Field(..., description="Dataset, hardware, and dependency requirements")
    assumptions: List[str] = Field(default_factory=list, description="Underlying engineering assumptions")
    risks: ProjectRisksSchema = Field(..., description="Technical challenges and implementation risks")

class ProjectAnalysisResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    version: int
    project_summary: str
    problem_statement: str
    proposed_solution: str
    primary_domain: str
    secondary_domains: List[str]
    keywords: List[str]
    user_technologies: List[str]
    recommended_technologies: RecommendedTechnologiesSchema
    objectives: List[str]
    target_users: List[str]
    project_type: str
    difficulty_level: str
    difficulty_reasoning: str
    requirements: ProjectRequirementsSchema
    assumptions: List[str]
    risks: ProjectRisksSchema
    model_name: str
    analysis_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectAnalysisListResponse(BaseModel):
    project_id: str
    total_versions: int
    analyses: List[ProjectAnalysisResponse]

class DashboardAnalyticsResponse(BaseModel):
    total_projects: int
    ideas_analyzed: int
    pending_analyses: int
    completed_analyses: int
    recent_analyses: List[Dict[str, Any]]

