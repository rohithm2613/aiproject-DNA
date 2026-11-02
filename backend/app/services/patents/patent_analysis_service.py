import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project
from app.models.patent import Patent
from app.models.analysis import ProjectAnalysis
from app.schemas.patent import (
    PriorArtAnalysisItem,
    PatentAnalysisResponse,
    LEGAL_DISCLAIMER
)
from app.services.patents.patent_embedding_service import PatentEmbeddingService

logger = logging.getLogger("uvicorn.error")

class PatentAnalysisService:
    """
    Analyzes discovered patent publications against the user's project idea,
    extracting technical problems, solutions, similarities, differences,
    claims overlap analysis, and technical differentiation opportunities.
    """

    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = PatentEmbeddingService(db)

    def analyze_prior_art(
        self,
        project_id: str,
        user_id: str,
        patent_ids: Optional[List[str]] = None,
        max_patents: int = 10,
    ) -> PatentAnalysisResponse:
        """
        Executes prior-art deep analysis for a project's patents.
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Get latest ProjectAnalysis
        analysis = (
            self.db.query(ProjectAnalysis)
            .filter(ProjectAnalysis.project_id == project_id)
            .order_by(ProjectAnalysis.version.desc())
            .first()
        )

        query = self.db.query(Patent).filter(Patent.project_id == project_id)
        if patent_ids:
            query = query.filter(Patent.id.in_(patent_ids))
        patents = query.order_by(Patent.created_at.desc()).limit(max_patents).all()

        if not patents:
            return PatentAnalysisResponse(
                project_id=project_id,
                total_analyzed=0,
                prior_art_analyses=[],
                overall_prior_art_summary="No patents have been discovered yet for this project.",
                technical_differentiation_opportunities=[],
                disclaimer=LEGAL_DISCLAIMER
            )

        # Ensure embeddings and get similarities
        self.embedding_service.ensure_patent_embeddings(project_id, patents)
        sim_map = self.embedding_service.get_patent_similarities(project_id, patents)

        # Try Gemini AI analysis if configured
        prior_art_items: List[PriorArtAnalysisItem] = []
        gemini_success = False

        if settings.GEMINI_API_KEY:
            try:
                prior_art_items = self._analyze_with_gemini(project, analysis, patents, sim_map)
                gemini_success = True
            except Exception as exc:
                logger.warning(f"[PatentAnalysis] Gemini AI analysis failed: {exc}. Falling back to heuristic synthesizer.")

        if not gemini_success:
            prior_art_items = self._analyze_heuristically(project, analysis, patents, sim_map)

        # Generate overall synthesis
        overall_summary, opportunities = self._synthesize_overall_landscape(project, analysis, prior_art_items)

        return PatentAnalysisResponse(
            project_id=project_id,
            total_analyzed=len(prior_art_items),
            prior_art_analyses=prior_art_items,
            overall_prior_art_summary=overall_summary,
            technical_differentiation_opportunities=opportunities,
            disclaimer=LEGAL_DISCLAIMER
        )

    def _analyze_heuristically(
        self,
        project: Project,
        analysis: Optional[ProjectAnalysis],
        patents: List[Patent],
        sim_map: Dict[str, tuple]
    ) -> List[PriorArtAnalysisItem]:
        """Deterministic heuristic analysis based on title, abstract, CPC classifications and keywords."""
        items: List[PriorArtAnalysisItem] = []

        project_keywords = analysis.keywords if (analysis and analysis.keywords) else (project.technologies or [])
        project_domain = analysis.primary_domain if (analysis and analysis.primary_domain) else (project.domain or "General")
        project_solution = analysis.proposed_solution if (analysis and analysis.proposed_solution) else (project.description or "")

        for pat in patents:
            score, band = sim_map.get(pat.id, (0.0, "Low semantic similarity"))
            abstract_text = pat.abstract or "Abstract not available from provider."
            title_text = pat.title or "Untitled Patent"

            # Technical problem heuristics
            tech_problem = f"Addressing technical challenges in {', '.join(pat.cpc_classifications[:2]) if pat.cpc_classifications else pat.jurisdiction or 'the domain'}, specifically regarding {title_text.lower()}."
            if "method" in title_text.lower():
                tech_solution = f"Discloses a computer-implemented method and processing pipeline for {title_text.lower()}."
            elif "system" in title_text.lower() or "apparatus" in title_text.lower():
                tech_solution = f"Discloses an architecture and apparatus designed to implement {title_text.lower()}."
            else:
                tech_solution = f"Discloses technical mechanisms for {title_text.lower()}."

            # Key features extracted
            features: List[str] = []
            if pat.cpc_classifications:
                features.append(f"Classification focus: {', '.join(pat.cpc_classifications[:3])}")
            if pat.assignees:
                features.append(f"Assigned by: {', '.join(pat.assignees[:2])}")
            if pat.claims:
                features.append(f"Primary claim excerpt: {pat.claims[0][:140]}...")
            else:
                features.append(f"Discloses automated workflows and data structures for {title_text[:60]}.")

            # Similarities
            similarities: List[str] = [
                f"Both target technical implementations in or adjacent to {project_domain}.",
            ]
            overlapping_kws = [k for k in project_keywords if k.lower() in (title_text + " " + abstract_text).lower()]
            if overlapping_kws:
                similarities.append(f"Shared technical focus areas: {', '.join(overlapping_kws[:3])}.")

            # Differences
            differences: List[str] = [
                f"The user's project incorporates specific domain workflows ({project_domain}) not explicitly detailed in {pat.publication_number}.",
                f"Different software integration parameters and modern interface requirements compared to the patent's disclosed embodiment.",
            ]

            claims_overlap = (
                f"Preliminary analysis against publication {pat.publication_number} shows technical conceptual overlap "
                f"in {pat.jurisdiction or 'global'} jurisdiction ({band}). Independent claim boundaries require formal legal evaluation."
            )

            limitations = (
                f"Disclosed mechanisms in {pat.publication_number} (filed {pat.filing_date or 'N/A'}) reflect architectural patterns "
                f"standard at publication date ({pat.publication_date or 'N/A'}), lacking modern distributed and real-time paradigms."
            )

            items.append(PriorArtAnalysisItem(
                patent_id=pat.id,
                publication_number=pat.publication_number,
                title=pat.title,
                jurisdiction=pat.jurisdiction,
                technical_problem=tech_problem,
                proposed_solution=tech_solution,
                key_features=features,
                similarities_with_idea=similarities,
                differences_from_idea=differences,
                claims_overlap_analysis=claims_overlap,
                limitation_observations=limitations,
                similarity_score=score,
                similarity_band=band
            ))

        return items

    def _analyze_with_gemini(
        self,
        project: Project,
        analysis: Optional[ProjectAnalysis],
        patents: List[Patent],
        sim_map: Dict[str, tuple]
    ) -> List[PriorArtAnalysisItem]:
        """Uses Gemini API with structured JSON output for deep prior-art comparison."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Prepare patent summaries
        patent_context_list = []
        for p in patents[:8]:
            score, band = sim_map.get(p.id, (0.0, "Low semantic similarity"))
            patent_context_list.append({
                "patent_id": p.id,
                "publication_number": p.publication_number,
                "title": p.title,
                "jurisdiction": p.jurisdiction,
                "abstract": (p.abstract or "")[:600],
                "assignees": p.assignees[:2] if p.assignees else [],
                "cpc": p.cpc_classifications[:4] if p.cpc_classifications else [],
                "similarity_score": score,
                "similarity_band": band,
            })

        project_summary = (analysis.project_summary if analysis and analysis.project_summary else project.description)[:1500]
        proposed_solution = (analysis.proposed_solution if analysis and analysis.proposed_solution else "")[:1000]

        prompt = f"""
You are an expert Patent and Prior-Art Technical Analyst. Analyze the following candidate patents against the user's project idea.
Compare technical mechanisms, extract problem/solution, identify conceptual similarities, distinct technical differences, and limitations.

IMPORTANT LEGAL BOUNDARY:
- Do NOT provide legal advice or definitive patent infringement conclusions.
- Frame all findings strictly as technical prior-art comparisons and conceptual overlap.

User Project Title: {project.title}
Domain: {project.domain}
Project Summary: {project_summary}
Proposed Solution: {proposed_solution}

Candidate Patents:
{json.dumps(patent_context_list, indent=2)}

Respond with a JSON array where each element matches this schema:
[
  {{
    "patent_id": "<matching patent_id>",
    "publication_number": "<publication_number>",
    "title": "<patent title>",
    "jurisdiction": "<jurisdiction>",
    "technical_problem": "<What technical problem does this patent solve?>",
    "proposed_solution": "<What technical architecture or method does it disclose?>",
    "key_features": ["<feature 1>", "<feature 2>"],
    "similarities_with_idea": ["<similarity 1>", "<similarity 2>"],
    "differences_from_idea": ["<technical difference 1>", "<technical difference 2>"],
    "claims_overlap_analysis": "<Technical observation on conceptual overlap with user project>",
    "limitation_observations": "<Technical limitations or narrow scope of the disclosed patent embodiment>"
  }}
]
"""
        primary_model = settings.GEMINI_MODEL or "gemini-2.5-flash"
        candidates = [primary_model]
        for fallback in ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-flash-latest"]:
            if fallback not in candidates:
                candidates.append(fallback)

        response = None
        for idx, model_name in enumerate(candidates):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    )
                )
                break
            except Exception as e:
                err_str = str(e)
                if ("404" in err_str or "NOT_FOUND" in err_str or "no longer available" in err_str.lower()) and idx < len(candidates) - 1:
                    logger.warning(f"[PatentAnalysis] Model '{model_name}' unavailable. Retrying with '{candidates[idx + 1]}'...")
                    continue
                raise

        if not response or not response.text:
            raise ValueError("Empty response received from Gemini prior-art analysis.")

        parsed = json.loads(response.text)
        if isinstance(parsed, dict) and "patents" in parsed:
            parsed = parsed["patents"]

        results: List[PriorArtAnalysisItem] = []
        for item in parsed:
            pid = item.get("patent_id")
            pub_num = item.get("publication_number", "")
            score, band = sim_map.get(pid, (0.0, "Low semantic similarity"))
            claims_analysis = item.get("claims_overlap_analysis", "")
            if "preliminary analysis against publication" not in claims_analysis.lower():
                claims_analysis = f"Preliminary analysis against publication {pub_num}: {claims_analysis}"

            results.append(PriorArtAnalysisItem(
                patent_id=pid,
                publication_number=pub_num,
                title=item.get("title", ""),
                jurisdiction=item.get("jurisdiction", "US"),
                technical_problem=item.get("technical_problem", ""),
                proposed_solution=item.get("proposed_solution", ""),
                key_features=item.get("key_features", []),
                similarities_with_idea=item.get("similarities_with_idea", []),
                differences_from_idea=item.get("differences_from_idea", []),
                claims_overlap_analysis=claims_analysis,
                limitation_observations=item.get("limitation_observations", ""),
                similarity_score=score,
                similarity_band=band,
            ))

        return results

    def _synthesize_overall_landscape(
        self,
        project: Project,
        analysis: Optional[ProjectAnalysis],
        prior_art_items: List[PriorArtAnalysisItem]
    ) -> tuple[str, List[str]]:
        """Generates an overall executive summary and technical differentiation opportunities."""
        high_sim = [p for p in prior_art_items if (p.similarity_score or 0) >= settings.SIMILARITY_HIGH_THRESHOLD]
        mod_sim = [p for p in prior_art_items if settings.SIMILARITY_MODERATE_THRESHOLD <= (p.similarity_score or 0) < settings.SIMILARITY_HIGH_THRESHOLD]

        summary = (
            f"Prior-art analysis identified {len(prior_art_items)} relevant patent publication(s) related to '{project.title}'. "
            f"Of these, {len(high_sim)} exhibit high semantic similarity and {len(mod_sim)} exhibit moderate similarity. "
            f"Disclosed prior art primarily focuses on foundational processing methods and system architectures, "
            f"leaving technical room for modern implementation paradigms and domain-specific integrations."
        )

        opportunities: List[str] = [
            f"Implement specialized machine learning inference pipelines tailored specifically for {project.domain}, avoiding broader disclosed hardware claims.",
            f"Adopt decentralized or edge-computing architectures that circumvent centralized server architectures typical of earlier patent disclosures.",
            f"Focus differentiation on real-time interactive user feedback and modern multimodal processing not addressed in legacy patent literature.",
        ]

        return summary, opportunities

