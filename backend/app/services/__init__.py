from app.services.project_service import ProjectService
from app.services.user_service import UserService
from app.services.ai_service import AIService
from app.services.project_analysis_service import ProjectAnalysisService
from app.services.research import ResearchDiscoveryService, research_discovery_service
from app.services.github import (
    GitHubService,
    github_service,
    RepositoryAnalyzer,
    InnovationGapService,
)
from app.services.embedding import (
    EmbeddingService,
    EmbeddingModelError,
    TextPreprocessor,
    SemanticSimilarityService,
    EmbeddingPipeline,
)
from app.services.rag import (
    EvidenceRetrievalService,
    CitationService,
    ResearchGapValidator,
    synthesize_deterministic_report,
    RAGService,
)
from app.services.patents import (
    PatentDiscoveryService,
    PatentEmbeddingService,
    PatentAnalysisService,
    UsptoPatentService,
    EpoPatentService,
)

__all__ = [
    "ProjectService",
    "UserService",
    "AIService",
    "ProjectAnalysisService",
    "ResearchDiscoveryService",
    "research_discovery_service",
    "GitHubService",
    "github_service",
    "RepositoryAnalyzer",
    "InnovationGapService",
    "EmbeddingService",
    "EmbeddingModelError",
    "TextPreprocessor",
    "SemanticSimilarityService",
    "EmbeddingPipeline",
    "EvidenceRetrievalService",
    "CitationService",
    "ResearchGapValidator",
    "synthesize_deterministic_report",
    "RAGService",
    "PatentDiscoveryService",
    "PatentEmbeddingService",
    "PatentAnalysisService",
    "UsptoPatentService",
    "EpoPatentService",
]
