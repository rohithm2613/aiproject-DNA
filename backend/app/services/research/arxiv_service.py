import logging
import xml.etree.ElementTree as ET
from typing import List, Optional
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

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"

class ArxivService(BaseResearchProvider):
    provider_name: str = "arxiv"
    API_URL: str = "https://export.arxiv.org/api/query"

    def __init__(self, timeout: Optional[float] = None):
        self.timeout = timeout or settings.RESEARCH_PROVIDER_TIMEOUT

    def _clean_query(self, query: str) -> str:
        """Sanitizes query text for arXiv search_query syntax."""
        # arXiv search supports field prefixes: all, ti, au, abs
        # Strip special characters that break arXiv API parser
        cleaned = "".join(c for c in query if c.isalnum() or c in (" ", "-", "_", "+"))
        terms = [t.strip() for t in cleaned.split() if t.strip()]
        if not terms:
            return "all:computer"
        # Search all fields with the terms
        return f"all:{' AND all:'.join(terms[:8])}"

    def parse_atom_feed(self, xml_content: str) -> List[ResearchPaperSchema]:
        """Parses arXiv Atom XML response into normalized ResearchPaperSchema objects."""
        papers: List[ResearchPaperSchema] = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as err:
            logger.warning(f"Failed to parse arXiv Atom XML: {err}")
            raise ProviderAPIError(f"Malformed XML response: {err}", self.provider_name)

        entries = root.findall(f"{ATOM_NS}entry")
        for entry in entries:
            try:
                # 1. ID and arXiv ID
                raw_id = entry.findtext(f"{ATOM_NS}id", default="")
                # arXiv ID is typically the last component of the URL
                arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id.split("/")[-1]
                arxiv_id = clean_text(arxiv_id) or "unknown"

                # 2. Title
                title = entry.findtext(f"{ATOM_NS}title", default="")
                title = clean_text(title)
                if not title:
                    continue  # Title is required

                # 3. Summary / Abstract
                abstract = entry.findtext(f"{ATOM_NS}summary", default="")
                abstract = clean_text(abstract)

                # 4. Authors
                author_elements = entry.findall(f"{ATOM_NS}author")
                authors: List[str] = []
                for auth in author_elements:
                    name = auth.findtext(f"{ATOM_NS}name")
                    if name:
                        authors.append(clean_text(name))

                # 5. Published date & year
                published = entry.findtext(f"{ATOM_NS}published")
                publication_date = clean_text(published)
                publication_year: Optional[int] = None
                if publication_date and len(publication_date) >= 4 and publication_date[:4].isdigit():
                    publication_year = int(publication_date[:4])

                # 6. Categories
                primary_cat = None
                prim_elem = entry.find(f"{ARXIV_NS}primary_category")
                if prim_elem is not None:
                    primary_cat = prim_elem.get("term")
                if not primary_cat:
                    cat_elem = entry.find(f"{ATOM_NS}category")
                    if cat_elem is not None:
                        primary_cat = cat_elem.get("term")

                # 7. Links: PDF and Abstract HTML
                paper_url = raw_id
                pdf_url = None
                for link in entry.findall(f"{ATOM_NS}link"):
                    link_type = link.get("type", "")
                    link_title = link.get("title", "")
                    link_rel = link.get("rel", "")
                    href = link.get("href", "")
                    if link_title == "pdf" or "pdf" in link_type:
                        pdf_url = href
                    elif link_rel == "alternate":
                        paper_url = href

                # If no direct PDF link found but we have arxiv_id, construct standard PDF link
                if not pdf_url and arxiv_id and arxiv_id != "unknown":
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

                # 8. DOI
                doi = entry.findtext(f"{ARXIV_NS}doi")
                doi = normalize_doi(doi)

                paper = ResearchPaperSchema(
                    provider=self.provider_name,
                    provider_paper_id=arxiv_id,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    publication_year=publication_year,
                    publication_date=publication_date,
                    venue=f"arXiv ({primary_cat})" if primary_cat else "arXiv",
                    doi=doi,
                    arxiv_id=arxiv_id,
                    citation_count=None,
                    paper_url=paper_url,
                    pdf_url=pdf_url,
                    open_access=True,  # arXiv is intrinsically open access
                    primary_category=primary_cat,
                )
                papers.append(paper)
            except Exception as e:
                logger.warning(f"Error parsing single arXiv entry: {e}")
                continue

        return papers

    async def search(self, query: str, max_results: int = 10) -> List[ResearchPaperSchema]:
        """Queries the official arXiv Atom API."""
        formatted_query = self._clean_query(query)
        params = {
            "search_query": formatted_query,
            "start": 0,
            "max_results": min(max_results, 50),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        headers = {
            "User-Agent": "AIProjectDNA/4.1 (Research Discovery Module; academic validation)",
            "Accept": "application/atom+xml, application/xml",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.API_URL, params=params, headers=headers)
                if response.status_code == 429:
                    raise ProviderRateLimitError("arXiv rate limit exceeded (HTTP 429)", self.provider_name, 429)
                if response.status_code >= 500:
                    raise ProviderAPIError(f"arXiv server error (HTTP {response.status_code})", self.provider_name, response.status_code)
                response.raise_for_status()

                return self.parse_atom_feed(response.text)
            except httpx.TimeoutException as exc:
                logger.warning(f"arXiv request timed out after {self.timeout}s")
                raise ProviderTimeoutError(f"arXiv request timed out ({exc})", self.provider_name)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    raise ProviderRateLimitError("arXiv rate limit reached", self.provider_name, 429)
                raise ProviderAPIError(f"arXiv HTTP error: {exc}", self.provider_name, exc.response.status_code)
            except (ProviderTimeoutError, ProviderRateLimitError, ProviderAPIError):
                raise
            except Exception as exc:
                logger.error(f"Unexpected arXiv service error: {exc}")
                raise ProviderAPIError(f"arXiv query failed: {exc}", self.provider_name)

