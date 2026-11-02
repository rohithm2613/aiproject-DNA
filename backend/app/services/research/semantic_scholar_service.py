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

class SemanticScholarService(BaseResearchProvider):
    provider_name: str = "semantic_scholar"
    API_URL: str = "https://api.semanticscholar.org/graph/v1/paper/search"
    DEFAULT_FIELDS: str = "paperId,title,abstract,authors,year,venue,externalIds,citationCount,openAccessPdf,url"

    def __init__(self, api_key: Optional[str] = None, timeout: Optional[float] = None):
        self.api_key = api_key or settings.SEMANTIC_SCHOLAR_API_KEY
        self.timeout = timeout or settings.RESEARCH_PROVIDER_TIMEOUT

    def parse_paper_item(self, item: Dict[str, Any]) -> Optional[ResearchPaperSchema]:
        """Parses a single paper JSON item from Semantic Scholar."""
        paper_id = item.get("paperId")
        if not paper_id:
            return None

        title = clean_text(item.get("title"))
        if not title:
            return None

        abstract = clean_text(item.get("abstract"))
        authors = clean_authors(item.get("authors"))
        year = item.get("year")
        venue = clean_text(item.get("venue"))
        citation_count = item.get("citationCount")

        # External IDs
        external_ids = item.get("externalIds") or {}
        doi = normalize_doi(external_ids.get("DOI") or external_ids.get("doi"))
        arxiv_id = clean_text(external_ids.get("ArXiv") or external_ids.get("arXiv") or external_ids.get("arxiv"))

        # Paper URL & PDF
        paper_url = item.get("url") or (f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else None)
        open_access_pdf = item.get("openAccessPdf")
        pdf_url = open_access_pdf.get("url") if isinstance(open_access_pdf, dict) else None
        open_access = bool(open_access_pdf)

        return ResearchPaperSchema(
            provider=self.provider_name,
            provider_paper_id=str(paper_id),
            title=title,
            abstract=abstract,
            authors=authors,
            publication_year=int(year) if year and str(year).isdigit() else None,
            publication_date=str(year) if year else None,
            venue=venue,
            doi=doi,
            arxiv_id=arxiv_id,
            citation_count=int(citation_count) if citation_count is not None else None,
            paper_url=paper_url,
            pdf_url=pdf_url,
            open_access=open_access,
            primary_category=None,
        )

    def parse_response(self, data: Dict[str, Any]) -> List[ResearchPaperSchema]:
        """Parses the entire Semantic Scholar search JSON payload."""
        papers: List[ResearchPaperSchema] = []
        raw_items = data.get("data", [])
        if not isinstance(raw_items, list):
            return papers

        for item in raw_items:
            try:
                parsed = self.parse_paper_item(item)
                if parsed:
                    papers.append(parsed)
            except Exception as e:
                logger.warning(f"Error parsing Semantic Scholar paper entry: {e}")
                continue

        return papers

    async def search(self, query: str, max_results: int = 10) -> List[ResearchPaperSchema]:
        """Queries Semantic Scholar Academic Graph API."""
        clean_q = clean_text(query)
        if not clean_q:
            return []

        # Limit query to avoid HTTP 400 URI length limits
        query_terms = clean_q.split()[:12]
        query_str = " ".join(query_terms)

        params = {
            "query": query_str,
            "limit": min(max_results, 50),
            "fields": self.DEFAULT_FIELDS,
        }

        headers: Dict[str, str] = {
            "User-Agent": "AIProjectDNA/4.1 (Research Discovery Module; academic validation)",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.API_URL, params=params, headers=headers)
                if response.status_code == 429:
                    raise ProviderRateLimitError(
                        "Semantic Scholar rate limit reached (HTTP 429). Please retry later or provide an API key.",
                        self.provider_name,
                        429
                    )
                if response.status_code >= 500:
                    raise ProviderAPIError(
                        f"Semantic Scholar server error (HTTP {response.status_code})",
                        self.provider_name,
                        response.status_code
                    )
                response.raise_for_status()

                data = response.json()
                return self.parse_response(data)
            except httpx.TimeoutException as exc:
                logger.warning(f"Semantic Scholar request timed out after {self.timeout}s")
                raise ProviderTimeoutError(f"Semantic Scholar request timed out ({exc})", self.provider_name)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    raise ProviderRateLimitError("Semantic Scholar rate limit reached", self.provider_name, 429)
                raise ProviderAPIError(f"Semantic Scholar HTTP error: {exc}", self.provider_name, exc.response.status_code)
            except (ProviderTimeoutError, ProviderRateLimitError, ProviderAPIError):
                raise
            except Exception as exc:
                logger.error(f"Unexpected Semantic Scholar error: {exc}")
                raise ProviderAPIError(f"Semantic Scholar query failed: {exc}", self.provider_name)

