import re
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from app.schemas.research import ResearchPaperSchema

logger = logging.getLogger("uvicorn.error")

class ResearchProviderError(Exception):
    """Base exception for research discovery providers."""
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        super().__init__(f"[{provider}] {message}")
        self.provider = provider
        self.message = message
        self.status_code = status_code

class ProviderTimeoutError(ResearchProviderError):
    """Raised when an external research provider request times out."""
    pass

class ProviderRateLimitError(ResearchProviderError):
    """Raised when an external research provider returns HTTP 429 rate limit."""
    pass

class ProviderAPIError(ResearchProviderError):
    """Raised when an external research provider returns a 5xx or unparseable response."""
    pass

def normalize_doi(doi: Optional[str]) -> Optional[str]:
    """
    Normalizes a DOI string to a clean standard form (e.g. '10.1145/3372278.3390678').
    Removes common URL prefixes and trims whitespace.
    """
    if not doi:
        return None
    cleaned = str(doi).strip().lower()
    cleaned = re.sub(r"^https?://(dx\.)?doi\.org/", "", cleaned)
    cleaned = re.sub(r"^doi:\s*", "", cleaned)
    return cleaned if cleaned else None

def clean_text(text: Optional[str]) -> Optional[str]:
    """Normalizes whitespace and removes unwanted line breaks/control characters."""
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    return cleaned if cleaned else None

def clean_authors(raw_authors: Any) -> List[str]:
    """Converts diverse author representations into a clean list of author names."""
    if not raw_authors:
        return []
    authors: List[str] = []
    if isinstance(raw_authors, list):
        for item in raw_authors:
            if isinstance(item, str):
                name = clean_text(item)
                if name:
                    authors.append(name)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("author") or item.get("display_name")
                name = clean_text(name)
                if name:
                    authors.append(name)
    elif isinstance(raw_authors, str):
        # Comma or semicolon-separated string
        parts = re.split(r"[,;]\s*", raw_authors)
        for part in parts:
            name = clean_text(part)
            if name:
                authors.append(name)
    return authors

class BaseResearchProvider(ABC):
    """Abstract base class for academic research paper discovery providers."""

    provider_name: str = "base"

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[ResearchPaperSchema]:
        """
        Executes an asynchronous paper search query and returns normalized ResearchPaperSchema items.
        Must handle its own retries and provider errors gracefully without raising unhandled exceptions.
        """
        pass

