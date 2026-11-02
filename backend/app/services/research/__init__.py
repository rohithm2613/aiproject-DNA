from app.services.research.base import (
    BaseResearchProvider,
    ResearchProviderError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderAPIError,
    normalize_doi,
    clean_text,
    clean_authors,
)
from app.services.research.arxiv_service import ArxivService
from app.services.research.semantic_scholar_service import SemanticScholarService
from app.services.research.openalex_service import OpenAlexService
from app.services.research.query_generator import generate_research_queries
from app.services.research.research_discovery_service import (
    ResearchDiscoveryService,
    research_discovery_service,
)

__all__ = [
    "BaseResearchProvider",
    "ResearchProviderError",
    "ProviderTimeoutError",
    "ProviderRateLimitError",
    "ProviderAPIError",
    "normalize_doi",
    "clean_text",
    "clean_authors",
    "ArxivService",
    "SemanticScholarService",
    "OpenAlexService",
    "generate_research_queries",
    "ResearchDiscoveryService",
    "research_discovery_service",
]

