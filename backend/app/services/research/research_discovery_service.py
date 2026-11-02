import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.research_paper import ResearchPaper
from app.schemas.research import (
    ResearchPaperSchema,
    ResearchSearchResponse,
    ResearchStatsResponse,
    ResearchListResponse,
)
from app.services.research.arxiv_service import ArxivService
from app.services.research.semantic_scholar_service import SemanticScholarService
from app.services.research.openalex_service import OpenAlexService
from app.services.research.query_generator import generate_research_queries
from app.services.research.base import (
    BaseResearchProvider,
    ResearchProviderError,
    normalize_doi,
)

logger = logging.getLogger("uvicorn.error")

class ResearchDiscoveryService:
    """
    Coordinates multi-provider academic research discovery across arXiv, Semantic Scholar,
    and OpenAlex. Handles query generation, concurrent requests, deduplication,
    and database persistence.
    """

    def __init__(
        self,
        arxiv_service: Optional[ArxivService] = None,
        semantic_scholar_service: Optional[SemanticScholarService] = None,
        openalex_service: Optional[OpenAlexService] = None,
    ):
        self.arxiv_service = arxiv_service or ArxivService()
        self.semantic_scholar_service = semantic_scholar_service or SemanticScholarService()
        self.openalex_service = openalex_service or OpenAlexService()

    def _get_provider_map(self) -> Dict[str, BaseResearchProvider]:
        return {
            "arxiv": self.arxiv_service,
            "semantic_scholar": self.semantic_scholar_service,
            "openalex": self.openalex_service,
        }

    async def _query_single_provider(
        self,
        provider_name: str,
        provider: BaseResearchProvider,
        queries: List[str],
        max_results_per_provider: int,
    ) -> Tuple[str, List[ResearchPaperSchema], Optional[str]]:
        """Queries a single provider across generated queries, aggregating unique results."""
        provider_papers: List[ResearchPaperSchema] = []
        error_msg: Optional[str] = None
        seen_ids = set()

        for q in queries:
            try:
                results = await provider.search(q, max_results=max_results_per_provider)
                for paper in results:
                    pid = paper.provider_paper_id
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        provider_papers.append(paper)
                        if len(provider_papers) >= max_results_per_provider:
                            break
                if len(provider_papers) >= max_results_per_provider:
                    break
            except ResearchProviderError as rpe:
                logger.warning(f"Provider {provider_name} search error: {rpe.message}")
                error_msg = rpe.message
                break
            except Exception as exc:
                logger.warning(f"Unexpected error in provider {provider_name}: {exc}")
                error_msg = str(exc)
                break

        return provider_name, provider_papers, error_msg

    def deduplicate_papers(
        self,
        new_papers: List[ResearchPaperSchema],
        existing_papers: List[ResearchPaper],
    ) -> Tuple[List[ResearchPaperSchema], int]:
        """
        Deduplicates incoming papers against both existing DB records and each other.
        Uses:
          1. Exact (provider, provider_paper_id) match
          2. Verified DOI match (case-insensitive normalized)
          3. Clean arXiv ID match
        Does NOT collapse papers merely because titles look similar.
        """
        # Collect existing keys
        existing_provider_keys = {
            (ep.provider, str(ep.provider_paper_id)) for ep in existing_papers
        }
        existing_dois = {
            normalize_doi(ep.doi) for ep in existing_papers if ep.doi
        }
        existing_arxiv_ids = {
            ep.arxiv_id.strip().lower() for ep in existing_papers if ep.arxiv_id
        }

        unique_to_insert: List[ResearchPaperSchema] = []
        duplicates_skipped = 0

        # Also track keys within the current batch to avoid batch duplicates
        batch_provider_keys = set()
        batch_dois = set()
        batch_arxiv_ids = set()

        for p in new_papers:
            p_prov_key = (p.provider, str(p.provider_paper_id))
            p_doi = normalize_doi(p.doi)
            p_arxiv = p.arxiv_id.strip().lower() if p.arxiv_id else None

            is_duplicate = False

            # 1. Check provider + paper id
            if p_prov_key in existing_provider_keys or p_prov_key in batch_provider_keys:
                is_duplicate = True

            # 2. Check DOI match if present
            if not is_duplicate and p_doi and (p_doi in existing_dois or p_doi in batch_dois):
                is_duplicate = True

            # 3. Check arXiv ID match if present
            if not is_duplicate and p_arxiv and (p_arxiv in existing_arxiv_ids or p_arxiv in batch_arxiv_ids):
                is_duplicate = True

            if is_duplicate:
                duplicates_skipped += 1
            else:
                unique_to_insert.append(p)
                batch_provider_keys.add(p_prov_key)
                if p_doi:
                    batch_dois.add(p_doi)
                if p_arxiv:
                    batch_arxiv_ids.add(p_arxiv)

        return unique_to_insert, duplicates_skipped

    async def search_and_persist(
        self,
        db: Session,
        project: Project,
        user_id: str,
        analysis_id: Optional[str] = None,
        max_results: int = 20,
        selected_providers: Optional[List[str]] = None,
    ) -> ResearchSearchResponse:
        """
        Full orchestration of academic discovery:
          1. Resolve latest or specified Phase 3 analysis.
          2. Generate focused search queries.
          3. Concurrently query active providers.
          4. Deduplicate results.
          5. Save new records to database.
          6. Return comprehensive search response.
        """
        # 1. Resolve analysis
        target_analysis: Optional[ProjectAnalysis] = None
        if analysis_id:
            target_analysis = db.query(ProjectAnalysis).filter(
                ProjectAnalysis.id == analysis_id,
                ProjectAnalysis.project_id == project.id,
            ).first()
        else:
            target_analysis = db.query(ProjectAnalysis).filter(
                ProjectAnalysis.project_id == project.id
            ).order_by(desc(ProjectAnalysis.version)).first()

        resolved_analysis_id = target_analysis.id if target_analysis else None

        # 2. Generate queries
        queries = generate_research_queries(project, target_analysis, max_queries=3)

        # 3. Select active providers
        provider_map = self._get_provider_map()
        if selected_providers:
            active_providers = {
                p: provider_map[p] for p in selected_providers if p in provider_map
            }
        else:
            active_providers = provider_map

        if not active_providers:
            active_providers = provider_map

        # 4. Concurrent execution across providers
        tasks = [
            self._query_single_provider(name, prov, queries, max_results)
            for name, prov in active_providers.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        provider_counts: Dict[str, int] = {}
        provider_errors: Dict[str, str] = {}
        all_retrieved_papers: List[ResearchPaperSchema] = []

        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Async provider task exception: {res}")
                continue
            prov_name, papers, err = res
            provider_counts[prov_name] = len(papers)
            if err:
                provider_errors[prov_name] = err
            all_retrieved_papers.extend(papers)

        # Determine overall status
        successful_providers = [p for p, c in provider_counts.items() if c > 0]
        if not successful_providers and provider_errors:
            status = "failed"
        elif len(provider_errors) > 0:
            status = "partial_success"
        else:
            status = "completed"

        # 5. Fetch existing papers for this project to deduplicate
        existing_papers = db.query(ResearchPaper).filter(
            ResearchPaper.project_id == project.id
        ).all()

        unique_papers, duplicates_skipped = self.deduplicate_papers(
            all_retrieved_papers,
            existing_papers
        )

        # 6. Persist unique papers to database
        newly_inserted_count = 0
        now_dt = datetime.now(timezone.utc)
        for p in unique_papers:
            db_paper = ResearchPaper(
                project_id=project.id,
                analysis_id=resolved_analysis_id,
                user_id=user_id,
                provider=p.provider,
                provider_paper_id=p.provider_paper_id,
                title=p.title,
                abstract=p.abstract,
                authors=p.authors or [],
                publication_year=p.publication_year,
                publication_date=p.publication_date,
                venue=p.venue,
                doi=p.doi,
                arxiv_id=p.arxiv_id,
                citation_count=p.citation_count,
                paper_url=p.paper_url,
                pdf_url=p.pdf_url,
                open_access=p.open_access,
                primary_category=p.primary_category,
                retrieved_at=now_dt,
            )
            db.add(db_paper)
            newly_inserted_count += 1

        if newly_inserted_count > 0:
            db.commit()

        # 7. Fetch all stored papers for this project to return in response
        stored_papers_query = db.query(ResearchPaper).filter(
            ResearchPaper.project_id == project.id
        ).order_by(desc(ResearchPaper.retrieved_at), desc(ResearchPaper.publication_year))

        total_stored = stored_papers_query.count()
        recent_papers_db = stored_papers_query.limit(50).all()

        response_papers = [
            ResearchPaperSchema(
                id=rp.id,
                project_id=rp.project_id,
                analysis_id=rp.analysis_id,
                user_id=rp.user_id,
                provider=rp.provider,
                provider_paper_id=rp.provider_paper_id,
                title=rp.title,
                abstract=rp.abstract,
                authors=rp.authors or [],
                publication_year=rp.publication_year,
                publication_date=rp.publication_date,
                venue=rp.venue,
                doi=rp.doi,
                arxiv_id=rp.arxiv_id,
                citation_count=rp.citation_count,
                paper_url=rp.paper_url,
                pdf_url=rp.pdf_url,
                open_access=rp.open_access,
                primary_category=rp.primary_category,
                retrieved_at=rp.retrieved_at,
                created_at=rp.created_at,
            )
            for rp in recent_papers_db
        ]

        return ResearchSearchResponse(
            status=status,
            project_id=project.id,
            analysis_id=resolved_analysis_id,
            queries_executed=queries,
            provider_counts=provider_counts,
            new_stored=newly_inserted_count,
            duplicates_skipped=duplicates_skipped,
            provider_errors=provider_errors,
            total_stored_papers=total_stored,
            papers=response_papers,
        )

    def get_stored_papers(
        self,
        db: Session,
        project_id: str,
        provider: Optional[str] = None,
        year: Optional[int] = None,
        open_access: Optional[bool] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ResearchListResponse:
        """Retrieves stored research papers for a project with optional filters and pagination."""
        query = db.query(ResearchPaper).filter(ResearchPaper.project_id == project_id)

        if provider:
            query = query.filter(ResearchPaper.provider == provider)

        if year:
            query = query.filter(ResearchPaper.publication_year == year)

        if open_access is not None:
            query = query.filter(ResearchPaper.open_access == open_access)

        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    ResearchPaper.title.ilike(term),
                    ResearchPaper.abstract.ilike(term),
                    ResearchPaper.venue.ilike(term),
                )
            )

        total = query.count()
        offset = max(0, (page - 1) * page_size)
        db_items = query.order_by(
            desc(ResearchPaper.retrieved_at),
            desc(ResearchPaper.publication_year)
        ).offset(offset).limit(page_size).all()

        items = [
            ResearchPaperSchema(
                id=p.id,
                project_id=p.project_id,
                analysis_id=p.analysis_id,
                user_id=p.user_id,
                provider=p.provider,
                provider_paper_id=p.provider_paper_id,
                title=p.title,
                abstract=p.abstract,
                authors=p.authors or [],
                publication_year=p.publication_year,
                publication_date=p.publication_date,
                venue=p.venue,
                doi=p.doi,
                arxiv_id=p.arxiv_id,
                citation_count=p.citation_count,
                paper_url=p.paper_url,
                pdf_url=p.pdf_url,
                open_access=p.open_access,
                primary_category=p.primary_category,
                retrieved_at=p.retrieved_at,
                created_at=p.created_at,
            )
            for p in db_items
        ]

        return ResearchListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        )

    def get_research_stats(self, db: Session, project_id: str) -> ResearchStatsResponse:
        """Computes summary statistics for stored papers of a given project."""
        papers = db.query(ResearchPaper).filter(ResearchPaper.project_id == project_id).all()

        by_provider: Dict[str, int] = {}
        year_distribution: Dict[str, int] = {}
        oa_count = 0
        latest_retrieved: Optional[datetime] = None

        for p in papers:
            by_provider[p.provider] = by_provider.get(p.provider, 0) + 1
            if p.open_access:
                oa_count += 1
            if p.publication_year:
                y_str = str(p.publication_year)
                year_distribution[y_str] = year_distribution.get(y_str, 0) + 1
            if p.retrieved_at:
                if not latest_retrieved or p.retrieved_at > latest_retrieved:
                    latest_retrieved = p.retrieved_at

        return ResearchStatsResponse(
            project_id=project_id,
            total_papers=len(papers),
            by_provider=by_provider,
            open_access_count=oa_count,
            year_distribution=year_distribution,
            most_recent_retrieval=latest_retrieved.isoformat() if latest_retrieved else None,
        )

research_discovery_service = ResearchDiscoveryService()

