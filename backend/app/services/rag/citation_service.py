import re
import logging
from typing import List, Set, Dict, Any, Tuple
from app.schemas.validation import ProjectValidationReportSchema, EvidenceItem

logger = logging.getLogger("uvicorn.error")

EVIDENCE_ID_REGEX = re.compile(r"EVID-(?:PAP|REP|GAP|PAT)-\d+", re.IGNORECASE)

class CitationService:
    """
    Validates citation integrity in RAG validation reports against the retrieved
    evidence manifest. Strips hallucinated evidence IDs and computes citation metrics.
    """

    @staticmethod
    def extract_evidence_ids(text: str) -> List[str]:
        """Extracts any EVID-XXX-YY tokens from raw text."""
        if not text:
            return []
        matches = EVIDENCE_ID_REGEX.findall(text)
        return [m.upper() for m in matches]

    @staticmethod
    def validate_and_sanitize_report(
        report: ProjectValidationReportSchema,
        evidence_manifest: List[EvidenceItem],
    ) -> Tuple[ProjectValidationReportSchema, Dict[str, Any]]:
        """
        Scans all report sections, filters out any hallucinated evidence IDs not present
        in the retrieved manifest, and calculates citation statistics.
        """
        valid_ids: Set[str] = {item.evidence_id.upper() for item in evidence_manifest}
        
        total_attempted = 0
        valid_count = 0
        purged_ids: List[str] = []

        def sanitize_id_list(id_list: List[str]) -> List[str]:
            nonlocal total_attempted, valid_count, purged_ids
            cleaned = []
            for raw_id in id_list:
                cleaned_id = raw_id.strip().upper()
                total_attempted += 1
                if cleaned_id in valid_ids:
                    cleaned.append(cleaned_id)
                    valid_count += 1
                else:
                    purged_ids.append(raw_id)
                    logger.warning(f"RAG Citation Validation: Purged hallucinated evidence ID: {raw_id}")
            # Deduplicate preserving order
            seen = set()
            return [x for x in cleaned if not (x in seen or seen.add(x))]

        # 1. Academic Research Papers
        for paper in report.academic_research.relevant_papers:
            total_attempted += 1
            if paper.evidence_id.upper() in valid_ids:
                paper.evidence_id = paper.evidence_id.upper()
                valid_count += 1
            else:
                purged_ids.append(paper.evidence_id)
                # If invalid, attempt to assign first available paper evidence ID or empty
                fallback_pap = next((e.evidence_id for e in evidence_manifest if e.source_type == "research_paper"), "")
                paper.evidence_id = fallback_pap

        # 2. Software Implementations
        for repo in report.software_implementations.relevant_repositories:
            total_attempted += 1
            if repo.evidence_id.upper() in valid_ids:
                repo.evidence_id = repo.evidence_id.upper()
                valid_count += 1
            else:
                purged_ids.append(repo.evidence_id)
                fallback_rep = next((e.evidence_id for e in evidence_manifest if e.source_type in ("github_repository", "repository_analysis")), "")
                repo.evidence_id = fallback_rep

        # 3. Existing Capability Analysis
        for cap in report.capability_analysis.already_addressed_capabilities:
            cap.supporting_evidence_ids = sanitize_id_list(cap.supporting_evidence_ids)
        for cap in report.capability_analysis.partially_addressed_capabilities:
            cap.supporting_evidence_ids = sanitize_id_list(cap.supporting_evidence_ids)
        for cap in report.capability_analysis.capabilities_with_insufficient_evidence:
            cap.supporting_evidence_ids = sanitize_id_list(cap.supporting_evidence_ids)

        # 4. Validated Research Gaps
        for gap in report.validated_research_gaps.validated_gaps:
            gap.supporting_evidence_ids = sanitize_id_list(gap.supporting_evidence_ids)
            gap.contradicting_evidence_ids = sanitize_id_list(gap.contradicting_evidence_ids)

        # 5. Innovation Opportunities
        for opp in report.innovation_opportunities.differentiating_capabilities:
            opp.supporting_evidence_ids = sanitize_id_list(opp.supporting_evidence_ids)
        for opp in report.innovation_opportunities.technical_improvements:
            opp.supporting_evidence_ids = sanitize_id_list(opp.supporting_evidence_ids)
        for opp in report.innovation_opportunities.research_directions:
            opp.supporting_evidence_ids = sanitize_id_list(opp.supporting_evidence_ids)

        # 6. Technical Recommendations
        report.technical_recommendations.citations = sanitize_id_list(report.technical_recommendations.citations)

        stats = {
            "total_citations_attempted": total_attempted,
            "valid_citations": valid_count,
            "purged_hallucinations_count": len(purged_ids),
            "purged_ids": purged_ids,
            "manifest_size": len(evidence_manifest),
            "citation_integrity_ratio": round(valid_count / max(1, total_attempted), 4),
        }

        return report, stats

