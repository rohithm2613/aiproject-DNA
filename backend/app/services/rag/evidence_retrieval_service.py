import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.research_paper import ResearchPaper
from app.models.github_repo import GitHubRepository
from app.models.repository_analysis import RepositoryAnalysis
from app.models.innovation_gap import InnovationGap
from app.models.patent import Patent
from app.models.project_embedding import ProjectEmbedding
from app.schemas.validation import EvidenceItem
from app.services.embedding.semantic_similarity_service import compute_cosine_similarity
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

class EvidenceRetrievalService:
    """
    Retrieves, normalizes, deduplicates, and ranks evidence from academic papers,
    GitHub repositories, repository analyses, and innovation gaps.
    """

    def __init__(self, db: Session):
        self.db = db

    def retrieve_evidence_manifest(
        self,
        project: Project,
        max_papers: int = 15,
        max_repos: int = 15,
        max_gaps: int = 20,
        max_patents: int = 15,
        include_embeddings: bool = True,
    ) -> Tuple[List[EvidenceItem], Dict[str, Any]]:
        """
        Gathers all available evidence items for the given project, computes
        traceable evidence IDs, attaches similarity scores, and constructs
        the normalized evidence manifest.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        evidence_items: List[EvidenceItem] = []
        counts_by_source = {"research_paper": 0, "github_repository": 0, "innovation_gap": 0, "patent": 0}

        # 1. Fetch project's own idea embedding if embeddings are enabled
        project_vec: Optional[List[float]] = None
        if include_embeddings:
            proj_emb = (
                self.db.query(ProjectEmbedding)
                .filter(
                    ProjectEmbedding.project_id == project.id,
                    ProjectEmbedding.source_type == "project",
                )
                .first()
            )
            if proj_emb and proj_emb.embedding:
                project_vec = proj_emb.embedding

        # Fetch candidate source embeddings mapping: (source_type, source_record_id) -> embedding
        embedding_map: Dict[Tuple[str, str], List[float]] = {}
        if project_vec:
            stored_embs = (
                self.db.query(ProjectEmbedding)
                .filter(
                    ProjectEmbedding.project_id == project.id,
                    ProjectEmbedding.source_type != "project",
                )
                .all()
            )
            for e in stored_embs:
                if e.embedding:
                    embedding_map[(e.source_type, e.source_record_id)] = e.embedding

        # ---------------------------------------------------------------------
        # 2. Retrieve & Normalize Academic Research Papers (Phase 4.1)
        # ---------------------------------------------------------------------
        papers = (
            self.db.query(ResearchPaper)
            .filter(ResearchPaper.project_id == project.id)
            .all()
        )

        scored_papers: List[Tuple[ResearchPaper, float]] = []
        for p in papers:
            cand_vec = embedding_map.get(("research_paper", p.id))
            sim_score = (
                compute_cosine_similarity(project_vec, cand_vec)
                if project_vec and cand_vec
                else None
            )
            # Default rank tie-breaker: citations or year
            sort_weight = sim_score if sim_score is not None else (0.1 + (p.citation_count or 0) * 0.001)
            scored_papers.append((p, sort_weight))

        # Sort descending by similarity / weight
        scored_papers.sort(key=lambda x: x[1], reverse=True)

        # Deduplicate papers by DOI or arXiv ID or title
        seen_paper_keys = set()
        deduped_papers: List[Tuple[ResearchPaper, Optional[float]]] = []
        for p, weight in scored_papers:
            key = p.doi or p.arxiv_id or p.title.strip().lower()
            if key in seen_paper_keys:
                continue
            seen_paper_keys.add(key)
            sim_val = round(weight, 4) if project_vec and ("research_paper", p.id) in embedding_map else None
            deduped_papers.append((p, sim_val))

        pap_index = 1
        for p, sim_score in deduped_papers[:max_papers]:
            evid_id = f"EVID-PAP-{pap_index:02d}"
            pap_index += 1

            # Determine strength
            if p.abstract and len(p.abstract) > 100 and (p.doi or p.arxiv_id):
                strength = "strong" if (sim_score is not None and sim_score >= 0.6) else "moderate"
            elif p.abstract:
                strength = "moderate"
            elif p.title:
                strength = "weak"
            else:
                strength = "insufficient"

            authors_str = ", ".join(p.authors) if p.authors else "Unknown Authors"
            content_parts = [f"Title: {p.title}"]
            if p.venue:
                content_parts.append(f"Venue: {p.venue}")
            if p.publication_year:
                content_parts.append(f"Year: {p.publication_year}")
            if p.primary_category:
                content_parts.append(f"Category: {p.primary_category}")
            if p.abstract:
                content_parts.append(f"Abstract: {p.abstract[:1200]}")

            evidence_items.append(
                EvidenceItem(
                    evidence_id=evid_id,
                    project_id=project.id,
                    source_type="research_paper",
                    source_record_id=p.id,
                    source_title=p.title,
                    source_url=p.paper_url or (f"https://doi.org/{p.doi}" if p.doi else None),
                    source_author=authors_str,
                    publication_year=p.publication_year,
                    evidence_content="\n".join(content_parts),
                    evidence_category=p.primary_category or "Academic Research",
                    similarity_score=sim_score,
                    evidence_strength=strength,
                    documented_or_inferred="documented",
                    retrieved_at=now_iso,
                )
            )
            counts_by_source["research_paper"] += 1

        # ---------------------------------------------------------------------
        # 3. Retrieve & Normalize GitHub Repositories (Phase 4.2 & 4.3)
        # ---------------------------------------------------------------------
        repos = (
            self.db.query(GitHubRepository)
            .filter(GitHubRepository.project_id == project.id)
            .all()
        )

        analyses = (
            self.db.query(RepositoryAnalysis)
            .filter(RepositoryAnalysis.project_id == project.id)
            .all()
        )
        analysis_by_repo_id = {a.github_repo_id: a for a in analyses}

        scored_repos: List[Tuple[GitHubRepository, Optional[RepositoryAnalysis], float]] = []
        for r in repos:
            a = analysis_by_repo_id.get(r.id)
            cand_vec = embedding_map.get(("github_repository", r.id))
            sim_score = (
                compute_cosine_similarity(project_vec, cand_vec)
                if project_vec and cand_vec
                else None
            )
            structural_score = None
            if a and a.similarity and isinstance(a.similarity, dict):
                structural_score = a.similarity.get("overall_score")

            # Weight combination for ranking: prioritize vector similarity, then structural score, then stars
            if sim_score is not None:
                sort_weight = sim_score
            elif structural_score is not None:
                sort_weight = structural_score / 100.0
            else:
                sort_weight = 0.1 + (r.stargazers_count or 0) * 0.0001

            scored_repos.append((r, a, sort_weight))

        scored_repos.sort(key=lambda x: x[2], reverse=True)

        seen_repo_names = set()
        deduped_repos: List[Tuple[GitHubRepository, Optional[RepositoryAnalysis], Optional[float]]] = []
        for r, a, weight in scored_repos:
            if r.full_name.lower() in seen_repo_names:
                continue
            seen_repo_names.add(r.full_name.lower())
            sim_val = round(weight, 4) if project_vec and ("github_repository", r.id) in embedding_map else None
            deduped_repos.append((r, a, sim_val))

        rep_index = 1
        for r, a, sim_score in deduped_repos[:max_repos]:
            evid_id = f"EVID-REP-{rep_index:02d}"
            rep_index += 1

            has_deep_analysis = a is not None
            has_readme = a.readme_present if a else False
            doc_features = a.features if (a and a.features) else []
            detected_techs = a.detected_technologies if (a and a.detected_technologies) else {}

            if has_deep_analysis and (r.stargazers_count >= 50 or len(doc_features) >= 2):
                strength = "strong"
            elif has_readme or r.description:
                strength = "moderate"
            elif r.full_name:
                strength = "weak"
            else:
                strength = "insufficient"

            content_lines = [
                f"Repository: {r.full_name}",
                f"Primary Language: {r.language or 'Unknown'}",
                f"Stars: {r.stargazers_count}",
                f"Description: {r.description or 'No description provided.'}",
            ]
            if a:
                if a.summary and a.summary != r.description:
                    content_lines.append(f"Deep Analysis Summary: {a.summary[:600]}")
                if a.problem_statement:
                    content_lines.append(f"Problem Addressed: {a.problem_statement[:400]}")
                # Detected technologies
                tech_list = []
                for cat, items in detected_techs.items():
                    if isinstance(items, list) and cat != "evidence_sources":
                        tech_list.extend(items)
                if tech_list:
                    content_lines.append(f"Detected Tech Stack: {', '.join(sorted(set(tech_list))[:12])}")
                # Extracted features
                if doc_features:
                    feat_names = [
                        (f.get("feature_name") if isinstance(f, dict) else getattr(f, "feature_name", ""))
                        for f in doc_features[:6]
                    ]
                    content_lines.append(f"Extracted Features: {', '.join(filter(None, feat_names))}")

            evidence_items.append(
                EvidenceItem(
                    evidence_id=evid_id,
                    project_id=project.id,
                    source_type="github_repository",
                    source_record_id=r.id,
                    source_title=r.full_name,
                    source_url=r.html_url,
                    source_author=r.owner_login,
                    publication_year=int(r.created_at[:4]) if r.created_at and len(r.created_at) >= 4 and r.created_at[:4].isdigit() else None,
                    evidence_content="\n".join(content_lines),
                    evidence_category=r.language or "Open Source Software",
                    similarity_score=sim_score,
                    evidence_strength=strength,
                    documented_or_inferred="documented" if (has_readme and doc_features) else "inferred",
                    retrieved_at=now_iso,
                )
            )
            counts_by_source["github_repository"] += 1

        # ---------------------------------------------------------------------
        # 4. Retrieve & Normalize Innovation Gap Candidates (Phase 4.3)
        # ---------------------------------------------------------------------
        gaps = (
            self.db.query(InnovationGap)
            .filter(InnovationGap.project_id == project.id)
            .order_by(InnovationGap.priority.desc())
            .limit(max_gaps)
            .all()
        )

        gap_index = 1
        for g in gaps:
            evid_id = f"EVID-GAP-{gap_index:02d}"
            gap_index += 1

            gap_content = [
                f"Candidate Gap: {g.gap_title}",
                f"Category: {g.category}",
                f"Priority: {g.priority.upper()}",
                f"Description: {g.description}",
                f"Why It Matters: {g.why_it_matters}",
                f"Suggested Implementation: {g.suggested_implementation}",
            ]
            if g.supporting_evidence and isinstance(g.supporting_evidence, dict):
                cites = g.supporting_evidence.get("analyzed_repositories", [])
                if cites:
                    gap_content.append(f"Associated Repositories: {', '.join(cites[:5])}")

            # Gaps are inherently inferred from cross-repository gap analysis
            strength = "strong" if g.priority == "high" and g.confidence_level == "high" else "moderate"

            evidence_items.append(
                EvidenceItem(
                    evidence_id=evid_id,
                    project_id=project.id,
                    source_type="innovation_gap",
                    source_record_id=g.id,
                    source_title=g.gap_title,
                    source_url=None,
                    source_author="Phase 4.3 Innovation Gap Analyzer",
                    publication_year=None,
                    evidence_content="\n".join(gap_content),
                    evidence_category=g.category,
                    similarity_score=None,
                    evidence_strength=strength,
                    documented_or_inferred="inferred",
                    retrieved_at=now_iso,
                )
            )
            counts_by_source["innovation_gap"] += 1

        # ---------------------------------------------------------------------
        # 5. Retrieve & Normalize Patent Evidence (Phase 4.6)
        # ---------------------------------------------------------------------
        patents = (
            self.db.query(Patent)
            .filter(Patent.project_id == project.id)
            .all()
        )

        scored_patents: List[Tuple[Patent, float]] = []
        for pat in patents:
            cand_vec = embedding_map.get(("patent", pat.id))
            sim_score = (
                compute_cosine_similarity(project_vec, cand_vec)
                if project_vec and cand_vec
                else None
            )
            sort_weight = sim_score if sim_score is not None else 0.1
            scored_patents.append((pat, sort_weight))

        scored_patents.sort(key=lambda x: x[1], reverse=True)

        seen_pub_numbers = set()
        deduped_patents: List[Tuple[Patent, Optional[float]]] = []
        for pat, weight in scored_patents:
            clean_pub = (pat.publication_number or "").strip().upper()
            if clean_pub in seen_pub_numbers:
                continue
            seen_pub_numbers.add(clean_pub)
            sim_val = round(weight, 4) if project_vec and ("patent", pat.id) in embedding_map else None
            deduped_patents.append((pat, sim_val))

        pat_index = 1
        for pat, sim_score in deduped_patents[:max_patents]:
            evid_id = f"EVID-PAT-{pat_index:02d}"
            pat_index += 1

            assignee_str = ", ".join(pat.assignees[:2]) if pat.assignees else "Independent Inventor"
            cpc_str = ", ".join(pat.cpc_classifications[:4]) if pat.cpc_classifications else "Not classified"

            content_lines = [
                f"Patent Publication: {pat.publication_number}",
                f"Title: {pat.title}",
                f"Jurisdiction: {pat.jurisdiction or 'US'}",
                f"Assignee/Applicant: {assignee_str}",
                f"CPC Classifications: {cpc_str}",
            ]
            if pat.abstract:
                content_lines.append(f"Abstract: {pat.abstract[:800]}")
            if pat.claims:
                clean_claims = [c[:200] for c in pat.claims[:2] if c]
                if clean_claims:
                    content_lines.append(f"Key Claims: {' | '.join(clean_claims)}")

            strength = "strong" if pat.abstract and pat.claims else "moderate" if pat.abstract else "weak"

            evidence_items.append(
                EvidenceItem(
                    evidence_id=evid_id,
                    project_id=project.id,
                    source_type="patent",
                    source_record_id=pat.id,
                    source_title=f"{pat.publication_number} - {pat.title}",
                    source_url=pat.source_url,
                    source_author=assignee_str,
                    publication_year=int(pat.publication_date[:4]) if pat.publication_date and len(pat.publication_date) >= 4 and pat.publication_date[:4].isdigit() else None,
                    evidence_content="\n".join(content_lines),
                    evidence_category=cpc_str,
                    similarity_score=sim_score,
                    evidence_strength=strength,
                    documented_or_inferred="documented",
                    retrieved_at=now_iso,
                )
            )
            counts_by_source["patent"] += 1

        retrieval_metadata = {
            "retrieval_timestamp": now_iso,
            "total_evidence_items": len(evidence_items),
            "counts_by_source": counts_by_source,
            "papers_evaluated": len(papers),
            "papers_included": counts_by_source["research_paper"],
            "repos_evaluated": len(repos),
            "repos_included": counts_by_source["github_repository"],
            "gaps_evaluated": len(gaps),
            "gaps_included": counts_by_source["innovation_gap"],
            "patents_evaluated": len(patents),
            "patents_included": counts_by_source["patent"],
            "has_embeddings": project_vec is not None,
            "coverage_level": (
                "comprehensive" if counts_by_source["research_paper"] >= 2 and counts_by_source["github_repository"] >= 2 and counts_by_source["patent"] >= 1
                else "adequate" if (counts_by_source["research_paper"] >= 1 or counts_by_source["patent"] >= 1) and counts_by_source["github_repository"] >= 1
                else "partial" if (counts_by_source["research_paper"] > 0 or counts_by_source["github_repository"] > 0 or counts_by_source["patent"] > 0)
                else "sparse"
            ),
        }

        return evidence_items, retrieval_metadata
