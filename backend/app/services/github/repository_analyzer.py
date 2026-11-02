import re
import base64
import logging
from typing import Dict, Any, Optional, Tuple, List
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.github_repo import GitHubRepository
from app.models.repository_analysis import RepositoryAnalysis
from app.schemas.repository_analysis import (
    TechnologyStackResponse,
    ExtractedFeatureResponse,
    ArchitectureAnalysisResponse,
    SimilarityAnalysisResponse,
    RepositoryAnalysisSchema,
)
from app.services.github.base import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubTimeoutError,
    clean_text,
)
from app.services.github.tech_detector import detect_technologies
from app.services.github.similarity_service import calculate_similarity

logger = logging.getLogger("uvicorn.error")

class RepositoryAnalyzer:
    """
    Dedicated analyzer service for GitHub repositories:
    Retrieves README and dependency files, extracts technology stacks,
    parses features and architecture, and computes similarity.
    """

    def __init__(self, token: Optional[str] = None, timeout: Optional[float] = None):
        self.token = token if token is not None else settings.GITHUB_TOKEN
        self.timeout = timeout or settings.GITHUB_ANALYSIS_TIMEOUT

    def _get_headers(self, accept: str = "application/vnd.github+json") -> Dict[str, str]:
        headers = {
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AIProjectDNA/4.3 (Repository Deep Analysis Module; academic innovation validation)",
        }
        if self.token and self.token.strip():
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    async def fetch_readme(self, owner: str, repo: str) -> Tuple[bool, Optional[str], Optional[str], Optional[int]]:
        """
        Retrieves the repository README file via GitHub REST API.
        Returns: (readme_present, readme_text, readme_url, readme_size)
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        headers = self._get_headers(accept="application/vnd.github.raw+json")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)

                if resp.status_code == 200:
                    content = resp.text
                    # Check if response returned raw text or JSON wrapper
                    if resp.headers.get("content-type", "").startswith("application/json") and '"content":' in content:
                        try:
                            data = resp.json()
                            raw_b64 = data.get("content", "")
                            content = base64.b64decode(raw_b64).decode("utf-8", errors="replace")
                            html_url = data.get("html_url")
                            size = data.get("size", len(content))
                            return True, content, html_url, size
                        except Exception:
                            pass
                    html_url = f"https://github.com/{owner}/{repo}#readme"
                    return True, content, html_url, len(content)

                if resp.status_code == 404:
                    logger.info(f"Repository {owner}/{repo} has no README file.")
                    return False, None, None, None

                if resp.status_code == 401:
                    raise GitHubAuthError("Invalid or expired GitHub authentication token (HTTP 401)", 401)

                if resp.status_code == 403:
                    err_msg = resp.text
                    reset_header = resp.headers.get("x-ratelimit-reset")
                    reset_time = int(reset_header) if reset_header and reset_header.isdigit() else None
                    raise GitHubRateLimitError(f"GitHub API rate limit exceeded: {err_msg}", 403, reset_time=reset_time)

                if resp.status_code >= 500:
                    raise GitHubAPIError(f"GitHub server error (HTTP {resp.status_code})", resp.status_code, resp.text)

                logger.warning(f"Unexpected status {resp.status_code} fetching README for {owner}/{repo}")
                return False, None, None, None

        except httpx.TimeoutException as exc:
            logger.warning(f"GitHub README request timed out for {owner}/{repo}: {exc}")
            raise GitHubTimeoutError(f"GitHub request timed out ({exc})")
        except httpx.RequestError as exc:
            logger.warning(f"GitHub README network error for {owner}/{repo}: {exc}")
            raise GitHubAPIError(f"Network error: {str(exc)}")

    async def fetch_dependency_files(self, owner: str, repo: str) -> Dict[str, str]:
        """
        Attempts to fetch common dependency manifests (requirements.txt, package.json, pyproject.toml).
        """
        dep_files = ["requirements.txt", "package.json", "pyproject.toml"]
        results: Dict[str, str] = {}

        headers = self._get_headers(accept="application/vnd.github.raw+json")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for fname in dep_files:
                try:
                    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{fname}"
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        results[fname] = resp.text
                except Exception:
                    # Non-fatal if specific dependency file fetch fails
                    continue
        return results

    def extract_features_deterministic(
        self,
        readme_text: Optional[str],
        repo_meta: Dict[str, Any]
    ) -> List[ExtractedFeatureResponse]:
        """
        Extracts documented features from README headers, bullet points,
        and capability sections without hallucination.
        """
        features: List[ExtractedFeatureResponse] = []
        if not readme_text:
            # Fallback: Infer basic capability from description if available
            desc = repo_meta.get("description")
            if desc:
                features.append(
                    ExtractedFeatureResponse(
                        feature_name="Core Capability",
                        description=desc,
                        evidence_source="Repository Description",
                        confidence_score=0.6,
                        is_documented=False,
                    )
                )
            return features

        # Search for sections like ## Features, ## Key Features, ## Capabilities, ## Highlights
        feature_sections = re.findall(
            r"(?:#+\s*(?:features|capabilities|highlights|what\s+it\s+does|overview|functionality)[^\n]*\n)([\s\S]*?)(?=\n#+|$)",
            readme_text,
            flags=re.IGNORECASE
        )

        section_text = "\n".join(feature_sections) if feature_sections else readme_text[:4000]

        # Extract bullet points: lines starting with -, *, or number.
        bullet_matches = re.findall(r"^\s*[-*•\d\.]+\s*(.+)$", section_text, flags=re.MULTILINE)

        for line in bullet_matches[:12]:
            cleaned = line.strip().strip("*_`")
            if len(cleaned) < 5 or cleaned.startswith("http") or cleaned.startswith("["):
                continue

            # Split feature name from description if format is: "Name: Description" or "Name - Description"
            parts = re.split(r"[:–—\-]\s+", cleaned, maxsplit=1)
            if len(parts) == 2 and len(parts[0]) <= 50:
                name = parts[0].strip()
                desc = parts[1].strip()
            else:
                name = cleaned[:45] + ("..." if len(cleaned) > 45 else "")
                desc = cleaned

            features.append(
                ExtractedFeatureResponse(
                    feature_name=name,
                    description=desc,
                    evidence_source="README Features / Documentation Section",
                    confidence_score=0.85,
                    is_documented=True,
                )
            )

        # If no bullet points found, extract sentences with active capability verbs
        if not features:
            sentences = re.split(r"\.\s+", readme_text[:2000])
            for s in sentences:
                s_clean = s.strip().replace("\n", " ")
                if re.search(r"\b(supports|provides|implements|allows|enables|includes|features)\b", s_clean, re.IGNORECASE):
                    if 15 <= len(s_clean) <= 180:
                        features.append(
                            ExtractedFeatureResponse(
                                feature_name=s_clean[:40] + "...",
                                description=s_clean,
                                evidence_source="README Documentation Excerpt",
                                confidence_score=0.75,
                                is_documented=True,
                            )
                        )
                    if len(features) >= 4:
                        break

        return features

    def extract_architecture_deterministic(
        self,
        tech_stack: TechnologyStackResponse,
        readme_text: Optional[str]
    ) -> ArchitectureAnalysisResponse:
        """
        Constructs system topology and architecture breakdown grounded strictly
        in detected technologies and verified documentation.
        """
        frontend = list(tech_stack.frontend_frameworks)
        backend = list(tech_stack.backend_frameworks)
        databases = list(tech_stack.databases)
        ai_ml = list(tech_stack.ai_ml_libraries)
        deployment = list(tech_stack.cloud_deployment) + list(tech_stack.devops_tools)

        # Detect integrations in README
        integrations: List[str] = []
        if readme_text:
            common_apis = ["REST API", "GraphQL", "gRPC", "WebSocket", "OAuth", "Stripe", "OpenAI API", "GitHub API", "Slack API", "MQTT"]
            for api in common_apis:
                if re.search(rf"\b{re.escape(api)}\b", readme_text, re.IGNORECASE):
                    integrations.append(api)

        # Summary
        summary_parts = []
        if backend:
            summary_parts.append(f"Backend services powered by {', '.join(backend)}")
        if frontend:
            summary_parts.append(f"User interface built with {', '.join(frontend)}")
        if ai_ml:
            summary_parts.append(f"AI/ML pipeline utilizing {', '.join(ai_ml)}")
        if databases:
            summary_parts.append(f"Persistence layer backed by {', '.join(databases)}")
        if deployment:
            summary_parts.append(f"Infrastructure configured for {', '.join(deployment[:3])}")

        arch_summary = ". ".join(summary_parts) + "." if summary_parts else "Modular architecture documented in repository."

        return ArchitectureAnalysisResponse(
            frontend_components=frontend,
            backend_services=backend,
            database_technologies=databases,
            external_integrations=integrations,
            ai_ml_components=ai_ml,
            deployment_configuration=deployment,
            architecture_summary=arch_summary,
        )

    async def analyze_with_ai(
        self,
        project: Project,
        analysis: Optional[ProjectAnalysis],
        repo: GitHubRepository,
        tech_stack: TechnologyStackResponse,
        readme_text: Optional[str],
    ) -> Optional[Tuple[str, str, List[ExtractedFeatureResponse], ArchitectureAnalysisResponse, SimilarityAnalysisResponse]]:
        """
        Uses Gemini LLM for deep semantic synthesis when available.
        Returns: (summary, problem_statement, features, architecture, similarity)
        """
        api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
        if not api_key or api_key == "your_gemini_api_key_here":
            return None

        try:
            from app.services.ai_service import AIService
            from google.genai import types
            from pydantic import BaseModel

            client = AIService.get_client()

            # Define schema for LLM structured output
            class AIAnalysisOutput(BaseModel):
                summary: str
                problem_statement: str
                features: List[ExtractedFeatureResponse]
                architecture: ArchitectureAnalysisResponse
                similarity: SimilarityAnalysisResponse

            system_inst = (
                "You are an expert software architect and technical project auditor for AI ProjectDNA. "
                "Analyze the provided GitHub repository against the user's project idea. "
                "CRITICAL: Ground all outputs strictly in the provided README text and repository metadata. "
                "Do NOT invent features or architectural components without evidence. "
                "Output strictly valid structured JSON."
            )

            readme_snippet = (readme_text or "")[: settings.GITHUB_README_MAX_CHARS]

            user_prompt = f"""USER PROJECT IDEA:
