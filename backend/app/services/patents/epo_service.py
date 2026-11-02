import base64
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
    PatentAuthError,
    normalize_publication_number,
    build_google_patents_url,
    clean_text,
    clean_list,
)

logger = logging.getLogger("uvicorn.error")

class EpoPatentService(BasePatentProvider):
    """
    Patent discovery provider for European Patent Office Open Patent Services (EPO OPS) v3.2.
    API Docs: https://www.epo.org/searching-for-patents/data/web-services/ops.html
    """

    provider_name: str = "epo"
    AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
    SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search"

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.consumer_key = settings.EPO_OPS_CONSUMER_KEY
        self.consumer_secret = settings.EPO_OPS_CONSUMER_SECRET
        self.timeout = settings.PATENT_PROVIDER_TIMEOUT
        self._client = client
        self._access_token: Optional[str] = None

    async def _get_auth_token(self, client: httpx.AsyncClient) -> Optional[str]:
        """Fetches an OAuth2 bearer access token using consumer key and secret."""
        if not self.consumer_key or not self.consumer_secret:
            logger.info("[EPO] Consumer key or secret not configured; skipping EPO OPS search.")
            return None

        if self._access_token:
            return self._access_token

        credentials = f"{self.consumer_key}:{self.consumer_secret}".encode("utf-8")
        basic_auth = base64.b64encode(credentials).decode("utf-8")

        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}

        try:
            resp = await client.post(self.AUTH_URL, headers=headers, data=data, timeout=self.timeout)
            if resp.status_code == 200:
                payload = resp.json()
                self._access_token = payload.get("access_token")
                return self._access_token
            logger.warning(f"[EPO] Authentication failed with HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        except Exception as exc:
            logger.warning(f"[EPO] Failed to fetch access token: {exc}")
            return None

    async def search(
        self,
        keywords: List[str],
        classifications: Optional[List[str]] = None,
        max_results: int = 15,
        jurisdiction: Optional[str] = None,
    ) -> List[PatentSchema]:
        """
        Executes a CQL search against EPO OPS published-data API.
        """
        if not keywords:
            return []

        if not self.consumer_key or not self.consumer_secret:
            logger.info("[EPO] Consumer key or secret not configured; skipping EPO OPS search.")
            return []

        should_close = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
            should_close = True

        try:
            token = await self._get_auth_token(client)
            if not token:
                # Without valid credentials, gracefully return empty
                return []

            # Format CQL query: e.g. ta="keyword1 keyword2"
            search_query_str = " ".join(keywords[:3])
            cql_query = f'ta="{search_query_str}"'

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            params = {
                "q": cql_query,
                "Range": f"1-{min(max_results, 25)}"
            }

            logger.info(f"[EPO] Querying OPS with CQL: {cql_query}")
            response = await client.get(self.SEARCH_URL, headers=headers, params=params)

            if response.status_code == 429:
                logger.warning("[EPO] OPS rate limit exceeded (429)")
                raise PatentRateLimitError("EPO OPS rate limit exceeded", provider=self.provider_name, status_code=429)

            if response.status_code >= 500:
                logger.warning(f"[EPO] OPS server error: {response.status_code}")
                raise PatentAPIError(f"EPO OPS server error: {response.status_code}", provider=self.provider_name, status_code=response.status_code)

            if response.status_code != 200:
                logger.warning(f"[EPO] OPS returned status {response.status_code}: {response.text[:200]}")
                return []

            data = response.json()
            return self._parse_epo_response(data)

        except httpx.TimeoutException as exc:
            logger.warning(f"[EPO] Request timed out: {exc}")
            raise PatentTimeoutError("EPO OPS request timed out", provider=self.provider_name)
        except (PatentRateLimitError, PatentTimeoutError, PatentAPIError):
            raise
        except Exception as exc:
            logger.error(f"[EPO] Error querying EPO OPS: {exc}", exc_info=True)
            return []
        finally:
            if should_close:
                await client.aclose()

    def _parse_epo_response(self, data: Dict[str, Any]) -> List[PatentSchema]:
        """Parses OPS JSON response structure into normalized PatentSchema objects."""
        results: List[PatentSchema] = []
        try:
            search_result = (
                data.get("ops:world-patent-data", {})
                .get("ops:biblio-search", {})
                .get("ops:search-result", {})
            )
            publications = search_result.get("ops:publication-reference", [])
            if isinstance(publications, dict):
                publications = [publications]

            for pub in publications:
                doc_id = pub.get("document-id", {})
                country = doc_id.get("country", {}).get("$", "EP")
                doc_number = doc_id.get("doc-number", {}).get("$", "")
                kind = doc_id.get("kind", {}).get("$", "")
                date_val = doc_id.get("date", {}).get("$", "")

                if not doc_number:
                    continue

                raw_pub_num = f"{country}{doc_number}{kind}".strip()
                pub_num_clean = normalize_publication_number(raw_pub_num)

                schema = PatentSchema(
                    provider=self.provider_name,
                    provider_patent_id=pub_num_clean,
                    publication_number=pub_num_clean,
                    application_number=None,
                    patent_number=str(doc_number),
                    title=f"Patent {pub_num_clean}",
                    abstract=None,
                    description=None,
                    claims=[],
                    inventors=[],
                    assignees=[],
                    filing_date=None,
                    publication_date=str(date_val) if date_val else None,
                    grant_date=None,
                    jurisdiction=country,
                    patent_type="Utility",
                    cpc_classifications=[],
                    ipc_classifications=[],
                    legal_status="Published",
                    source_url=build_google_patents_url(pub_num_clean)
                )
                results.append(schema)

        except Exception as exc:
            logger.warning(f"[EPO] Failed to parse OPS response: {exc}")

        return results

