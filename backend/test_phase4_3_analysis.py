import sys
import uuid
import time
import asyncio
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException

sys.path.insert(0, 'backend')

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.user import User
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.github_repo import GitHubRepository
from app.models.repository_analysis import RepositoryAnalysis
from app.models.innovation_gap import InnovationGap
from app.schemas.repository_analysis import (
    TechnologyStackResponse,
    ExtractedFeatureResponse,
    ArchitectureAnalysisResponse,
    SimilarityAnalysisResponse,
    RepositoryAnalysisSchema,
    InnovationGapResponse,
    RepositoryAnalysisRequest,
)
from app.services.github.base import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubTimeoutError,
)
from app.services.github.tech_detector import (
    detect_technologies,
    parse_requirements_txt,
    parse_package_json,
    parse_pyproject_toml,
)
from app.services.github.similarity_service import (
    calculate_similarity,
    calculate_jaccard,
    tokenize,
)
from app.services.github.repository_analyzer import RepositoryAnalyzer
from app.services.github.innovation_gap_service import InnovationGapService
from app.routes.repository_analysis import (
    analyze_repositories,
    get_stored_repository_analyses,
    get_single_repository_analysis,
    get_innovation_gaps,
    get_analysis_stats,
)

SAMPLE_README_CONTENT = """# SkyFleet UAV Air Routing

Autonomous multi-agent UAV routing and collision avoidance using reinforcement learning.

## Overview
SkyFleet provides decentralized 3D trajectory deconfliction for lower-altitude drone logistics.
Designed for crowded urban delivery networks.

## Features
- Dynamic 3D Path Planning: Real-time recalculation of flight trajectories using deep Q-learning.
- Geofencing Boundary Enforcement: Keeps drones strictly within designated commercial air corridors.
- Collision Avoidance Protocol: Inter-vehicle broadcast protocol with sub-millisecond failover.
- Hardware-in-the-Loop Simulation: Integrated PX4 and Gazebo bridge for synthetic stress testing.

## Tech Stack
- Python 3.10+
- PyTorch 2.0
- ROS 2 Humble
- FastAPI for telemetry ingestion
- PostgreSQL with PostGIS
- Docker for containerized deployment

## Installation
```bash
pip install -r requirements.txt
docker-compose up -d
```
"""

SAMPLE_REQUIREMENTS_TXT = """torch>=2.0.0
fastapi==0.110.0
psycopg2-binary>=2.9.5
rclpy>=0.9.0
numpy>=1.24.0
scikit-learn
"""

SAMPLE_PACKAGE_JSON = """{
  "name": "uav-dashboard",
  "dependencies": {
    "react": "^18.2.0",
    "tailwindcss": "^3.3.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "jest": "^29.0.0"
  }
}"""

SAMPLE_PYPROJECT_TOML = """[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.110.0"
torch = "^2.0.0"
"""

def make_mock_client(mock_resp=None, side_effect=None):
    mock_client = AsyncMock()
    if side_effect:
        mock_client.get.side_effect = side_effect
    else:
        mock_client.get.return_value = mock_resp
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client
    mock_cm.__aexit__.return_value = None
    return mock_cm

