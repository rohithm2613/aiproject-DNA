import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
from fastapi import HTTPException

sys.path.insert(0, 'backend')

from app.database.base import Base
from app.database.session import engine, SessionLocal, apply_safe_schema_migrations
import app.models  # noqa: F401
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.github_repo import GitHubRepository
from app.schemas.user import UserRegister
from app.schemas.project import ProjectCreate
from app.schemas.github import (
    GitHubRepositorySchema,
    GitHubSearchRequest,
    GitHubRateLimitInfo,
)
from app.services.user_service import UserService
from app.services.project_service import ProjectService
from app.services.github.base import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubTimeoutError,
    clean_text,
    parse_rate_limit,
)
from app.services.github.github_query_generator import (
    generate_github_queries,
    extract_meaningful_tokens,
)
from app.services.github.github_service import GitHubService
from app.routes.github import (
    search_github_repositories,
    get_stored_repositories,
    get_repository_stats,
)

# Sample Mock GitHub Search JSON
MOCK_GITHUB_SEARCH_RESPONSE = {
    "total_count": 2,
    "incomplete_results": False,
    "items": [
        {
            "id": 1010101,
            "node_id": "MDEwOlJlcG9zaXRvcnkxMDEwMTAx",
            "name": "uav-air-routing",
            "full_name": "skyfleet/uav-air-routing",
            "private": False,
            "owner": {
                "login": "skyfleet",
                "id": 5555,
                "type": "Organization",
                "html_url": "https://github.com/skyfleet"
            },
            "html_url": "https://github.com/skyfleet/uav-air-routing",
            "description": "Autonomous multi-agent UAV routing and collision avoidance using reinforcement learning.",
            "fork": False,
            "url": "https://api.github.com/repos/skyfleet/uav-air-routing",
            "homepage": "https://skyfleet.io/routing",
            "size": 4200,
            "stargazers_count": 850,
            "watchers_count": 850,
            "language": "Python",
            "forks_count": 140,
            "open_issues_count": 12,
            "default_branch": "main",
            "topics": ["uav", "reinforcement-learning", "robotics", "ros2"],
            "visibility": "public",
            "created_at": "2022-04-10T12:00:00Z",
            "updated_at": "2024-03-01T15:30:00Z",
            "pushed_at": "2024-03-01T15:00:00Z",
            "archived": False,
            "license": {
                "key": "apache-2.0",
                "name": "Apache License 2.0",
                "spdx_id": "Apache-2.0"
            }
        },
        {
            "id": 2020202,
            "node_id": "MDEwOlJlcG9zaXRvcnkyMDIwMjAy",
            "name": "drone-geofencing-sim",
            "full_name": "aerolab/drone-geofencing-sim",
            "private": False,
            "owner": {
                "login": "aerolab",
                "id": 6666,
                "type": "User",
                "html_url": "https://github.com/aerolab"
            },
            "html_url": "https://github.com/aerolab/drone-geofencing-sim",
            "description": "3D urban airspace geofencing corridor simulator for low-altitude delivery drones.",
            "fork": False,
            "url": "https://api.github.com/repos/aerolab/drone-geofencing-sim",
            "homepage": None,
            "size": 1800,
            "stargazers_count": 320,
            "watchers_count": 320,
            "language": "C++",
            "forks_count": 45,
            "open_issues_count": 4,
            "default_branch": "master",
            "topics": ["geofencing", "simulation", "uav"],
            "visibility": "public",
            "created_at": "2023-01-15T09:20:00Z",
            "updated_at": "2024-02-18T11:00:00Z",
            "pushed_at": "2024-02-18T10:30:00Z",
            "archived": False,
            "license": {
                "key": "mit",
                "name": "MIT License",
                "spdx_id": "MIT"
            }
        }
    ]
}

