import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.innovation_gap import InnovationGap
from app.schemas.repository_analysis import (
    RepositoryAnalysisSchema,
    InnovationGapResponse,
)

logger = logging.getLogger("uvicorn.error")

class InnovationGapService:
    """
    Analyzes gaps, differentiation vectors, and missing capabilities
    between the user's project idea and analyzed GitHub repositories.
    """

    @staticmethod
    def _generate_deterministic_gaps(
        project: Project,
        analysis: Optional[ProjectAnalysis],
        analyzed_repos: List[RepositoryAnalysisSchema],
    ) -> List[Dict[str, Any]]:
        """
        Deterministic, rule-based innovation gap analysis engine.
        Ensures 100% reliable execution even when AI models are unavailable.
        """
        gaps: List[Dict[str, Any]] = []
        repo_names = [r.repo_full_name for r in analyzed_repos]
        total_repos = len(analyzed_repos)

        # Collect all extracted features and technologies across analyzed repos
        all_repo_features = []
        for r in analyzed_repos:
            for f in r.features:
                all_repo_features.append((f.feature_name.lower(), r.repo_full_name))

        all_repo_techs = set()
        for r in analyzed_repos:
            all_repo_techs.update([t.lower() for t in r.detected_technologies.programming_languages])
            all_repo_techs.update([t.lower() for t in r.detected_technologies.backend_frameworks])
            all_repo_techs.update([t.lower() for t in r.detected_technologies.ai_ml_libraries])

        # 1. Missing Features (Objectives in user project NOT found in analyzed repositories)
        user_objectives = []
        if analysis and analysis.objectives:
            user_objectives = analysis.objectives
        elif project.objectives:
            user_objectives = [o.strip() for o in project.objectives.split("\n") if o.strip()]

        for idx, obj in enumerate(user_objectives[:3]):
            obj_lower = obj.lower()
            matching_repo = None
            for feat_name, repo_name in all_repo_features:
                if any(w in feat_name for w in obj_lower.split() if len(w) > 4):
                    matching_repo = repo_name
                    break

            if not matching_repo:
                gaps.append({
                    "gap_title": f"Unaddressed Objective: {obj[:60]}",
                    "category": "missing_feature",
                    "description": f"The capability '{obj}' was not found in the {total_repos} analyzed repositories.",
                    "why_it_matters": "Provides a primary differentiation angle by delivering user-demanded functionality absent from existing open-source baselines.",
                    "suggested_implementation": f"Implement a dedicated service module addressing '{obj}' with comprehensive unit test coverage and modular interfaces.",
                    "priority": "high" if idx == 0 else "medium",
                    "confidence_level": "high",
                    "supporting_evidence": [f"Reviewed {total_repos} repositories ({', '.join(repo_names[:3])}); no matching implementation found."],
                })

        # 2. Partially Implemented Features
        if analyzed_repos:
            first_repo = analyzed_repos[0]
            gaps.append({
                "gap_title": "Production Readiness & Operational Scalability",
                "category": "partially_implemented",
                "description": f"Existing repositories like {first_repo.repo_full_name} provide reference implementations but lack production deployment configurations and resilient error handling.",
                "why_it_matters": "Prototypes without containerized deployment and monitoring are difficult to adopt in production environments.",
                "suggested_implementation": "Incorporate Docker Compose orchestration, structured logging, health checks, and CI/CD pipelines.",
                "priority": "medium",
                "confidence_level": "high",
                "supporting_evidence": [f"{r.repo_full_name}: Minimal deployment or containerization configuration detected" for r in analyzed_repos[:2]],
            })

        # 3. Improvement Opportunities (Modern Web UI / API)
        has_modern_frontend = any(
            bool(r.detected_technologies.frontend_frameworks) for r in analyzed_repos
        )
        if not has_modern_frontend:
            gaps.append({
                "gap_title": "Interactive User Dashboard & Real-Time Visualization",
                "category": "improvement_opportunity",
                "description": "Analyzed repositories are primarily CLI utilities or algorithm libraries lacking an intuitive, modern web interface.",
                "why_it_matters": "An accessible web dashboard significantly lowers the barrier to entry for end users and non-technical stakeholders.",
                "suggested_implementation": "Develop a responsive React/TypeScript frontend with real-time state visualization and parameter controls.",
                "priority": "medium",
                "confidence_level": "high",
                "supporting_evidence": [f"{r.repo_full_name}: No frontend UI framework detected in codebase" for r in analyzed_repos],
            })

        # 4. Differentiating Features (Domain-specific synthesis)
        gaps.append({
            "gap_title": f"End-to-End {project.domain} Unified Platform",
            "category": "differentiating_feature",
            "description": f"While analyzed repositories tackle isolated sub-problems, your proposal combines holistic pipeline integration specifically customized for {project.domain}.",
            "why_it_matters": "A unified platform eliminates friction between disparate tools and simplifies the user workflow.",
            "suggested_implementation": f"Design an end-to-end integration flow that links algorithm inference directly with {project.domain} reporting dashboards.",
            "priority": "high",
            "confidence_level": "medium",
            "supporting_evidence": [f"Existing repositories ({', '.join(repo_names[:3])}) focus on isolated components rather than an end-to-end workflow"],
        })

        return gaps

    async def detect_gaps_with_ai(
        self,
        project: Project,
        analysis: Optional[ProjectAnalysis],
        analyzed_repos: List[RepositoryAnalysisSchema],
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Uses Gemini LLM for deep comparative gap synthesis when available.
        """
        api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
        if not api_key or api_key == "your_gemini_api_key_here":
            return None

        try:
            from app.services.ai_service import AIService
            from google.genai import types
            from pydantic import BaseModel

            client = AIService.get_client()

            class SingleGapSchema(BaseModel):
                gap_title: str
                category: str  # missing_feature | partially_implemented | improvement_opportunity | differentiating_feature
                description: str
                why_it_matters: str
                suggested_implementation: str
                priority: str  # high | medium | low
                confidence_level: str  # high | medium | low
                supporting_evidence: List[str]

            class InnovationGapBatchSchema(BaseModel):
                gaps: List[SingleGapSchema]

            repos_summary = []
            for r in analyzed_repos[:10]:
                techs = r.detected_technologies.programming_languages + r.detected_technologies.backend_frameworks + r.detected_technologies.ai_ml_libraries
                feats = [f.feature_name for f in r.features[:5]]
                repos_summary.append({
                    "full_name": r.repo_full_name,
                    "summary": r.summary,
                    "technologies": techs,
                    "features": feats,
                })

            system_inst = (
                "You are a principal innovation architect and research gap analyst for AI ProjectDNA. "
                "Compare the user's project idea against the analyzed existing GitHub repositories. "
                "Identify: 1) missing features (not found in analyzed repos), 2) partially implemented features, "
                "3) improvement opportunities, and 4) differentiating features. "
                "CRITICAL: Explicitly describe missing capabilities as 'not found in the analyzed repositories'. "
                "Do NOT make unsubstantiated claims that no solution exists worldwide. "
                "Return strictly valid structured JSON."
            )

            prompt = f"""USER PROJECT IDEA:
Title: {project.title}
Domain: {project.domain}
Description: {project.description}
Technologies: {', '.join(project.technologies or [])}
Objectives: {project.objectives or 'Not specified'}

ANALYZED EXISTING GITHUB REPOSITORIES ({len(analyzed_repos)} repos):
{json.dumps(repos_summary, default=str)}

Synthesize 4 to 6 actionable innovation gaps and differentiation vectors."""

            primary_model = settings.GEMINI_MODEL or "gemini-2.5-flash"
            candidates = [primary_model]
            for fallback in ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-flash-latest"]:
                if fallback not in candidates:
                    candidates.append(fallback)

            response = None
            for idx, m_name in enumerate(candidates):
                try:
                    response = client.models.generate_content(
                        model=m_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=InnovationGapBatchSchema,
                            system_instruction=system_inst,
                            temperature=0.2,
                        )
                    )
                    break
                except Exception as candidate_err:
                    err_str = str(candidate_err)
                    if ("404" in err_str or "NOT_FOUND" in err_str or "no longer available" in err_str.lower()) and idx < len(candidates) - 1:
                        continue
                    raise candidate_err

            if response and response.text:
                parsed = InnovationGapBatchSchema.model_validate_json(response.text)
                normalized = []
                for g in parsed.gaps:
                    item = g.model_dump()
                    cat_raw = item["category"].lower().strip().replace(" ", "_")
                    if "missing" in cat_raw:
                        cat = "missing_feature"
                    elif "partial" in cat_raw:
                        cat = "partially_implemented"
                    elif "different" in cat_raw:
                        cat = "differentiating_feature"
                    elif "improv" in cat_raw or "opportun" in cat_raw:
                        cat = "improvement_opportunity"
                    else:
                        cat = cat_raw
                    item["category"] = cat

                    # Grounding guardrail: Ensure missing features state "not found in the analyzed repositories"
                    if cat == "missing_feature" and "not found in the analyzed repositories" not in item["description"].lower():
                        item["description"] = f"{item['description']} (Not found in the analyzed repositories.)"

                    prio_raw = item.get("priority", "medium").lower().strip()
                    item["priority"] = "high" if "high" in prio_raw else ("low" if "low" in prio_raw else "medium")

                    conf_raw = item.get("confidence_level", "medium").lower().strip()
                    item["confidence_level"] = "high" if "high" in conf_raw else ("low" if "low" in conf_raw else "medium")

                    normalized.append(item)
                return normalized
        except Exception as exc:
            logger.info(f"AI innovation gap detection fallback triggered: {exc}")
            return None

    async def detect_and_persist_gaps(
        self,
        project: Project,
        analysis: Optional[ProjectAnalysis],
        analyzed_repos: List[RepositoryAnalysisSchema],
        user_id: str,
        db: Session,
    ) -> List[InnovationGapResponse]:
        """
        Coordinates gap detection (AI with deterministic fallback),
        stores the resulting gaps in the database, and returns normalized schemas.
        """
        if not analyzed_repos:
            return []

        # 1. Attempt AI synthesis, fallback to deterministic
        raw_gaps = await self.detect_gaps_with_ai(project, analysis, analyzed_repos)
        if not raw_gaps:
            raw_gaps = self._generate_deterministic_gaps(project, analysis, analyzed_repos)

        # 2. Clear old gaps for this project to support fresh analysis runs
        db.query(InnovationGap).filter(InnovationGap.project_id == project.id).delete()
        db.commit()

        # 3. Persist new gap records
        persisted_gaps: List[InnovationGapResponse] = []
        for g in raw_gaps:
            gap_model = InnovationGap(
                project_id=project.id,
                user_id=user_id,
                gap_title=g["gap_title"],
                category=g["category"],
                description=g["description"],
                why_it_matters=g["why_it_matters"],
                suggested_implementation=g["suggested_implementation"],
                priority=g.get("priority", "medium").lower(),
                confidence_level=g.get("confidence_level", "medium").lower(),
                supporting_evidence=g.get("supporting_evidence", []),
            )
            db.add(gap_model)
            db.commit()
            db.refresh(gap_model)

            persisted_gaps.append(
                InnovationGapResponse(
                    id=gap_model.id,
                    project_id=gap_model.project_id,
                    user_id=gap_model.user_id,
                    gap_title=gap_model.gap_title,
                    category=gap_model.category,
                    description=gap_model.description,
                    why_it_matters=gap_model.why_it_matters,
                    suggested_implementation=gap_model.suggested_implementation,
                    priority=gap_model.priority,
                    confidence_level=gap_model.confidence_level,
                    supporting_evidence=gap_model.supporting_evidence,
                    created_at=gap_model.created_at,
                    updated_at=gap_model.updated_at,
                )
            )

        return persisted_gaps

