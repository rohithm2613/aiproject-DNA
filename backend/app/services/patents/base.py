import re
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from app.schemas.patent import PatentSchema

logger = logging.getLogger("uvicorn.error")

class PatentProviderError(Exception):
    """Base exception for patent discovery providers."""
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        super().__init__(f"[{provider}] {message}")
        self.provider = provider
        self.message = message
        self.status_code = status_code

class PatentTimeoutError(PatentProviderError):
    """Raised when an external patent provider request times out."""
    pass

class PatentRateLimitError(PatentProviderError):
    """Raised when an external patent provider returns HTTP 429 rate limit."""
    pass

class PatentAPIError(PatentProviderError):
    """Raised when an external patent provider returns an HTTP error or unparseable response."""
    pass

class PatentAuthError(PatentProviderError):
    """Raised when an external patent provider fails authentication or missing credentials."""
    pass

def normalize_publication_number(raw_num: Optional[str]) -> str:
    """
    Normalizes a patent publication or grant number into a standardized alphanumeric representation.
    Removes hyphens, spaces, slashes, commas, dots and converts to uppercase.
    Example: 'US-11,234,567-B2' -> 'US11234567B2'
    """
    if not raw_num:
        return ""
    cleaned = re.sub(r"[\s\-_/,\.]+", "", str(raw_num)).strip().upper()
    return cleaned

def extract_jurisdiction(publication_number: str) -> str:
    """
    Extracts the leading two-letter country / jurisdiction code (e.g., US, EP, WO, CN, JP, DE, GB).
    Defaults to 'US' if missing or starts with digits.
    """
    if not publication_number:
        return "UNKNOWN"
    match = re.match(r"^([A-Z]{2})", publication_number.upper())
    if match:
        return match.group(1)
    return "US"

def build_google_patents_url(publication_number: Optional[str]) -> Optional[str]:
    """
    Generates a canonical Google Patents link for human verification.
    URL format: https://patents.google.com/patent/{publication_number}/en
    """
    if not publication_number:
        return None
    normalized = normalize_publication_number(publication_number)
    if not normalized:
        return None
    return f"https://patents.google.com/patent/{normalized}/en"

def clean_text(text: Optional[str]) -> Optional[str]:
    """Normalizes whitespace and removes unwanted line breaks/control characters."""
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    return cleaned if cleaned else None

def clean_list(raw_list: Any) -> List[str]:
    """Converts diverse string or list representations into a clean list of strings."""
    if not raw_list:
        return []
    cleaned: List[str] = []

    def add_token(t: Optional[str]):
        if not t:
            return
        parts = re.split(r"[,;]\s*", str(t))
        for p in parts:
            txt = clean_text(p)
            if txt and txt not in cleaned:
                cleaned.append(txt)

    if isinstance(raw_list, list):
        for item in raw_list:
            if isinstance(item, str):
                add_token(item)
            elif isinstance(item, dict):
                val = item.get("name") or item.get("title") or item.get("code") or item.get("text")
                add_token(val)
    elif isinstance(raw_list, str):
        add_token(raw_list)
    return cleaned

class BasePatentProvider(ABC):
    """Abstract base class for patent discovery providers."""

    provider_name: str = "base"

    @abstractmethod
    async def search(
        self,
        keywords: List[str],
        classifications: Optional[List[str]] = None,
        max_results: int = 15,
        jurisdiction: Optional[str] = None,
    ) -> List[PatentSchema]:
        """
        Executes a patent search and returns normalized PatentSchema items.
        Must handle its own errors gracefully without crashing the whole search process.
        """
        pass