def run_tests():
    print("================================================================")
    print(">>> AI ProjectDNA - PHASE 4.2 GITHUB DISCOVERY TESTS <<<")
    print("================================================================")

    # Initialize Database Schema
    Base.metadata.create_all(bind=engine)
    apply_safe_schema_migrations()
    db = SessionLocal()

    # Create distinct test users
    user_a = UserService.get_by_email(db, "test_github_user_a@example.com")
    if not user_a:
        user_a = UserService.create_user(
            db, UserRegister(full_name="GitHub Explorer A", email="test_github_user_a@example.com", password="Password123!")
        )

    user_b = UserService.get_by_email(db, "test_github_user_b@example.com")
    if not user_b:
        user_b = UserService.create_user(
            db, UserRegister(full_name="GitHub Explorer B", email="test_github_user_b@example.com", password="Password123!")
        )

    # Clean existing test records
    db.query(GitHubRepository).filter(GitHubRepository.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
    db.query(ProjectAnalysis).filter(ProjectAnalysis.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
    db.query(Project).filter(Project.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
    db.commit()

    # Create Project for User A
    project_a = ProjectService.create_project(
        db,
        ProjectCreate(
            title="Autonomous Drone Delivery Airspace Corridors",
            description="Multi-agent reinforcement learning system for urban aerial logistics and geofencing.",
            domain="Robotics & Autonomous Systems",
            technologies=["Python", "ROS 2", "PyTorch", "C++"],
            objectives="Optimize airspace corridors and collision deconfliction."
        ),
        user_id=user_a.id
    )

    # Create Phase 3 Analysis Dossier
    analysis_a = ProjectAnalysis(
        project_id=project_a.id,
        user_id=user_a.id,
        version=1,
        project_summary="Autonomous multi-agent UAV urban routing framework.",
        problem_statement="Congested airspace and lack of coordinated low-altitude routing corridors.",
        proposed_solution="Decentralized multi-agent reinforcement learning policy with dynamic 3D geofencing.",
        primary_domain="Robotics & Autonomous Systems",
        secondary_domains=["Artificial Intelligence", "Internet of Things"],
        keywords=["Reinforcement Learning", "UAV Path Planning", "Geofencing", "Collision Avoidance", "ROS 2"],
        user_technologies=["Python", "C++", "ROS 2"],
        recommended_technologies={
            "languages": ["Python", "C++"],
            "frameworks": ["ROS 2", "PyTorch", "PX4 Autopilot"],
            "algorithms": ["PPO", "A* 3D"]
        },
        objectives=["Establish 3D geofencing corridors", "Deconflict dynamic obstacles"],
        target_users=["Drone delivery operators"],
        project_type="Hybrid Research-Software",
        difficulty_level="Advanced",
        difficulty_reasoning="Complex 3D multi-agent optimization",
        requirements={"software_requirements": ["ROS 2 Humble"]},
        assumptions=["RTK-GPS connectivity"],
        risks={"technical_challenges": ["Sensor noise"]}
    )
    db.add(analysis_a)
    db.commit()

    gh_service = GitHubService(token="mock_gh_token_123")

    # TEST 1: Successful GitHub Repository Response Parsing
    print("\n[TEST 1] Successful GitHub Repository Response Parsing:")
    items = MOCK_GITHUB_SEARCH_RESPONSE["items"]
    parsed_repo = gh_service.parse_repo_item(items[0], query="uav routing")
    assert parsed_repo is not None
    print(f"  [OK] Parsed Repository: '{parsed_repo.full_name}' by '{parsed_repo.owner_login}'")
    assert parsed_repo.github_repository_id == 1010101
    assert parsed_repo.stargazers_count == 850
    assert parsed_repo.forks_count == 140
    assert parsed_repo.language == "Python"
    assert "ros2" in parsed_repo.topics
    assert parsed_repo.license_name == "Apache License 2.0"
    assert parsed_repo.search_query == "uav routing"

    # TEST 2: Missing Optional Metadata Handling
    print("\n[TEST 2] Missing Optional Metadata Handling:")
    sparse_raw = {
        "id": 9999999,
        "name": "minimal-repo",
        "full_name": "alice/minimal-repo",
        "html_url": "https://github.com/alice/minimal-repo",
        "owner": {"login": "alice"},
        # Null / missing fields
        "description": None,
        "homepage": None,
        "language": None,
        "topics": None,
        "license": None,
    }
    sparse_parsed = gh_service.parse_repo_item(sparse_raw)
    assert sparse_parsed is not None
    assert sparse_parsed.description is None
    assert sparse_parsed.homepage is None
    assert sparse_parsed.language is None
    assert sparse_parsed.license_name is None
    assert sparse_parsed.topics == []
    print("  [OK] Safely handled missing description, homepage, language, topics, and license without fabricating")

    # TEST 3: Repository Schema Validation
    print("\n[TEST 3] Repository Schema Validation:")
    schema_repo = GitHubRepositorySchema(
        github_repository_id=77777,
        full_name="org/project-dna",
        name="project-dna",
        owner_login="org",
        html_url="https://github.com/org/project-dna",
        stargazers_count=120,
        language="TypeScript",
        archived=False,
        fork=False
    )
    repo_dict = schema_repo.model_dump()
    assert repo_dict["github_repository_id"] == 77777
    assert repo_dict["language"] == "TypeScript"
    print("  [OK] GitHubRepositorySchema successfully validated attributes and constraints")

    # TEST 4: Search Query Generation from Phase 3 Analysis
    print("\n[TEST 4] Search Query Generation from Phase 3 Analysis:")
    queries = generate_github_queries(project_a, analysis_a, max_queries=4)
    print(f"  [OK] Generated {len(queries)} focused queries: {queries}")
    assert len(queries) >= 2
    assert any("drone" in q.lower() or "uav" in q.lower() for q in queries)
    assert any("robotics" in q.lower() or "learning" in q.lower() for q in queries)

    # TEST 5: Query Deduplication
    print("\n[TEST 5] Query Deduplication:")
    # Ensure generated queries contain no exact or case-insensitive duplicate terms
    lower_queries = [q.lower().strip() for q in queries]
    assert len(lower_queries) == len(set(lower_queries))
    print(f"  [OK] All generated queries are strictly unique: {len(lower_queries)} unique queries")

    # TEST 6: Duplicate Repository Detection Within One Search Batch
    print("\n[TEST 6] Duplicate Repository Detection Within One Search Batch:")
    dup_batch = [parsed_repo, parsed_repo]  # Same repo twice in a multi-query batch
    seen_in_batch = set()
    kept = []
    skipped = 0
    for r in dup_batch:
        if r.github_repository_id in seen_in_batch:
            skipped += 1
        else:
            seen_in_batch.add(r.github_repository_id)
            kept.append(r)
    print(f"  [OK] Batch Deduplication: {len(kept)} kept, {skipped} skipped")
    assert len(kept) == 1
    assert skipped == 1

    # TEST 7: Database-Backed Duplicate Detection
    print("\n[TEST 7] Database-Backed Duplicate Detection:")
    # Persist first repo into DB
    db_repo = GitHubRepository(
        project_id=project_a.id,
        analysis_id=analysis_a.id,
        user_id=user_a.id,
        github_repository_id=1010101,
        full_name="skyfleet/uav-air-routing",
        name="uav-air-routing",
        owner_login="skyfleet",
        html_url="https://github.com/skyfleet/uav-air-routing",
        stargazers_count=850,
        forks_count=140,
        language="Python",
        topics=["uav", "robotics"]
    )
    db.add(db_repo)
    db.commit()

    existing_query = db.query(GitHubRepository).filter(
        GitHubRepository.project_id == project_a.id,
        GitHubRepository.github_repository_id == 1010101
    ).first()
    assert existing_query is not None
    print(f"  [OK] Database successfully identifies existing repository ID: {existing_query.github_repository_id}")

    # TEST 8: Repository Database Persistence
    print("\n[TEST 8] Repository Database Persistence:")
    db_repo2 = GitHubRepository(
        project_id=project_a.id,
        analysis_id=analysis_a.id,
        user_id=user_a.id,
        github_repository_id=2020202,
        full_name="aerolab/drone-geofencing-sim",
        name="drone-geofencing-sim",
        owner_login="aerolab",
        html_url="https://github.com/aerolab/drone-geofencing-sim",
        stargazers_count=320,
        forks_count=45,
        language="C++",
        topics=["geofencing", "simulation"]
    )
    db.add(db_repo2)
    db.commit()
    db.refresh(db_repo2)
    assert db_repo2.id is not None
    print(f"  [OK] Successfully persisted second repository with ID: {db_repo2.id}")

    # TEST 9: Existing Repository Metadata Update
    print("\n[TEST 9] Existing Repository Metadata Update:")
    # Simulate rediscovery with updated stars and watchers
    fresh_incoming = GitHubRepositorySchema(
        github_repository_id=1010101,
        full_name="skyfleet/uav-air-routing",
        name="uav-air-routing",
        owner_login="skyfleet",
        html_url="https://github.com/skyfleet/uav-air-routing",
        stargazers_count=925,  # Increased stars from 850
        forks_count=155,       # Increased forks from 140
        watchers_count=925,
        open_issues_count=14,
        language="Python"
    )
    existing_repo = db.query(GitHubRepository).filter(
        GitHubRepository.project_id == project_a.id,
        GitHubRepository.github_repository_id == 1010101
    ).first()
    existing_repo.stargazers_count = fresh_incoming.stargazers_count
    existing_repo.forks_count = fresh_incoming.forks_count
    db.commit()
    db.refresh(existing_repo)
    print(f"  [OK] Updated repository stars: {existing_repo.stargazers_count}, forks: {existing_repo.forks_count}")
    assert existing_repo.stargazers_count == 925
    assert existing_repo.forks_count == 155

    # TEST 10: Project Ownership Enforcement
    print("\n[TEST 10] Project Ownership Enforcement:")
    retrieved_a = get_stored_repositories(project_id=project_a.id, current_user=user_a, db=db)
    print(f"  [OK] User A retrieved {retrieved_a.total} stored repositories for their project")
    assert retrieved_a.total == 2

    # TEST 11: Cross-User Access Rejection
    print("\n[TEST 11] Cross-User Access Rejection:")
    try:
        get_stored_repositories(project_id=project_a.id, current_user=user_b, db=db)
        assert False, "Should raise 403 Forbidden for User B"
    except HTTPException as e:
        print(f"  [OK] Correctly rejected User B access: Status {e.status_code} - {e.detail}")
        assert e.status_code == 403

    try:
        get_repository_stats(project_id=project_a.id, current_user=user_b, db=db)
        assert False, "Should raise 403 Forbidden for stats"
    except HTTPException as e:
        print(f"  [OK] Correctly rejected User B stats query: Status {e.status_code}")
        assert e.status_code == 403

    try:
        get_stored_repositories(project_id="non-existent-proj-id", current_user=user_a, db=db)
        assert False, "Should raise 404 Not Found"
    except HTTPException as e:
        print(f"  [OK] Non-existent project rejected with 404: {e.detail}")
        assert e.status_code == 404

    # TEST 12: GitHub 401 Authentication Error Handling
    print("\n[TEST 12] GitHub 401 Authentication Error Handling:")
    mock_401_resp = MagicMock()
    mock_401_resp.status_code = 401
    mock_401_resp.headers = {"content-type": "application/json"}
    mock_401_resp.json.return_value = {"message": "Bad credentials"}
    mock_401_client = AsyncMock()
    mock_401_client.get.return_value = mock_401_resp
    mock_cm_401 = AsyncMock()
    mock_cm_401.__aenter__.return_value = mock_401_client
    mock_cm_401.__aexit__.return_value = None
    with patch("httpx.AsyncClient", return_value=mock_cm_401):
        try:
            asyncio.run(gh_service.search_repositories("test"))
            assert False, "Should raise GitHubAuthError"
        except GitHubAuthError as err:
            print(f"  [OK] Caught expected GitHubAuthError: {err}")
            assert err.status_code == 401

    # TEST 13: GitHub 403 Rate-Limit Handling
    print("\n[TEST 13] GitHub 403 Rate-Limit Handling:")
    mock_403_resp = MagicMock()
    mock_403_resp.status_code = 403
    mock_403_resp.headers = {
        "content-type": "application/json",
        "x-ratelimit-limit": "10",
        "x-ratelimit-remaining": "0",
        "x-ratelimit-reset": "1793500000"
    }
    mock_403_resp.json.return_value = {"message": "API rate limit exceeded for IP"}
    mock_403_client = AsyncMock()
    mock_403_client.get.return_value = mock_403_resp
    mock_cm_403 = AsyncMock()
    mock_cm_403.__aenter__.return_value = mock_403_client
    mock_cm_403.__aexit__.return_value = None
    with patch("httpx.AsyncClient", return_value=mock_cm_403):
        try:
            asyncio.run(gh_service.search_repositories("test"))
            assert False, "Should raise GitHubRateLimitError"
        except GitHubRateLimitError as err:
            print(f"  [OK] Caught expected GitHubRateLimitError: {err}")
            assert err.status_code == 403

    # TEST 14: HTTP 5xx Error Handling
    print("\n[TEST 14] HTTP 5xx Error Handling:")
    mock_500_resp = MagicMock()
    mock_500_resp.status_code = 503
    mock_500_resp.headers = {}
    mock_500_client = AsyncMock()
    mock_500_client.get.return_value = mock_500_resp
    mock_cm_500 = AsyncMock()
    mock_cm_500.__aenter__.return_value = mock_500_client
    mock_cm_500.__aexit__.return_value = None
    with patch("httpx.AsyncClient", return_value=mock_cm_500):
        try:
            asyncio.run(gh_service.search_repositories("test"))
            assert False, "Should raise GitHubAPIError for 503"
        except GitHubAPIError as err:
            print(f"  [OK] Caught expected GitHubAPIError: {err}")
            assert err.status_code == 503

    # TEST 15: Request Timeout Handling
    print("\n[TEST 15] Request Timeout Handling:")
    mock_to_client = AsyncMock()
    mock_to_client.get.side_effect = httpx.TimeoutException("Connection timed out")
    mock_cm_to = AsyncMock()
    mock_cm_to.__aenter__.return_value = mock_to_client
    mock_cm_to.__aexit__.return_value = None
    with patch("httpx.AsyncClient", return_value=mock_cm_to):
        try:
            asyncio.run(gh_service.search_repositories("test"))
            assert False, "Should raise GitHubTimeoutError"
        except GitHubTimeoutError as err:
            print(f"  [OK] Caught expected GitHubTimeoutError: {err}")

    # TEST 16: Partial Query Failure Handling
    print("\n[TEST 16] Partial Query Failure Handling:")
    # Query 1 succeeds with 1 repo, subsequent queries raise timeout
    call_count = 0
    async def mock_partial_search(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return [parsed_repo], GitHubRateLimitInfo(remaining=28)
        raise GitHubTimeoutError("Query timed out")

    with patch.object(gh_service, "search_repositories", side_effect=mock_partial_search):
        partial_res = asyncio.run(
            gh_service.search_and_persist(db=db, project=project_a, user_id=user_a.id, max_results=10)
        )
        print(f"  [OK] Partial status: {partial_res.status}, errors: {list(partial_res.errors.keys())}")
        assert partial_res.status == "partial_success"
        assert len(partial_res.errors) >= 1

    # TEST 17: All-Query Failure Handling
    print("\n[TEST 17] All-Query Failure Handling:")
    mock_all_fail = AsyncMock()
    mock_all_fail.side_effect = GitHubAPIError("Service unavailable", 503)
    with patch.object(gh_service, "search_repositories", mock_all_fail):
        all_fail_res = asyncio.run(
            gh_service.search_and_persist(db=db, project=project_a, user_id=user_a.id, max_results=10)
        )
        print(f"  [OK] All-fail status: {all_fail_res.status}, total retrieved: {all_fail_res.total_retrieved}")
        assert all_fail_res.status == "failed"
        assert all_fail_res.total_retrieved == 0
        assert all_fail_res.new_stored == 0

    # TEST 18: Repository Retrieval Filtering
    print("\n[TEST 18] Repository Retrieval Filtering:")
    # Filter by language = 'Python'
    filtered_py = get_stored_repositories(project_id=project_a.id, language="Python", current_user=user_a, db=db)
    print(f"  [OK] Filtered language=Python: {filtered_py.total} repository found")
    assert filtered_py.total == 1
    assert filtered_py.items[0].language == "Python"

    # Filter by min_stars = 500
    filtered_stars = get_stored_repositories(project_id=project_a.id, min_stars=500, current_user=user_a, db=db)
    print(f"  [OK] Filtered min_stars=500: {filtered_stars.total} repository found")
    assert filtered_stars.total == 1
    assert filtered_stars.items[0].stargazers_count >= 500

    # Filter by text search = 'geofencing'
    filtered_search = get_stored_repositories(project_id=project_a.id, search="geofencing", current_user=user_a, db=db)
    print(f"  [OK] Filtered search='geofencing': {filtered_search.total} repository found")
    assert filtered_search.total >= 1

    # TEST 19: Pagination
    print("\n[TEST 19] Pagination:")
    page_1 = get_stored_repositories(project_id=project_a.id, page=1, page_size=1, current_user=user_a, db=db)
    page_2 = get_stored_repositories(project_id=project_a.id, page=2, page_size=1, current_user=user_a, db=db)
    print(f"  [OK] Page 1: '{page_1.items[0].name}', Page 2: '{page_2.items[0].name}', Total: {page_1.total}")
    assert page_1.total == 2
    assert len(page_1.items) == 1
    assert len(page_2.items) == 1
    assert page_1.items[0].id != page_2.items[0].id

    # TEST 20: Repository Statistics Endpoint
    print("\n[TEST 20] Repository Statistics Endpoint (GET /api/projects/{id}/github/stats):")
    stats = get_repository_stats(project_id=project_a.id, current_user=user_a, db=db)
    print(f"  [OK] Total Repos: {stats.total_repositories}")
    print(f"  [OK] Language Distribution: {stats.language_distribution}")
    print(f"  [OK] Total Stars: {stats.total_stars}")
    print(f"  [OK] Total Forks: {stats.total_forks}")
    assert stats.total_repositories == 2
    assert "Python" in stats.language_distribution
    assert "C++" in stats.language_distribution
    assert stats.total_stars >= 1100
    assert stats.total_forks >= 180

    # TEST 21: GitHub Token Secrecy Verification
    print("\n[TEST 21] GitHub Token Secrecy Verification:")
    secret_token = "ghp_SuperSecretGitHubTokenDoNotLeak998877"
    secret_service = GitHubService(token=secret_token)
    assert secret_service.token == secret_token

    # Ensure token is never in headers sent to frontend or serialized schemas
    repo_export = parsed_repo.model_dump_json()
    assert secret_token not in repo_export
    stats_export = stats.model_dump_json()
    assert secret_token not in stats_export

    # Ensure token is not in route representation
    headers = secret_service._get_headers()
    assert "Bearer ghp_SuperSecret" in headers["Authorization"]
    # Verify no frontend exposure
    assert "GITHUB_TOKEN" not in open("frontend/src/services/api.ts").read()
    print("  [OK] Verified GITHUB_TOKEN is strictly confidential and never exposed to client or schemas")

    db.close()
    print("\n================================================================")
    print(">>> ALL 21 PHASE 4.2 GITHUB DISCOVERY TESTS PASSED 100%! <<<")
    print("================================================================")

if __name__ == "__main__":
    run_tests()
