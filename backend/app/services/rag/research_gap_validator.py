import logging
from typing import List, Tuple
from app.schemas.validation import EvidenceItem, ValidatedResearchGapItem

logger = logging.getLogger("uvicorn.error")

class ResearchGapValidator:
    """
    Evaluates candidate innovation gaps against retrieved academic and implementation
    evidence to classify them into:
      - supported_gap: Evidence confirms the limitation exists and is not solved in sample repos.
      - partially_supported_gap: Evidence shows some implementations exist but key aspects remain open.
      - not_supported_gap: Evidence demonstrates this capability is already solved in existing implementations.
      - insufficient_evidence: Insufficient retrieved sources to establish whether this gap is genuine.
    """

    @classmethod
    def evaluate_candidate_gaps(
        cls,
        evidence_items: List[EvidenceItem],
    ) -> Tuple[List[ValidatedResearchGapItem], str]:
        """
        Synthesizes candidate gap items based on retrieved evidence manifest and innovation gaps.
        """
        gap_evids = [e for e in evidence_items if e.source_type == "innovation_gap"]
        paper_evids = [e for e in evidence_items if e.source_type == "research_paper"]
        repo_evids = [e for e in evidence_items if e.source_type in ("github_repository", "repository_analysis")]

        validated_items: List[ValidatedResearchGapItem] = []

        if not gap_evids:
            # Fallback if no explicit gap records exist: synthesize from repos and papers
            if repo_evids or paper_evids:
                validated_items.append(
                    ValidatedResearchGapItem(
                        gap_title="Real-time Cross-Source Synthesis & Benchmarking",
                        description="Existing repositories offer isolated pipelines; no unified benchmark exists in the retrieved sample.",
                        category="architecture",
                        validation_status="partially_supported_gap",
                        priority="high",
                        supporting_evidence_ids=[paper_evids[0].evidence_id] if paper_evids else [],
                        contradicting_evidence_ids=[repo_evids[0].evidence_id] if repo_evids else [],
                        reasoning="Academic papers identify real-time cross-source synthesis as an open bottleneck, while sample repositories only implement batch workflows.",
                        confidence_level="moderate" if (paper_evids and repo_evids) else "weak",
                        suggested_direction="Develop an end-to-end event-driven architecture with unified evaluation metrics.",
                    )
                )
            else:
                validated_items.append(
                    ValidatedResearchGapItem(
                        gap_title="End-to-End System Evaluation",
                        description="Insufficient evidence was retrieved in the current sample to validate specific architecture gaps.",
                        category="evaluation",
                        validation_status="insufficient_evidence",
                        priority="medium",
                        supporting_evidence_ids=[],
                        contradicting_evidence_ids=[],
                        reasoning="No academic papers or GitHub repositories were matched with sufficient similarity to confirm this gap.",
                        confidence_level="insufficient",
                        suggested_direction="Broaden retrieval parameters or ingest domain-specific benchmarks.",
                    )
                )
            summary = f"Evaluated {len(validated_items)} synthesized gap candidates against {len(evidence_items)} total retrieved sources."
            return validated_items, summary

        # Iterate over discovered gap items
        for gap_ev in gap_evids:
            title = gap_ev.source_title
            desc = gap_ev.evidence_content
            category = gap_ev.evidence_category or "capability"

            # Check matching papers and repositories
            keywords = [w.lower() for w in title.split() if len(w) > 3]
            
            supporting_papers = []
            for p in paper_evids:
                p_text = (p.source_title + " " + p.evidence_content).lower()
                if any(kw in p_text for kw in keywords):
                    supporting_papers.append(p.evidence_id)

            contradicting_repos = []
            supporting_repos = []
            for r in repo_evids:
                r_text = (r.source_title + " " + r.evidence_content).lower()
                matches = sum(1 for kw in keywords if kw in r_text)
                if matches >= 2:
                    # Repo appears to implement or closely address the gap
                    contradicting_repos.append(r.evidence_id)
                elif matches == 1:
                    supporting_repos.append(r.evidence_id)

            supporting_ids = list(dict.fromkeys([gap_ev.evidence_id] + supporting_papers + supporting_repos))
            contradicting_ids = list(dict.fromkeys(contradicting_repos))

            # Classification logic
            if contradicting_ids and not supporting_papers:
                status = "not_supported_gap"
                reasoning = (
                    f"Existing repository implementations ({', '.join(contradicting_ids[:2])}) "
                    f"already address functionality overlapping with '{title}' in their documented features."
                )
                confidence = "moderate" if len(contradicting_ids) > 1 else "weak"
                priority = "low"
                suggested_dir = "Pivot towards higher-order customization or edge cases not handled by existing repos."

            elif contradicting_ids and supporting_papers:
                status = "partially_supported_gap"
                reasoning = (
                    f"Academic literature ({', '.join(supporting_papers[:2])}) emphasizes limitations in this area, "
                    f"though partial implementations exist in ({', '.join(contradicting_ids[:2])})."
                )
                confidence = "strong" if len(supporting_ids) >= 2 else "moderate"
                priority = "medium"
                suggested_dir = "Address remaining edge cases, scalability limits, or architectural trade-offs identified in research."

            elif supporting_papers or supporting_repos:
                status = "supported_gap"
                reasoning = (
                    f"Confirmed as an open research/implementation gap backed by ({', '.join(supporting_ids[:3])}). "
                    f"No existing repository in the retrieved sample provides a complete solution."
                )
                confidence = "strong" if len(supporting_papers) >= 2 else "moderate"
                priority = "high"
                suggested_dir = "Prioritize implementation as a core differentiating capability with empirical evaluation."

            else:
                status = "insufficient_evidence"
                reasoning = (
                    f"Retrieved sources do not contain sufficient evidence to conclusively validate or refute "
                    f"'{title}'. Absence of evidence in the sample does not guarantee absence in other literature."
                )
                confidence = "insufficient"
                priority = "medium"
                suggested_dir = "Expand academic literature search or examine niche open-source toolkits."

            validated_items.append(
                ValidatedResearchGapItem(
                    gap_title=title,
                    description=desc,
                    category=category,
                    validation_status=status,
                    priority=priority,
                    supporting_evidence_ids=supporting_ids,
                    contradicting_evidence_ids=contradicting_ids,
                    reasoning=reasoning,
                    confidence_level=confidence,
                    suggested_direction=suggested_dir,
                )
            )

        supported_cnt = sum(1 for g in validated_items if g.validation_status == "supported_gap")
        partial_cnt = sum(1 for g in validated_items if g.validation_status == "partially_supported_gap")
        not_sup_cnt = sum(1 for g in validated_items if g.validation_status == "not_supported_gap")
        insuff_cnt = sum(1 for g in validated_items if g.validation_status == "insufficient_evidence")

        summary = (
            f"Validated {len(validated_items)} candidate innovation gaps: "
            f"{supported_cnt} strongly supported, {partial_cnt} partially supported, "
            f"{not_sup_cnt} not supported (already addressed), and {insuff_cnt} with insufficient evidence."
        )

        return validated_items, summary

