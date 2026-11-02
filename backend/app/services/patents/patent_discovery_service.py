import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from app.core.config import settings
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.patent import Patent
from app.schemas.patent import (
    PatentSchema,
    PatentSearchResponse,
    PatentListResponse,
    PatentStatsResponse,
    PatentEvidenceManifestItem,
    LEGAL_DISCLAIMER,
)
from app.services.patents.base import (
    BasePatentProvider,
    PatentProviderError,
    normalize_publication_number,
    extract_jurisdiction,
    build_google_patents_url,
)
from app.services.patents.uspto_service import UsptoPatentService
from app.services.patents.epo_service import EpoPatentService
from app.services.patents.patent_query_generator import PatentQueryGenerator
from app.services.patents.patent_embedding_service import PatentEmbeddingService

logger = logging.getLogger("uvicorn.error")

class PatentDiscoveryService:
    """
    Coordinates patent and prior-art discovery across USPTO Open Data and EPO OPS,
    handling query generation, deduplication, persistence, embedding generation,
    and statistics.
    """

    def __init__(
        self,
        uspto_service: Optional[UsptoPatentService] = None,
        epo_service: Optional[EpoPatentService] = None,
    ):
        self.uspto_service = uspto_service or UsptoPatentService()
        self.epo_service = epo_service or EpoPatentService()

    def _get_provider_map(self) -> Dict[str, BasePatentProvider]:
        return {
            "uspto": self.uspto_service,
            "epo": self.epo_service,
        }

    async def _query_single_provider(
        self,
        provider_name: str,
        provider: BasePatentProvider,
        keywords: List[str],
        classifications: List[str],
        max_results_per_provider: int,
    ) -> Tuple[str, List[PatentSchema], Optional[str]]:
        """Queries a single provider safely, returning results and optional error message."""
        try:
            results = await provider.search(
                keywords=keywords,
                classifications=classifications,
                max_results=max_results_per_provider
            )
            return provider_name, results, None
        except PatentProviderError as ppe:
            logger.warning(f"Provider {provider_name} search error: {ppe.message}")
            return provider_name, [], ppe.message
        except Exception as exc:
            logger.error(f"Unexpected error in provider {provider_name}: {exc}", exc_info=True)
            return provider_name, [], str(exc)

    def deduplicate_patents(
        self,
        new_patents: List[PatentSchema],
        existing_patents: List[Patent],
    ) -> Tuple[List[PatentSchema], int]:
        """
        Deduplicates incoming patents against existing database records and each other
        using normalized publication numbers.
        """
        seen_pub_numbers = set()
        for p in existing_patents:
            norm_num = normalize_publication_number(p.publication_number)
            if norm_num:
                seen_pub_numbers.add(norm_num)

        unique_new: List[PatentSchema] = []
        duplicates_count = 0

        for pat in new_patents:
            clean_num = normalize_publication_number(pat.publication_number)
            if not clean_num:
                continue

            if clean_num in seen_pub_numbers:
                duplicates_count += 1
            else:
                seen_pub_numbers.add(clean_num)
                pat.publication_number = clean_num
                unique_new.append(pat)

        return unique_new, duplicates_count

    async def search_and_persist_patents(
        self,
        db: Session,
        project_id: str,
        user_id: str,
        analysis_id: Optional[str] = None,
        max_results: int = 25,
        providers: Optional[List[str]] = None,
        jurisdictions: Optional[List[str]] = None,
        query_override: Optional[str] = None,
    ) -> PatentSearchResponse:
        """
        Executes patent discovery across configured providers, deduplicates,
        stores in database, and triggers embedding generation.
        """
        # 1. Fetch Project & Analysis
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project with ID '{project_id}' not found.")

        analysis = None
        if analysis_id:
            analysis = db.query(ProjectAnalysis).filter(
                ProjectAnalysis.id == analysis_id,
                ProjectAnalysis.project_id == project_id
            ).first()
        else:
            analysis = db.query(ProjectAnalysis).filter(
                ProjectAnalysis.project_id == project_id
            ).order_by(ProjectAnalysis.version.desc()).first()

        analysis_dict: Dict[str, Any] = {
            "project_title": project.title,
            "primary_domain": project.domain,
            "user_technologies": project.technologies or [],
            "keywords": [],
            "secondary_domains": [],
        }
        if analysis:
            analysis_dict["keywords"] = analysis.keywords or []
            analysis_dict["secondary_domains"] = analysis.secondary_domains or []
            if analysis.primary_domain:
                analysis_dict["primary_domain"] = analysis.primary_domain
            if analysis.user_technologies:
                analysis_dict["user_technologies"] = analysis.user_technologies

        # 2. Generate Queries and Classifications
        query_info = PatentQueryGenerator.generate_queries(analysis_dict, query_override=query_override)
        keywords = query_info["primary_keywords"]
        classifications = query_info["cpc_codes"]
        search_queries = query_info["search_queries"]

        # 3. Determine Providers
        provider_map = self._get_provider_map()
        target_provider_names = providers or ["uspto", "epo"]
        valid_providers = {name: provider_map[name] for name in target_provider_names if name in provider_map}

        # 4. Query Providers Concurrently
        tasks = [
            self._query_single_provider(
                name,
                prov,
                keywords=keywords,
                classifications=classifications,
                max_results_per_provider=max_results,
            )
            for name, prov in valid_providers.items()
        ]

        query_results = await asyncio.gather(*tasks)

        all_retrieved: List[PatentSchema] = []
        provider_counts: Dict[str, int] = {}
        provider_errors: Dict[str, str] = {}

        for pname, plist, perr in query_results:
            provider_counts[pname] = len(plist)
            if perr:
                provider_errors[pname] = perr
            all_retrieved.extend(plist)

        # 5. Fetch existing patents for deduplication
        existing_patents = db.query(Patent).filter(Patent.project_id == project_id).all()
        unique_to_save, duplicates_skipped = self.deduplicate_patents(all_retrieved, existing_patents)

        # 6. Apply Jurisdiction Filter if requested
        if jurisdictions:
            jur_set = {j.upper() for j in jurisdictions}
            unique_to_save = [p for p in unique_to_save if (p.jurisdiction or "").upper() in jur_set]

        # 7. Persist New Records
        new_stored = 0
        persisted_records: List[Patent] = []
        for p_schema in unique_to_save:
            clean_pub = normalize_publication_number(p_schema.publication_number)
            jur = p_schema.jurisdiction or extract_jurisdiction(clean_pub)
            google_url = p_schema.source_url or build_google_patents_url(clean_pub)

            patent_record = Patent(
                project_id=project_id,
                analysis_id=analysis.id if analysis else None,
                user_id=user_id,
                provider=p_schema.provider,
                provider_patent_id=p_schema.provider_patent_id,
                publication_number=clean_pub,
                application_number=p_schema.application_number,
                patent_number=p_schema.patent_number,
                title=p_schema.title,
                abstract=p_schema.abstract,
                description=p_schema.description,
                claims=p_schema.claims or [],
                inventors=p_schema.inventors or [],
                assignees=p_schema.assignees or [],
                filing_date=p_schema.filing_date,
                publication_date=p_schema.publication_date,
                grant_date=p_schema.grant_date,
                priority_date=p_schema.priority_date,
                jurisdiction=jur,
                patent_type=p_schema.patent_type or "Utility",
                cpc_classifications=p_schema.cpc_classifications or [],
                ipc_classifications=p_schema.ipc_classifications or [],
                patent_family_id=p_schema.patent_family_id,
                legal_status=p_schema.legal_status or "Granted",
                source_url=google_url,
                raw_metadata={},
            )
            db.add(patent_record)
            persisted_records.append(patent_record)
            new_stored += 1

        if new_stored > 0:
            db.commit()
            for rec in persisted_records:
                db.refresh(rec)

        # 8. Generate Vector Embeddings and Cosine Similarities
        embedding_service = PatentEmbeddingService(db)
        all_patents = db.query(Patent).filter(Patent.project_id == project_id).all()
        embedding_service.ensure_patent_embeddings(project_id, all_patents)

        # 9. Return Schema Items with Similarities
        all_schemas = [PatentSchema.model_validate(p.to_dict()) for p in all_patents]
        enriched_schemas = embedding_service.populate_schema_similarities(project_id, all_schemas, all_patents)

        # Sort by similarity score descending
        enriched_schemas.sort(key=lambda s: s.similarity_score or 0.0, reverse=True)

        status = "completed"
        if provider_errors and new_stored > 0:
            status = "partial_success"
        elif provider_errors and new_stored == 0 and not existing_patents:
            status = "failed"

        return PatentSearchResponse(
            status=status,
            project_id=project_id,
            analysis_id=analysis.id if analysis else None,
            queries_executed=search_queries,
            provider_counts=provider_counts,
            new_stored=new_stored,
            duplicates_skipped=duplicates_skipped,
            provider_errors=provider_errors,
            total_stored_patents=len(all_patents),
            patents=enriched_schemas[:max_results],
            disclaimer=LEGAL_DISCLAIMER
        )

    def get_patents(
        self,
        db: Session,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
        jurisdiction: Optional[str] = None,
        provider: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "similarity",
    ) -> PatentListResponse:
        """Retrieves paginated and filtered patents for a project."""
        query = db.query(Patent).filter(Patent.project_id == project_id)

        if jurisdiction and jurisdiction.lower() != "all":
            query = query.filter(Patent.jurisdiction == jurisdiction.upper())

        if provider and provider.lower() != "all":
            query = query.filter(Patent.provider == provider.lower())

        if search_query and search_query.strip():
            clean_q = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Patent.title.ilike(clean_q),
                    Patent.abstract.ilike(clean_q),
                    Patent.publication_number.ilike(clean_q)
                )
            )

        total = query.count()
        patents = query.all()

        # Enrich with similarities
        embedding_service = PatentEmbeddingService(db)
        schemas = [PatentSchema.model_validate(p.to_dict()) for p in patents]
        enriched = embedding_service.populate_schema_similarities(project_id, schemas, patents)

        # Sort
        if sort_by == "similarity":
            enriched.sort(key=lambda s: s.similarity_score or 0.0, reverse=True)
        elif sort_by == "publication_date":
            enriched.sort(key=lambda s: s.publication_date or "", reverse=True)
        elif sort_by == "created_at":
            enriched.sort(key=lambda s: s.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

        start = (page - 1) * page_size
        paginated_items = enriched[start:start + page_size]

        return PatentListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=paginated_items,
            disclaimer=LEGAL_DISCLAIMER
        )

    def get_patent_by_id(self, db: Session, project_id: str, patent_id: str) -> Optional[PatentSchema]:
        """Fetches a single patent enriched with similarity score."""
        patent = db.query(Patent).filter(Patent.project_id == project_id, Patent.id == patent_id).first()
        if not patent:
            return None

        embedding_service = PatentEmbeddingService(db)
        schema = PatentSchema.model_validate(patent.to_dict())
        enriched = embedding_service.populate_schema_similarities(project_id, [schema], [patent])
        return enriched[0]

    def get_patent_stats(self, db: Session, project_id: str) -> PatentStatsResponse:
        """Computes statistical metrics across discovered patents for a project."""
        patents = db.query(Patent).filter(Patent.project_id == project_id).all()
        if not patents:
            return PatentStatsResponse(
                project_id=project_id,
                total_patents=0,
                disclaimer=LEGAL_DISCLAIMER
            )

        embedding_service = PatentEmbeddingService(db)
        sim_map = embedding_service.get_patent_similarities(project_id, patents)

        by_provider: Dict[str, int] = {}
        by_jurisdiction: Dict[str, int] = {}
        top_classifications: Dict[str, int] = {}
        top_assignees: Dict[str, int] = {}
        high_sim_count = 0
        mod_sim_count = 0
        low_sim_count = 0

        for p in patents:
            prov = p.provider or "unknown"
            by_provider[prov] = by_provider.get(prov, 0) + 1

            jur = p.jurisdiction or "US"
            by_jurisdiction[jur] = by_jurisdiction.get(jur, 0) + 1

            for cpc in (p.cpc_classifications or []):
                top_classifications[cpc] = top_classifications.get(cpc, 0) + 1

            for asg in (p.assignees or []):
                top_assignees[asg] = top_assignees.get(asg, 0) + 1

            score, band = sim_map.get(p.id, (0.0, "Low semantic similarity"))
            if score >= settings.SIMILARITY_HIGH_THRESHOLD:
                high_sim_count += 1
            elif score >= settings.SIMILARITY_MODERATE_THRESHOLD:
                mod_sim_count += 1
            else:
                low_sim_count += 1

        # Sort dicts by count desc
        top_classifications = dict(sorted(top_classifications.items(), key=lambda x: x[1], reverse=True)[:10])
        top_assignees = dict(sorted(top_assignees.items(), key=lambda x: x[1], reverse=True)[:8])

        latest = max((p.retrieved_at for p in patents if p.retrieved_at), default=None)

        return PatentStatsResponse(
            project_id=project_id,
            total_patents=len(patents),
            by_provider=by_provider,
            by_jurisdiction=by_jurisdiction,
            top_classifications=top_classifications,
            top_assignees=top_assignees,
            high_similarity_count=high_sim_count,
            moderate_similarity_count=mod_sim_count,
            low_similarity_count=low_sim_count,
            most_recent_retrieval=latest.isoformat() if latest else None,
            disclaimer=LEGAL_DISCLAIMER
        )

    def get_patent_evidence_manifest(self, db: Session, project_id: str) -> List[PatentEvidenceManifestItem]:
        """Generates evidence manifest entries with deterministic IDs (EVID-PAT-01..N)."""
        patents = db.query(Patent).filter(Patent.project_id == project_id).order_by(Patent.created_at.asc()).all()
        if not patents:
            return []

        embedding_service = PatentEmbeddingService(db)
        sim_map = embedding_service.get_patent_similarities(project_id, patents)

        manifest: List[PatentEvidenceManifestItem] = []
        for idx, p in enumerate(patents, start=1):
            score, _ = sim_map.get(p.id, (None, None))
            snippet = (p.abstract or f"Patent {p.publication_number}: {p.title}")[:300]
            manifest.append(PatentEvidenceManifestItem(
                evidence_id=f"EVID-PAT-{idx:02d}",
                patent_id=p.id,
                publication_number=p.publication_number,
                title=p.title,
                jurisdiction=p.jurisdiction,
                similarity_score=score,
                snippet=snippet
            ))

        return manifest

