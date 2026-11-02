import logging
from typing import List, Optional, Dict, Any
import httpx
from app.core.config import settings
from app.schemas.research import ResearchPaperSchema
from app.services.research.base import (
    BaseResearchProvider,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderAPIError,
    normalize_doi,
    clean_text,
    clean_authors,
)

logger = logging.getLogger("uvicorn.error")

class OpenAlexService(BaseResearchProvider):
    provider_name: str = "openalex"
    API_URL: str = "https://api.openalex.org/works"

    def __init__(self, email: Optional[str] = None, timeout: Optional[float] = None):
        self.email = email or settings.OPENALEX_EMAIL
        self.timeout = timeout or settings.RESEARCH_PROVIDER_TIMEOUT

    @staticmethod
    def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
        """
        Reconstructs plain text abstract from OpenAlex's abstract_inverted_index format.
        Format: {"Word": [pos1, pos2], "Another": [pos3]}
        """
        if not inverted_index or not isinstance(inverted_index, dict):
            return None

        word_positions: List[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            if isinstance(positions, list):
                for pos in positions:
                    if isinstance(pos, int) and pos >= 0:
                        word_positions.append((pos, word))

        if not word_positions:
            return None

        # Sort by index position
        word_positions.sort(key=lambda x: x[0])
        words = [w for _, w in word_positions]
        return clean_text(" ".join(words))

    def parse_work_item(self, item: Dict[str, Any]) -> Optional[ResearchPaperSchema]:
        """Parses a single OpenAlex Work object into normalized ResearchPaperSchema."""
        raw_id = item.get("id")
        if not raw_id:
            return None

        # Extract Work ID from full URL (e.g. 'https://openalex.org/W2741809807' -> 'W2741809807')
        work_id = str(raw_id).split("/")[-1] if "/" in str(raw_id) else str(raw_id)

        title = clean_text(item.get("title") or item.get("display_name"))
        if not title:
            return None

        # Reconstruct abstract from inverted index
        abstract = self.reconstruct_abstract(item.get("abstract_inverted_index"))

        # Authors
        authors: List[str] = []
        authorships = item.get("authorships") or []
        for auth_entry in authorships:
            author_obj = auth_entry.get("author") or {}
            name = author_obj.get("display_name")
            if name:
                cleaned_name = clean_text(name)
                if cleaned_name:
                    authors.append(cleaned_name)

        # Dates & Year
        publication_year = item.get("publication_year")
        publication_date = item.get("publication_date")

        # Primary location / venue / URLs
        primary_location = item.get("primary_location") or {}
        source = primary_location.get("source") or {}
        venue = clean_text(source.get("display_name"))

        landing_page_url = primary_location.get("landing_page_url") or item.get("doi") or str(raw_id)
        pdf_url = primary_location.get("pdf_url")

        # Open access details
        oa_info = item.get("open_access") or {}
        open_access = oa_info.get("is_oa") or primary_location.get("is_oa") or False
        if not pdf_url and oa_info.get("oa_url"):
            pdf_url = oa_info.get("oa_url")

        # Citations & Topic
        citation_count = item.get("cited_by_count")
        primary_topic_obj = item.get("primary_topic") or {}
        primary_category = clean_text(primary_topic_obj.get("display_name"))

        doi = normalize_doi(item.get("doi"))

        return ResearchPaperSchema(
            provider=self.provider_name,
            provider_paper_id=work_id,
            title=title,
            abstract=abstract,
            authors=authors,
            publication_year=int(publication_year) if publication_year else None,
            publication_date=str(publication_date) if publication_date else None,
            venue=venue,
            doi=doi,
            arxiv_id=None,
            citation_count=int(citation_count) if citation_count is not None else None,
            paper_url=landing_page_url,
            pdf_url=pdf_url,
            open_access=bool(open_access),
            primary_category=primary_category,
        )

    def parse_response(self, data: Dict[str, Any]) -> List[ResearchPaperSchema]:
        """Parses OpenAlex works search response."""
        papers: List[ResearchPaperSchema] = []
        results = data.get("results", [])
        if not isinstance(results, list):
            return papers

        for item in results:
            try:
                parsed = self.parse_work_item(item)
                if parsed:
                    papers.append(parsed)
            except Exception as e:
                logger.warning(f"Error parsing OpenAlex work entry: {e}")
                continue

        return papers

    async def search(self, query: str, max_results: int = 10) -> List[ResearchPaperSchema]:
        """Queries OpenAlex API for research works."""
        clean_q = clean_text(query)
        if not clean_q:
            return []

        # OpenAlex performs best with clean, focused keyword strings
        query_terms = clean_q.split()[:10]
        query_str = " ".join(query_terms)

        params: Dict[str, Any] = {
            "search": query_str,
            "per-page": min(max_results, 50),
        }
        if self.email:
            params["mailto"] = self.email

        headers = {
            "User-Agent": f"AIProjectDNA/4.1 (Research Discovery Module; mailto:{self.email or 'admin@projectdna.local'})",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.API_URL, params=params, headers=headers)
                if response.status_code == 429:
                    raise ProviderRateLimitError(
                        "OpenAlex rate limit exceeded (HTTP 429).",
                        self.provider_name,
                        429
                    )
                if response.status_code >= 500:
                    raise ProviderAPIError(
                        f"OpenAlex server error (HTTP {response.status_code})",
                        self.provider_name,
                        response.status_code
                    )
                response.raise_for_status()

                data = response.json()
                return self.parse_response(data)
            except httpx.TimeoutException as exc:
                logger.warning(f"OpenAlex request timed out after {self.timeout}s")
                raise ProviderTimeoutError(f"OpenAlex request timed out ({exc})", self.provider_name)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    raise ProviderRateLimitError("OpenAlex rate limit reached", self.provider_name, 429)
                raise ProviderAPIError(f"OpenAlex HTTP error: {exc}", self.provider_name, exc.response.status_code)
            except (ProviderTimeoutError, ProviderRateLimitError, ProviderAPIError):
                raise
            except Exception as exc:
                logger.error(f"Unexpected OpenAlex error: {exc}")
                raise ProviderAPIError(f"OpenAlex query failed: {exc}", self.provider_name)