def run_tests():
    print("================================================================")
    print(">>> AI ProjectDNA - PHASE 4.3 REPO ANALYSIS & GAPS TESTS <<<")
    print("================================================================")

    # 0. Initialize Database Tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create Test Users
    user_a = User(
        id=str(uuid.uuid4()),
        full_name="Deep Analysis Lead A",
        email=f"analyzer_a_{int(time.time())}@projectdna.io",
        hashed_password="hashed_pass_a"
    )
    user_b = User(
        id=str(uuid.uuid4()),
        full_name="Unauthorized User B",
        email=f"analyzer_b_{int(time.time())}@projectdna.io",
        hashed_password="hashed_pass_b"
    )
    db.add_all([user_a, user_b])
    db.commit()

    # Create Test Project
    project_a = Project(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        title="Autonomous Drone Delivery Routing & Collision Avoidance",
        description="Decentralized multi-drone routing and 3D geofencing system for urban airspace logistics.",
        domain="Robotics & Autonomous Systems",
        technologies=["ROS 2", "Python", "PyTorch", "FastAPI"],
        objectives="1. Implement real-time 3D flight trajectory planning.\n2. Prevent urban airspace collisions.\n3. Integrate weather sensor telemetry.\n4. Deliver an interactive web dashboard for dispatchers."
    )
    db.add(project_a)
    db.commit()

    # Create Test ProjectAnalysis (Phase 3)
    analysis_a = ProjectAnalysis(
        id=str(uuid.uuid4()),
        project_id=project_a.id,
        user_id=user_a.id,
        version=1,
        project_summary="Autonomous drone delivery routing network with reinforcement learning.",
        problem_statement="Congested low-altitude airspace delivery corridors risk vehicle collisions.",
        proposed_solution="Decentralized reinforcement learning navigation with real-time geofencing.",
        primary_domain="Robotics",
        secondary_domains=["Artificial Intelligence", "Transportation"],
        keywords=["UAV", "Path Planning", "Geofencing", "Collision Avoidance", "ROS 2"],
        user_technologies=["ROS 2", "Python", "PyTorch", "FastAPI"],
        recommended_technologies={"backend": ["FastAPI", "PostgreSQL"], "ai": ["PyTorch", "Ray"]},
        objectives=[
            "Implement real-time 3D flight trajectory planning.",
            "Prevent urban airspace collisions.",
            "Integrate weather sensor telemetry.",
            "Deliver an interactive web dashboard for dispatchers."
        ],
        target_users=["Urban Delivery Fleets", "Logistics Operators"],
        project_type="Applied Engineering & Research",
        difficulty_level="Advanced",
        difficulty_reasoning="Requires real-time distributed deconfliction.",
        requirements={"hardware": ["PX4 Flight Controller"], "software": ["ROS 2"]},
        assumptions=["GPS signal is uninterrupted"],
        risks={"technical": ["Latency spikes"]},
        model_name="gemini-2.5-flash",
        analysis_status="completed"
    )
    db.add(analysis_a)
    db.commit()

    # Create Discovered GitHub Repositories (Phase 4.2)
    repo_1 = GitHubRepository(
        id=str(uuid.uuid4()),
        project_id=project_a.id,
        analysis_id=analysis_a.id,
        user_id=user_a.id,
        github_repository_id=1010101,
        full_name="skyfleet/uav-air-routing",
        name="uav-air-routing",
        owner_login="skyfleet",
        html_url="https://github.com/skyfleet/uav-air-routing",
        description="Autonomous multi-agent UAV routing and collision avoidance using reinforcement learning.",
        language="Python",
        topics=["uav", "reinforcement-learning", "robotics", "ros2"],
        stargazers_count=850,
        forks_count=140
    )
    repo_2 = GitHubRepository(
        id=str(uuid.uuid4()),
        project_id=project_a.id,
        analysis_id=analysis_a.id,
        user_id=user_a.id,
        github_repository_id=2020202,
        full_name="aerolab/drone-geofencing-sim",
        name="drone-geofencing-sim",
        owner_login="aerolab",
        html_url="https://github.com/aerolab/drone-geofencing-sim",
        description="3D urban airspace geofencing corridor simulator for low-altitude delivery drones.",
        language="C++",
        topics=["geofencing", "simulation", "uav"],
        stargazers_count=320,
        forks_count=45
    )
    db.add_all([repo_1, repo_2])
    db.commit()

    analyzer = RepositoryAnalyzer()
    gap_service = InnovationGapService()

    # TEST 1: Successful README Retrieval
    print("\n[TEST 1] Successful README Retrieval (fetch_readme):")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_README_CONTENT
    mock_resp.headers = {"content-type": "text/plain"}
    with patch("httpx.AsyncClient", return_value=make_mock_client(mock_resp)):
        present, content, url, size = asyncio.run(analyzer.fetch_readme("skyfleet", "uav-air-routing"))
        print(f"  [OK] README Present: {present}, Size: {size} bytes, URL: {url}")
        assert present is True
        assert "Dynamic 3D Path Planning" in content
        assert size > 200

    # TEST 2: Missing README Handling
    print("\n[TEST 2] Missing README Handling (404 gracefully handled):")
    mock_resp404 = MagicMock()
    mock_resp404.status_code = 404
    with patch("httpx.AsyncClient", return_value=make_mock_client(mock_resp404)):
        present, content, url, size = asyncio.run(analyzer.fetch_readme("sparseorg", "empty-repo"))
        print(f"  [OK] Missing README correctly handled: Present={present}, Content={content}")
        assert present is False
        assert content is None

    # TEST 3: README Parsing
    print("\n[TEST 3] README Parsing (Headers, Bullet points, Code blocks):")
    features = analyzer.extract_features_deterministic(SAMPLE_README_CONTENT, repo_1.to_dict())
    print(f"  [OK] Extracted {len(features)} features from markdown bullet points")
    assert len(features) >= 3
    feature_names = [f.feature_name for f in features]
    assert any("Dynamic 3D Path Planning" in fn or "Path Planning" in fn for fn in feature_names)
    assert any("Geofencing" in fn for fn in feature_names)

    # TEST 4: Technology Extraction
    print("\n[TEST 4] Technology Extraction (Categorization into 7 Standard Categories):")
    tech_stack = detect_technologies(
        repo_meta=repo_1.to_dict(),
        readme_text=SAMPLE_README_CONTENT,
        dependency_files={"requirements.txt": SAMPLE_REQUIREMENTS_TXT},
    )
    print(f"  [OK] Languages: {tech_stack.programming_languages}")
    print(f"  [OK] Backend: {tech_stack.backend_frameworks}")
    print(f"  [OK] AI/ML: {tech_stack.ai_ml_libraries}")
    print(f"  [OK] Databases: {tech_stack.databases}")
    assert "Python" in tech_stack.programming_languages
    assert "FastAPI" in tech_stack.backend_frameworks
    assert "PyTorch" in tech_stack.ai_ml_libraries
    assert "PostgreSQL" in tech_stack.databases

    # TEST 5: Dependency File Parsing
    print("\n[TEST 5] Dependency File Parsing (requirements.txt, package.json, pyproject.toml):")
    req_pkgs = parse_requirements_txt(SAMPLE_REQUIREMENTS_TXT)
    pkg_deps = parse_package_json(SAMPLE_PACKAGE_JSON)
    pyproj_deps = parse_pyproject_toml(SAMPLE_PYPROJECT_TOML)
    print(f"  [OK] Parsed {len(req_pkgs)} requirements.txt packages: {req_pkgs}")
    print(f"  [OK] Parsed {len(pkg_deps)} package.json dependencies: {pkg_deps}")
    print(f"  [OK] Parsed {len(pyproj_deps)} pyproject.toml dependencies: {pyproj_deps}")
    assert "torch" in req_pkgs
    assert "fastapi" in req_pkgs
    assert "react" in pkg_deps
    assert "fastapi" in pyproj_deps

    # TEST 6: Feature Extraction
    print("\n[TEST 6] Feature Extraction (Attributes & Documented Flag):")
    feat_1 = features[0]
    print(f"  [OK] Feature: '{feat_1.feature_name}' | Confidence: {feat_1.confidence_score} | Documented: {feat_1.is_documented}")
    assert feat_1.confidence_score >= 0.7
    assert feat_1.is_documented is True
    assert "README" in feat_1.evidence_source

    # TEST 7: Evidence Validation
    print("\n[TEST 7] Evidence Validation (Traceable Proof for Every Detected Tech):")
    for tech, evidence_list in tech_stack.evidence.items():
        assert len(evidence_list) >= 1, f"No evidence for tech: {tech}"
    print(f"  [OK] All {len(tech_stack.evidence)} detected technologies have verified evidence sources: {list(tech_stack.evidence.keys())[:5]}")

    # TEST 8: Similarity Calculation
    print("\n[TEST 8] Similarity Calculation (Composite & Transparent Breakdown):")
    sim = calculate_similarity(
        project=project_a,
        analysis=analysis_a,
        repo=repo_1,
        tech_stack=tech_stack,
        features=features,
        readme_text=SAMPLE_README_CONTENT,
    )
    print(f"  [OK] Overall Score: {sim.overall_score}%")
    print(f"  [OK] Problem: {sim.problem_similarity_score}%, Feature: {sim.feature_similarity_score}%")
    print(f"  [OK] Technology: {sim.technology_overlap_score}%, Domain: {sim.domain_similarity_score}%")
    print(f"  [OK] Rationale: {sim.explanation[:80]}...")
    assert 0.0 <= sim.overall_score <= 100.0
    assert sim.technology_overlap_score > 0.0  # Python, FastAPI, PyTorch match
    assert len(sim.explanation) > 20

    # TEST 9: Innovation Gap Detection
    print("\n[TEST 9] Innovation Gap Detection (Categories, Priority, Evidence):")
    sample_analysis_schema = RepositoryAnalysisSchema(
        project_id=project_a.id,
        github_repo_id=repo_1.id,
        repo_full_name=repo_1.full_name,
        readme_present=True,
        summary="UAV path planning library",
        detected_technologies=tech_stack,
        architecture=ArchitectureAnalysisResponse(backend_services=["FastAPI"]),
        features=features,
        similarity=sim,
    )
    gaps = asyncio.run(
        gap_service.detect_and_persist_gaps(
            project=project_a,
            analysis=analysis_a,
            analyzed_repos=[sample_analysis_schema],
            user_id=user_a.id,
            db=db,
        )
    )
    print(f"  [OK] Identified {len(gaps)} innovation gaps:")
    for g in gaps:
        print(f"    - [{g.priority.upper()}] ({g.category}): {g.gap_title}")
    assert len(gaps) >= 3
    # Check that missing features are explicitly phrased as "not found in the analyzed repositories"
    missing_gaps = [g for g in gaps if g.category == "missing_feature"]
    assert len(missing_gaps) >= 1
    assert "not found in the" in missing_gaps[0].description.lower()

    # TEST 10: Duplicate Analysis Prevention
    print("\n[TEST 10] Duplicate Analysis Prevention (Update in-place):")
    with patch.object(analyzer, "fetch_readme", return_value=(True, SAMPLE_README_CONTENT, "url", 500)), \
         patch.object(analyzer, "fetch_dependency_files", return_value={"requirements.txt": SAMPLE_REQUIREMENTS_TXT}):
        
        # Run 1
        res1 = asyncio.run(analyzer.analyze_single_repository(project_a, analysis_a, repo_1, user_a.id, db, force_refresh=True))
        # Run 2 (force_refresh=True to update in place)
        res2 = asyncio.run(analyzer.analyze_single_repository(project_a, analysis_a, repo_1, user_a.id, db, force_refresh=True))

        analyses_count = db.query(RepositoryAnalysis).filter(
            RepositoryAnalysis.project_id == project_a.id,
            RepositoryAnalysis.github_repo_id == repo_1.id,
        ).count()
        print(f"  [OK] Total analysis records for repo 1 in DB: {analyses_count}")
        assert analyses_count == 1
        assert res1.id == res2.id

    # TEST 11: Database Persistence
    print("\n[TEST 11] Database Persistence (Foreign keys and Cascade):")
    db_record = db.query(RepositoryAnalysis).filter(RepositoryAnalysis.id == res1.id).first()
    assert db_record is not None
    assert db_record.repo_full_name == "skyfleet/uav-air-routing"
    assert "Python" in db_record.detected_technologies["programming_languages"]
    print(f"  [OK] Confirmed DB record persistence with ID: {db_record.id}")

    # TEST 12: Repository Analysis Retrieval Endpoint
    print("\n[TEST 12] Repository Analysis Retrieval Endpoint (GET /analysis):")
    list_res = get_stored_repository_analyses(project_id=project_a.id, page=1, page_size=10, current_user=user_a, db=db)
    print(f"  [OK] Retrieved {list_res.total} stored analysis record(s)")
    assert list_res.total == 1
    assert list_res.items[0].repo_full_name == "skyfleet/uav-air-routing"

    # TEST 13: Project Ownership Enforcement
    print("\n[TEST 13] Project Ownership Enforcement:")
    single_res = get_single_repository_analysis(project_id=project_a.id, analysis_id=res1.id, current_user=user_a, db=db)
    print(f"  [OK] User A successfully verified ownership and accessed: '{single_res.repo_full_name}'")
    assert single_res.id == res1.id

    # TEST 14: Cross-User Access Rejection
    print("\n[TEST 14] Cross-User Access Rejection (403 Forbidden):")
    try:
        get_stored_repository_analyses(project_id=project_a.id, current_user=user_b, db=db)
        assert False, "Should raise 403 Forbidden"
    except HTTPException as e:
        print(f"  [OK] Correctly rejected User B: Status {e.status_code} - {e.detail}")
        assert e.status_code == 403

    try:
        get_stored_repository_analyses(project_id="non-existent-proj", current_user=user_a, db=db)
        assert False, "Should raise 404 Not Found"
    except HTTPException as e:
        print(f"  [OK] Correctly rejected invalid project: Status {e.status_code} - {e.detail}")
        assert e.status_code == 404

    # TEST 15: GitHub 401 Authentication Error Handling
    print("\n[TEST 15] GitHub 401 Authentication Error Handling:")
    mock_resp401 = MagicMock()
    mock_resp401.status_code = 401
    with patch("httpx.AsyncClient", return_value=make_mock_client(mock_resp401)):
        try:
            asyncio.run(analyzer.fetch_readme("owner", "repo"))
            assert False, "Should raise GitHubAuthError"
        except GitHubAuthError as e:
            print(f"  [OK] Caught expected GitHubAuthError: {e}")
            assert e.status_code == 401

    # TEST 16: GitHub 403 Rate-Limit Handling
    print("\n[TEST 16] GitHub 403 Rate-Limit Handling:")
    mock_resp403 = MagicMock()
    mock_resp403.status_code = 403
    mock_resp403.text = "API rate limit exceeded"
    mock_resp403.headers = {"x-ratelimit-reset": "1700000000"}
    with patch("httpx.AsyncClient", return_value=make_mock_client(mock_resp403)):
        try:
            asyncio.run(analyzer.fetch_readme("owner", "repo"))
            assert False, "Should raise GitHubRateLimitError"
        except GitHubRateLimitError as e:
            print(f"  [OK] Caught expected GitHubRateLimitError: {e}")
            assert e.status_code == 403
            assert e.reset_time == 1700000000

    # TEST 17: GitHub Timeout Handling
    print("\n[TEST 17] GitHub Timeout Handling:")
    with patch("httpx.AsyncClient", return_value=make_mock_client(side_effect=httpx.TimeoutException("Connection timed out"))):
        try:
            asyncio.run(analyzer.fetch_readme("owner", "repo"))
            assert False, "Should raise GitHubTimeoutError"
        except GitHubTimeoutError as e:
            print(f"  [OK] Caught expected GitHubTimeoutError: {e}")

    # TEST 18: Partial Repository Analysis Failure Handling
    print("\n[TEST 18] Partial Repository Analysis Failure Handling:")
    # Analyze repo_1 succeeds, repo_2 fails
    async def mock_analyze_repo(project, analysis, repo, user_id, db, force_refresh=False):
        if repo.id == repo_1.id:
            return res1
        raise GitHubAPIError("Repository not found or unavailable", 404)

    with patch("app.routes.repository_analysis.RepositoryAnalyzer.analyze_single_repository", side_effect=mock_analyze_repo), \
         patch("app.routes.repository_analysis.InnovationGapService.detect_and_persist_gaps", return_value=gaps):
        batch_res = asyncio.run(
            analyze_repositories(
                project_id=project_a.id,
                payload=RepositoryAnalysisRequest(max_repositories=5),
                current_user=user_a,
                db=db,
            )
        )
        print(f"  [OK] Batch Status: '{batch_res.status}', Analyzed: {batch_res.total_analyzed}, Errors: {list(batch_res.errors.keys())}")
        assert batch_res.status == "partial_success"
        assert batch_res.total_analyzed == 1
        assert len(batch_res.errors) >= 1

    # TEST 19: AI Provider Failure & Deterministic Fallback
    print("\n[TEST 19] AI Provider Failure & Deterministic Fallback:")
    # Simulate Gemini failure raising an exception
    with patch.object(analyzer, "analyze_with_ai", return_value=None), \
         patch.object(analyzer, "fetch_readme", return_value=(True, SAMPLE_README_CONTENT, "url", 500)), \
         patch.object(analyzer, "fetch_dependency_files", return_value={"requirements.txt": SAMPLE_REQUIREMENTS_TXT}):
        fallback_res = asyncio.run(
            analyzer.analyze_single_repository(project_a, analysis_a, repo_2, user_a.id, db, force_refresh=True)
        )
        print(f"  [OK] Fallback completed with mode: '{fallback_res.analysis_mode}', Status: '{fallback_res.analysis_status}'")
        assert fallback_res.analysis_mode == "deterministic_fallback"
        assert fallback_res.analysis_status == "completed"
        assert len(fallback_res.features) >= 1
        assert fallback_res.similarity is not None

    # TEST 20: Innovation Gap Filtering
    print("\n[TEST 20] Innovation Gap Filtering (by priority):")
    high_gaps = get_innovation_gaps(project_id=project_a.id, priority="high", current_user=user_a, db=db)
    medium_gaps = get_innovation_gaps(project_id=project_a.id, priority="medium", current_user=user_a, db=db)
    print(f"  [OK] Filtered Priority=High: {high_gaps.total} gaps")
    print(f"  [OK] Filtered Priority=Medium: {medium_gaps.total} gaps")
    assert high_gaps.total >= 1
    assert all(g.priority == "high" for g in high_gaps.items)

    # TEST 21: Analysis Statistics Endpoint
    print("\n[TEST 21] Analysis Statistics Endpoint (GET /analysis/stats):")
    stats = get_analysis_stats(project_id=project_a.id, current_user=user_a, db=db)
    print(f"  [OK] Total Analyzed Repos: {stats.total_analyzed_repositories}")
    print(f"  [OK] Average Similarity: {stats.average_similarity_score}%")
    print(f"  [OK] Discovered Technologies: {list(stats.technology_distribution.keys())[:5]}")
    print(f"  [OK] Total Features Extracted: {stats.total_features_extracted}")
    print(f"  [OK] Total Innovation Gaps: {stats.innovation_gaps_count}")
    print(f"  [OK] Gaps by Priority: {stats.gaps_by_priority}")
    assert stats.total_analyzed_repositories == 2
    assert stats.average_similarity_score > 0.0
    assert stats.total_features_extracted >= 2
    assert stats.innovation_gaps_count >= 3

    print("\n================================================================")
    print(">>> ALL 21 PHASE 4.3 REPO ANALYSIS & GAPS TESTS PASSED 100%! <<<")
    print("================================================================")

if __name__ == "__main__":
    run_tests()