Title: {project.title}
Domain: {project.domain}
Description: {project.description}
Technologies: {', '.join(project.technologies or [])}
Objectives: {project.objectives or 'Not specified'}

GITHUB REPOSITORY TO ANALYZE:
Name: {repo.full_name}
Description: {repo.description or 'None provided'}
Language: {repo.language or 'Not specified'}
Topics: {', '.join(repo.topics or [])}
Detected Technologies: {json.dumps(tech_stack.model_dump(), default=str)}

README CONTENT:
{readme_snippet if readme_snippet else 'No README file available for this repository.'}

Perform deep evidence-grounded analysis and similarity evaluation."""

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
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=AIAnalysisOutput,
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

            if response.text:
                parsed = AIAnalysisOutput.model_validate_json(response.text)
                return (
                    parsed.summary,
                    parsed.problem_statement,
                    parsed.features,
                    parsed.architecture,
                    parsed.similarity,
                )
        except Exception as exc:
            logger.info(f"AI repository deep analysis fallback triggered for {repo.full_name}: {exc}")
            return None

    async def analyze_single_repository(
        self,
        project: Project,
        analysis: Optional[ProjectAnalysis],
        repo: GitHubRepository,
        user_id: str,
        db: Session,
        force_refresh: bool = False,
    ) -> RepositoryAnalysisSchema:
        """
        Executes deep analysis on a single discovered GitHub repository.
        Persists results to PostgreSQL/SQLite, updating existing records safely.
        """
        # 1. Check existing record
        existing = db.query(RepositoryAnalysis).filter(
            RepositoryAnalysis.project_id == project.id,
            RepositoryAnalysis.github_repo_id == repo.id,
        ).first()

        if existing and not force_refresh:
            return RepositoryAnalysisSchema(
                id=existing.id,
                project_id=existing.project_id,
                github_repo_id=existing.github_repo_id,
                user_id=existing.user_id,
                repo_full_name=existing.repo_full_name,
                readme_present=existing.readme_present,
                readme_url=existing.readme_url,
                readme_size=existing.readme_size,
                summary=existing.summary,
                problem_statement=existing.problem_statement,
                detected_technologies=TechnologyStackResponse(**(existing.detected_technologies or {})),
                architecture=ArchitectureAnalysisResponse(**(existing.architecture or {})),
                features=[ExtractedFeatureResponse(**f) for f in (existing.features or [])],
                similarity=SimilarityAnalysisResponse(**(existing.similarity or {})) if existing.similarity else None,
                analysis_status=existing.analysis_status,
                analysis_mode=existing.analysis_mode,
                error_message=existing.error_message,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
            )

        # 2. Fetch README and Manifests
        owner = repo.owner_login
        repo_name = repo.name
        readme_present, readme_text, readme_url, readme_size = await self.fetch_readme(owner, repo_name)
        dep_files = await self.fetch_dependency_files(owner, repo_name)

        # 3. Detect Technologies
        tech_stack = detect_technologies(
            repo_meta=repo.to_dict(),
            readme_text=readme_text,
            dependency_files=dep_files,
        )

        # 4. Attempt AI Semantic Analysis with Deterministic Fallback
        ai_result = await self.analyze_with_ai(project, analysis, repo, tech_stack, readme_text)

        if ai_result:
            summary, problem_stmt, features, architecture, similarity = ai_result
            analysis_mode = "ai_enhanced"
        else:
            # Deterministic Fallback
            summary = (
                repo.description
                or (readme_text[:300].strip() if readme_text else f"Open-source repository '{repo.full_name}'.")
            )
            problem_stmt = (
                f"Addresses implementation challenges in {repo.language or 'software engineering'} related to {', '.join(repo.topics or ['open-source development'])}."
            )
            features = self.extract_features_deterministic(readme_text, repo.to_dict())
            architecture = self.extract_architecture_deterministic(tech_stack, readme_text)
            similarity = calculate_similarity(
                project=project,
                analysis=analysis,
                repo=repo,
                tech_stack=tech_stack,
                features=features,
                readme_text=readme_text,
            )
            analysis_mode = "deterministic_fallback"

        # 5. Persist or Update DB Record
        if existing:
            existing.readme_present = readme_present
            existing.readme_url = readme_url
            existing.readme_size = readme_size
            existing.summary = summary
            existing.problem_statement = problem_stmt
            existing.detected_technologies = tech_stack.model_dump()
            existing.architecture = architecture.model_dump()
            existing.features = [f.model_dump() for f in features]
            existing.similarity = similarity.model_dump() if similarity else {}
            existing.analysis_status = "completed"
            existing.analysis_mode = analysis_mode
            existing.error_message = None
            db.commit()
            db.refresh(existing)
            target_record = existing
        else:
            target_record = RepositoryAnalysis(
                project_id=project.id,
                github_repo_id=repo.id,
                user_id=user_id,
                repo_full_name=repo.full_name,
                readme_present=readme_present,
                readme_url=readme_url,
                readme_size=readme_size,
                summary=summary,
                problem_statement=problem_stmt,
                detected_technologies=tech_stack.model_dump(),
                architecture=architecture.model_dump(),
                features=[f.model_dump() for f in features],
                similarity=similarity.model_dump() if similarity else {},
                analysis_status="completed",
                analysis_mode=analysis_mode,
            )
            db.add(target_record)
            db.commit()
            db.refresh(target_record)

        return RepositoryAnalysisSchema(
            id=target_record.id,
            project_id=target_record.project_id,
            github_repo_id=target_record.github_repo_id,
            user_id=target_record.user_id,
            repo_full_name=target_record.repo_full_name,
            readme_present=target_record.readme_present,
            readme_url=target_record.readme_url,
            readme_size=target_record.readme_size,
            summary=target_record.summary,
            problem_statement=target_record.problem_statement,
            detected_technologies=tech_stack,
            architecture=architecture,
            features=features,
            similarity=similarity,
            analysis_status=target_record.analysis_status,
            analysis_mode=target_record.analysis_mode,
            created_at=target_record.created_at,
            updated_at=target_record.updated_at,
        )

