import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.core.config import settings
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.github_repo import GitHubRepository
from app.schemas.github import (
    GitHubRepositorySchema,
    GitHubSearchResponse,
    GitHubRepositoryListResponse,
    GitHubStatsResponse,
    GitHubRateLimitInfo,
)
from app.services.github.base import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubTimeoutError,
    clean_text,
    parse_rate_limit,
)
from app.services.github.github_query_generator import generate_github_queries

logger = logging.getLogger("uvicorn.error")

class GitHubService:
    """
    Service client for discovering and persisting GitHub repositories
    matching project ideas and Phase 3 analysis dossiers.
    """

    SEARCH_URL = "https://api.github.com/search/repositories"

    def __init__(self, token: Optional[str] = None, timeout: Optional[float] = None):
        self.token = token if token is not None else settings.GITHUB_TOKEN
        self.timeout = timeout or settings.GITHUB_API_TIMEOUT

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AIProjectDNA/4.2 (GitHub Repository Discovery Module; academic innovation validation)",
        }
        if self.token and self.token.strip():
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    def parse_repo_item(self, item: Dict[str, Any], query: Optional[str] = None) -> Optional[GitHubRepositorySchema]:
        """Parses a single raw GitHub repository JSON object into a normalized schema."""
        if not item or not isinstance(item, dict):
            return None

        repo_id = item.get("id")
        full_name = item.get("full_name")
        name = item.get("name")
        html_url = item.get("html_url")
        owner_obj = item.get("owner") or {}
        owner_login = owner_obj.get("login")

        if not repo_id or not full_name or not name or not owner_login or not html_url:
            return None

        license_obj = item.get("license") or {}
        license_name = clean_text(license_obj.get("name") or license_obj.get("spdx_id"))

        # Topics
        raw_topics = item.get("topics") or []
        topics = [clean_text(t) for t in raw_topics if clean_text(t)]

        return GitHubRepositorySchema(
            github_repository_id=int(repo_id),
            full_name=clean_text(full_name) or str(full_name),
            name=clean_text(name) or str(name),
            owner_login=clean_text(owner_login) or str(owner_login),
            owner_type=clean_text(owner_obj.get("type")),
            description=clean_text(item.get("description")),
            html_url=str(html_url),
            homepage=clean_text(item.get("homepage")),
            language=clean_text(item.get("language")),
            languages={},
            topics=topics,
            stargazers_count=int(item.get("stargazers_count") or 0),
            forks_count=int(item.get("forks_count") or 0),
            watchers_count=int(item.get("watchers_count") or item.get("stargazers_count") or 0),
            open_issues_count=int(item.get("open_issues_count") or 0),
            default_branch=clean_text(item.get("default_branch")),
            created_at=clean_text(item.get("created_at")),
            updated_at=clean_text(item.get("updated_at")),
            pushed_at=clean_text(item.get("pushed_at")),
            license_name=license_name,
            archived=bool(item.get("archived", False)),
            fork=bool(item.get("fork", False)),
            visibility=str(item.get("visibility") or "public"),
            size=int(item["size"]) if item.get("size") is not None else None,
            search_query=query,
        )

    async def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30,
        page: int = 1,
    ) -> Tuple[List[GitHubRepositorySchema], GitHubRateLimitInfo]:
        """
        Executes a single search query against GitHub Search API.
        Returns parsed repositories and rate-limit metadata.
        """
        clean_q = clean_text(query)
        if not clean_q:
            return [], GitHubRateLimitInfo()

        params = {
            "q": clean_q,
            "sort": sort if sort in ("stars", "forks", "updated") else "stars",
            "order": order if order in ("asc", "desc") else "desc",
            "per_page": min(max(1, per_page), 100),
            "page": max(1, page),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.SEARCH_URL, params=params, headers=self._get_headers())
                rate_limit = parse_rate_limit(response.headers)

                if response.status_code == 401:
                    raise GitHubAuthError("Invalid or expired GitHub authentication token (HTTP 401)", 401)

                if response.status_code == 403:
                    msg = response.json().get("message", "Forbidden") if response.headers.get("content-type", "").startswith("application/json") else response.text
                    if "rate limit" in msg.lower() or rate_limit.remaining == 0:
                        raise GitHubRateLimitError(f"GitHub API rate limit exceeded: {msg}", 403, rate_limit.reset)
                    raise GitHubAPIError(f"GitHub permission denied: {msg}", 403)

                if response.status_code == 422:
                    logger.warning(f"GitHub query syntax validation error (HTTP 422) for '{query}'")
                    return [], rate_limit

                if response.status_code >= 500:
                    raise GitHubAPIError(f"GitHub server error (HTTP {response.status_code})", response.status_code)

                response.raise_for_status()
                data = response.json()

                raw_items = data.get("items", [])
                repos: List[GitHubRepositorySchema] = []
                for it in raw_items:
                    parsed = self.parse_repo_item(it, query=clean_q)
                    if parsed:
                        repos.append(parsed)

                return repos, rate_limit

            except httpx.TimeoutException as exc:
                logger.warning(f"GitHub request timed out after {self.timeout}s: {exc}")
                raise GitHubTimeoutError(f"GitHub request timed out ({exc})")
            except (GitHubAuthError, GitHubRateLimitError, GitHubAPIError, GitHubTimeoutError):
                raise
            except Exception as exc:
                logger.error(f"Unexpected error communicating with GitHub API: {exc}")
                raise GitHubAPIError(f"GitHub query execution failed: {exc}")

    async def search_and_persist(
        self,
        db: Session,
        project: Project,
        user_id: str,
        analysis_id: Optional[str] = None,
        max_results: int = 30,
        sort: str = "stars",
        order: str = "desc",
    ) -> GitHubSearchResponse:
        """
        Coordinates full GitHub discovery lifecycle:
          1. Resolve latest or specified Phase 3 analysis.
          2. Dynamically generate 2-4 focused queries.
          3. Execute searches sequentially to respect GitHub secondary rate limits.
          4. Deduplicate across queries and against existing database records.
          5. Update existing repository stats or insert new records.
          6. Persist to database and return response with rate limit details.
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
        queries = generate_github_queries(project, target_analysis, max_queries=settings.GITHUB_MAX_QUERIES)

        # 3. Query execution
        queries_executed: List[str] = []
        per_query_counts: Dict[str, int] = {}
        errors: Dict[str, str] = {}
        last_rate_limit: Optional[GitHubRateLimitInfo] = None
        all_incoming_repos: List[GitHubRepositorySchema] = []

        per_query_limit = max(10, max_results // max(1, len(queries)))

        for q in queries:
            queries_executed.append(q)
            try:
                repos, rate_info = await self.search_repositories(
                    query=q,
                    sort=sort,
                    order=order,
                    per_page=per_query_limit,
                    page=1,
                )
                last_rate_limit = rate_info
                per_query_counts[q] = len(repos)
                all_incoming_repos.extend(repos)
            except GitHubAuthError as auth_err:
                errors[q] = auth_err.message
                break  # Don't retry invalid auth
            except GitHubRateLimitError as rate_err:
                errors[q] = rate_err.message
                break  # Don't exhaust further rate limit
            except (GitHubAPIError, GitHubTimeoutError) as err:
                errors[q] = err.message
                continue

        # Determine overall status
        if not all_incoming_repos and errors:
            status = "failed"
        elif errors:
            status = "partial_success"
        else:
            status = "completed"

        # 4. Fetch existing records for this project
        existing_repos = db.query(GitHubRepository).filter(
            GitHubRepository.project_id == project.id
        ).all()
        existing_by_gh_id = {r.github_repository_id: r for r in existing_repos}

        # 5. Deduplicate and Update / Insert
        seen_in_batch = set()
        new_stored = 0
        existing_updated = 0
        duplicates_skipped = 0
        now_dt = datetime.now(timezone.utc)

        for repo in all_incoming_repos:
            gh_id = repo.github_repository_id

            # Batch deduplication check
            if gh_id in seen_in_batch:
                duplicates_skipped += 1
                continue
            seen_in_batch.add(gh_id)

            if gh_id in existing_by_gh_id:
                # Update existing record with fresh statistics
                existing = existing_by_gh_id[gh_id]
                existing.stargazers_count = repo.stargazers_count
                existing.forks_count = repo.forks_count
                existing.watchers_count = repo.watchers_count
                existing.open_issues_count = repo.open_issues_count
                existing.updated_at = repo.updated_at
                existing.pushed_at = repo.pushed_at
                existing.archived = repo.archived
                existing.size = repo.size
                existing.retrieved_at = now_dt
                if repo.description and not existing.description:
                    existing.description = repo.description
                if repo.topics and not existing.topics:
                    existing.topics = repo.topics
                existing_updated += 1
            else:
                # Persist new repository
                new_db_repo = GitHubRepository(
                    project_id=project.id,
                    analysis_id=resolved_analysis_id,
                    user_id=user_id,
                    github_repository_id=repo.github_repository_id,
                    full_name=repo.full_name,
                    name=repo.name,
                    owner_login=repo.owner_login,
                    owner_type=repo.owner_type,
                    description=repo.description,
                    html_url=repo.html_url,
                    homepage=repo.homepage,
                    language=repo.language,
                    languages=repo.languages or {},
                    topics=repo.topics or [],
                    stargazers_count=repo.stargazers_count,
                    forks_count=repo.forks_count,
                    watchers_count=repo.watchers_count,
                    open_issues_count=repo.open_issues_count,
                    default_branch=repo.default_branch,
                    created_at=repo.created_at,
                    updated_at=repo.updated_at,
                    pushed_at=repo.pushed_at,
                    license_name=repo.license_name,
                    archived=repo.archived,
                    fork=repo.fork,
                    visibility=repo.visibility,
                    size=repo.size,
                    search_query=repo.search_query,
                    retrieved_at=now_dt,
                )
                db.add(new_db_repo)
                new_stored += 1

        if new_stored > 0 or existing_updated > 0:
            db.commit()

        # 6. Retrieve stored repositories for this project to return
        total_stored = db.query(GitHubRepository).filter(
            GitHubRepository.project_id == project.id
        ).count()

        recent_db_repos = db.query(GitHubRepository).filter(
            GitHubRepository.project_id == project.id
        ).order_by(desc(GitHubRepository.stargazers_count), desc(GitHubRepository.retrieved_at)).limit(50).all()

        response_repos = [
            GitHubRepositorySchema(
                id=r.id,
                project_id=r.project_id,
                analysis_id=r.analysis_id,
                user_id=r.user_id,
                github_repository_id=r.github_repository_id,
                full_name=r.full_name,
                name=r.name,
                owner_login=r.owner_login,
                owner_type=r.owner_type,
                description=r.description,
                html_url=r.html_url,
                homepage=r.homepage,
                language=r.language,
                languages=r.languages or {},
                topics=r.topics or [],
                stargazers_count=r.stargazers_count,
                forks_count=r.forks_count,
                watchers_count=r.watchers_count,
                open_issues_count=r.open_issues_count,
                default_branch=r.default_branch,
                created_at=r.created_at,
                updated_at=r.updated_at,
                pushed_at=r.pushed_at,
                license_name=r.license_name,
                archived=r.archived,
                fork=r.fork,
                visibility=r.visibility,
                size=r.size,
                search_query=r.search_query,
                retrieved_at=r.retrieved_at,
                created_at_db=r.created_at_db,
            )
            for r in recent_db_repos
        ]

        return GitHubSearchResponse(
            status=status,
            project_id=project.id,
            analysis_id=resolved_analysis_id,
            queries_executed=queries_executed,
            total_retrieved=len(all_incoming_repos),
            new_stored=new_stored,
            existing_updated=existing_updated,
            duplicates_skipped=duplicates_skipped,
            per_query_counts=per_query_counts,
            rate_limit=last_rate_limit,
            errors=errors,
            total_stored_repositories=total_stored,
            repositories=response_repos,
        )

    def get_stored_repositories(
        self,
        db: Session,
        project_id: str,
        language: Optional[str] = None,
        min_stars: Optional[int] = None,
        topic: Optional[str] = None,
        archived: Optional[bool] = None,
        fork: Optional[bool] = None,
        search_text: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> GitHubRepositoryListResponse:
        """Retrieves stored GitHub repositories for a project with optional filters and pagination."""
        query = db.query(GitHubRepository).filter(GitHubRepository.project_id == project_id)

        if language:
            query = query.filter(GitHubRepository.language.ilike(language.strip()))

        if min_stars is not None:
            query = query.filter(GitHubRepository.stargazers_count >= min_stars)

        if archived is not None:
            query = query.filter(GitHubRepository.archived == archived)

        if fork is not None:
            query = query.filter(GitHubRepository.fork == fork)

        if search_text:
            term = f"%{search_text.strip()}%"
            query = query.filter(
                or_(
                    GitHubRepository.full_name.ilike(term),
                    GitHubRepository.description.ilike(term),
                    GitHubRepository.language.ilike(term),
                )
            )

        # Filtering by JSON topics (supported across Postgres & SQLite)
        if topic:
            clean_topic = topic.strip().lower()
            query = query.filter(func.lower(func.cast(GitHubRepository.topics, func.text if db.bind.dialect.name == "sqlite" else func.VARCHAR)).like(f"%{clean_topic}%"))

        total = query.count()
        offset = max(0, (page - 1) * page_size)
        db_items = query.order_by(
            desc(GitHubRepository.stargazers_count),
            desc(GitHubRepository.retrieved_at)
        ).offset(offset).limit(page_size).all()

        items = [
            GitHubRepositorySchema(
                id=r.id,
                project_id=r.project_id,
                analysis_id=r.analysis_id,
                user_id=r.user_id,
                github_repository_id=r.github_repository_id,
                full_name=r.full_name,
                name=r.name,
                owner_login=r.owner_login,
                owner_type=r.owner_type,
                description=r.description,
                html_url=r.html_url,
                homepage=r.homepage,
                language=r.language,
                languages=r.languages or {},
                topics=r.topics or [],
                stargazers_count=r.stargazers_count,
                forks_count=r.forks_count,
                watchers_count=r.watchers_count,
                open_issues_count=r.open_issues_count,
                default_branch=r.default_branch,
                created_at=r.created_at,
                updated_at=r.updated_at,
                pushed_at=r.pushed_at,
                license_name=r.license_name,
                archived=r.archived,
                fork=r.fork,
                visibility=r.visibility,
                size=r.size,
                search_query=r.search_query,
                retrieved_at=r.retrieved_at,
                created_at_db=r.created_at_db,
            )
            for r in db_items
        ]

        return GitHubRepositoryListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        )

    def get_repository_stats(self, db: Session, project_id: str) -> GitHubStatsResponse:
        """Computes summary statistics for stored GitHub repositories of a given project."""
        repos = db.query(GitHubRepository).filter(GitHubRepository.project_id == project_id).all()

        language_dist: Dict[str, int] = {}
        total_stars = 0
        total_forks = 0
        archived_count = 0
        fork_count = 0
        latest_discovery: Optional[datetime] = None

        for r in repos:
            if r.language:
                language_dist[r.language] = language_dist.get(r.language, 0) + 1
            total_stars += r.stargazers_count or 0
            total_forks += r.forks_count or 0
            if r.archived:
                archived_count += 1
            if r.fork:
                fork_count += 1
            if r.retrieved_at:
                if not latest_discovery or r.retrieved_at > latest_discovery:
                    latest_discovery = r.retrieved_at

        return GitHubStatsResponse(
            project_id=project_id,
            total_repositories=len(repos),
            language_distribution=language_dist,
            total_stars=total_stars,
            total_forks=total_forks,
            archived_count=archived_count,
            fork_count=fork_count,
            latest_discovery_at=latest_discovery.isoformat() if latest_discovery else None,
        )

github_service = GitHubService()

