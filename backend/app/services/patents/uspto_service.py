import json
import logging
from typing import List, Optional, Dict, Any
import httpx
from app.core.config import settings
from app.schemas.patent import PatentSchema
from app.services.patents.base import (
    BasePatentProvider,
    PatentTimeoutError,
    PatentRateLimitError,
    PatentAPIError,
    normalize_publication_number,
    build_google_patents_url,
    clean_text,
    clean_list,
)

logger = logging.getLogger("uvicorn.error")

class UsptoPatentService(BasePatentProvider):
    """
    Patent discovery provider for USPTO Open Data / PatentsView REST API.
    API Docs: https://patentsview.org/apis/api-endpoints/patents
    """

    provider_name: str = "uspto"

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.api_url = settings.USPTO_API_URL or "https://api.patentsview.org/patents/query"
        self.api_key = settings.USPTO_API_KEY
        self.timeout = settings.PATENT_PROVIDER_TIMEOUT
        self._client = client

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "AI-ProjectDNA-PatentDiscovery/1.0"
        }
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers

    async def search(
        self,
        keywords: List[str],
        classifications: Optional[List[str]] = None,
        max_results: int = 15,
        jurisdiction: Optional[str] = None,
    ) -> List[PatentSchema]:
        """
        Executes a PatentsView query based on keywords and optional CPC classifications.
        """
        if not keywords:
            return []

        search_query_str = " ".join(keywords[:4])

        # PatentsView query format: JSON object
        # Searching title or abstract
        query_payload = {
            "_or": [
                {"_text_phrase": {"patent_title": search_query_str}},
                {"_text_any": {"patent_abstract": search_query_str}},
            ]
        }

        fields = [
            "patent_id",
            "patent_number",
            "patent_title",
            "patent_abstract",
            "patent_date",
            "app_date",
            "cpc_subgroup_id",
            "assignee_organization",
            "inventor_first_name",
            "inventor_last_name"
        ]

        params = {
            "q": json.dumps(query_payload),
            "f": json.dumps(fields),
            "o": json.dumps({"per_page": min(max_results, 50)}),
            "s": json.dumps([{"patent_date": "desc"}])
        }

        should_close = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
            should_close = True

        try:
            logger.info(f"[USPTO] Querying PatentsView with: {search_query_str}")
            response = await client.get(self.api_url, params=params, headers=self._build_headers())

            if response.status_code == 429:
                logger.warning("[USPTO] PatentsView API rate limit exceeded (429)")
                raise PatentRateLimitError("USPTO PatentsView rate limit exceeded", provider=self.provider_name, status_code=429)

            if response.status_code >= 500:
                logger.warning(f"[USPTO] PatentsView API server error: {response.status_code}")
                raise PatentAPIError(f"USPTO PatentsView server error: {response.status_code}", provider=self.provider_name, status_code=response.status_code)

            if response.status_code != 200:
                logger.warning(f"[USPTO] PatentsView returned unexpected status: {response.status_code} - {response.text[:200]}")
                return []

            data = response.json()
            patents_list = data.get("patents") or []
            return self._parse_patents(patents_list)

        except httpx.TimeoutException as exc:
            logger.warning(f"[USPTO] Request timed out: {exc}")
            raise PatentTimeoutError("USPTO PatentsView request timed out", provider=self.provider_name)
        except (PatentRateLimitError, PatentTimeoutError, PatentAPIError):
            raise
        except Exception as exc:
            logger.error(f"[USPTO] Unexpected error during patent search: {exc}", exc_info=True)
            return []
        finally:
            if should_close:
                await client.aclose()

    def _parse_patents(self, raw_patents: List[Dict[str, Any]]) -> List[PatentSchema]:
        """Transforms USPTO PatentsView JSON response into normalized PatentSchema objects."""
        results: List[PatentSchema] = []

        for p in raw_patents:
            if not isinstance(p, dict):
                continue

            raw_num = p.get("patent_number") or p.get("patent_id")
            if not raw_num:
                continue

            # Standardize publication number (US + number)
            pub_num_clean = normalize_publication_number(str(raw_num))
            if not pub_num_clean.startswith("US"):
                pub_num_clean = f"US{pub_num_clean}"

            title = clean_text(p.get("patent_title")) or "Untitled Patent"
            abstract = clean_text(p.get("patent_abstract"))

            # Inventors
            inventors: List[str] = []
            for inv in (p.get("inventors") or []):
                if isinstance(inv, dict):
                    first = clean_text(inv.get("inventor_first_name")) or ""
                    last = clean_text(inv.get("inventor_last_name")) or ""
                    name = f"{first} {last}".strip()
                    if name and name not in inventors:
                        inventors.append(name)

            # Assignees
            assignees: List[str] = []
            for asg in (p.get("assignees") or []):
                if isinstance(asg, dict):
                    org = clean_text(asg.get("assignee_organization"))
                    if org and org not in assignees:
                        assignees.append(org)

            # CPC classifications
            cpc_list: List[str] = []
            for cpc in (p.get("cpcs") or []):
                if isinstance(cpc, dict):
                    code = clean_text(cpc.get("cpc_subgroup_id"))
                    if code and code not in cpc_list:
                        cpc_list.append(code)

            pub_date = p.get("patent_date")
            app_date = p.get("app_date")

            schema = PatentSchema(
                provider=self.provider_name,
                provider_patent_id=str(p.get("patent_id") or raw_num),
                publication_number=pub_num_clean,
                application_number=str(app_date) if app_date else None,
                patent_number=str(raw_num),
                title=title,
                abstract=abstract,
                description=None,
                claims=[],
                inventors=inventors,
                assignees=assignees,
                filing_date=str(app_date) if app_date else None,
                publication_date=str(pub_date) if pub_date else None,
                grant_date=str(pub_date) if pub_date else None,
                jurisdiction="US",
                patent_type="Utility",
                cpc_classifications=cpc_list,
                ipc_classifications=[],
                legal_status="Granted",
                source_url=build_google_patents_url(pub_num_clean)
            )
            results.append(schema)

        return results

