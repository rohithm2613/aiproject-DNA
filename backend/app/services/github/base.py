import re
import logging
from typing import Optional, Dict, Any
from app.schemas.github import GitHubRateLimitInfo

logger = logging.getLogger("uvicorn.error")

class GitHubAPIError(Exception):
    """Base exception for GitHub API interactions."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(f"[GitHub] {message}")
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

class GitHubAuthError(GitHubAPIError):
    """Raised when GitHub returns 401 Unauthorized (invalid or expired token)."""
    pass

class GitHubRateLimitError(GitHubAPIError):
    """Raised when GitHub returns 403 rate limit reached."""
    def __init__(self, message: str, status_code: int = 403, reset_time: Optional[int] = None):
        super().__init__(message, status_code=status_code)
        self.reset_time = reset_time

class GitHubTimeoutError(GitHubAPIError):
    """Raised when GitHub HTTP request times out."""
    pass

def clean_text(text: Optional[str]) -> Optional[str]:
    """Normalizes whitespace and removes control characters."""
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    return cleaned if cleaned else None

def parse_rate_limit(headers: Any) -> GitHubRateLimitInfo:
    """Extracts rate limit metadata from GitHub response headers."""
    def _get_int(key: str) -> Optional[int]:
        val = headers.get(key)
        if val and str(val).isdigit():
            return int(val)
        return None

    return GitHubRateLimitInfo(
        limit=_get_int("x-ratelimit-limit"),
        remaining=_get_int("x-ratelimit-remaining"),
        reset=_get_int("x-ratelimit-reset"),
        used=_get_int("x-ratelimit-used"),
    )

