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
from app.models.research_paper import ResearchPaper
from app.schemas.user import UserRegister
from app.schemas.project import ProjectCreate
from app.schemas.research import (
    ResearchPaperSchema,
    ResearchSearchRequest,
)
from app.services.user_service import UserService
from app.services.project_service import ProjectService
from app.services.research.base import (
    normalize_doi,
    clean_text,
    clean_authors,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderAPIError,
)
from app.services.research.arxiv_service import ArxivService
from app.services.research.semantic_scholar_service import SemanticScholarService
from app.services.research.openalex_service import OpenAlexService
from app.services.research.query_generator import generate_research_queries
from app.services.research.research_discovery_service import ResearchDiscoveryService
from app.routes.research import (
    search_research_papers,
    get_stored_research,
    get_research_stats,
)

# Sample mock XML for arXiv
MOCK_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.09876v1</id>
    <title>Deep Autonomous Drone Routing in Urban Corridors</title>
    <summary>This paper proposes a deep reinforcement learning framework for urban UAV airspace routing.</summary>
    <author><name>Dr. Alice Chen</name></author>
    <author><name>Bob Smith</name></author>
    <published>2023-01-20T10:00:00Z</published>
    <arxiv:primary_category term="cs.RO" />
    <link title="pdf" href="http://arxiv.org/pdf/2301.09876v1" type="application/pdf" />
    <arxiv:doi>10.1145/123456.7890</arxiv:doi>
  </entry>
</feed>
"""

# Sample mock JSON for Semantic Scholar
MOCK_SEMANTIC_SCHOLAR_JSON = {
    "total": 1,
    "data": [
        {
            "paperId": "s2_paper_12345",
            "title": "Multi-Agent Reinforcement Learning for Urban Air Mobility",
            "abstract": "We explore decentralized collision avoidance algorithms for multi-agent drone fleets.",
            "authors": [{"authorId": "a1", "name": "Elena Rostova"}, {"authorId": "a2", "name": "Marcus Vance"}],
            "year": 2022,
            "venue": "IEEE Transactions on Intelligent Transportation Systems",
            "externalIds": {"DOI": "10.1109/TITS.2022.987654", "ArXiv": "2205.12345"},
            "citationCount": 42,
            "openAccessPdf": {"url": "https://arxiv.org/pdf/2205.12345.pdf", "status": "gold"},
            "url": "https://www.semanticscholar.org/paper/s2_paper_12345"
        }
    ]
}

# Sample mock JSON for OpenAlex
MOCK_OPENALEX_JSON = {
    "results": [
        {
            "id": "https://openalex.org/W9988776655",
            "title": "Decentralized Airspace Geofencing for UAV Swarms",
            "abstract_inverted_index": {
                "Decentralized": [0],
                "geofencing": [1],
                "provides": [2],
                "robust": [3],
                "airspace": [4],
                "deconfliction.": [5]
            },
            "authorships": [
                {"author": {"id": "https://openalex.org/A1", "display_name": "Karthik Nair"}},
                {"author": {"id": "https://openalex.org/A2", "display_name": "Sarah Jenkins"}}
            ],
            "publication_year": 2024,
            "publication_date": "2024-03-15",
            "primary_location": {
                "source": {"display_name": "Journal of Field Robotics"},
                "landing_page_url": "https://doi.org/10.1002/rob.22150",
                "pdf_url": "https://jfr.org/papers/rob.22150.pdf",
                "is_oa": True
            },
            "open_access": {
                "is_oa": True,
                "oa_url": "https://jfr.org/papers/rob.22150.pdf"
            },
            "doi": "https://doi.org/10.1002/rob.22150",
            "cited_by_count": 18,
            "primary_topic": {"display_name": "Robotics and Control"}
        }
    ]
}

def run_tests():
    print("================================================================")
    print(">>> AI ProjectDNA - PHASE 4.1 RESEARCH DISCOVERY TESTS <<<")
    print("================================================================")

    # Initialize Database Schema
    Base.metadata.create_all(bind=engine)
    apply_safe_schema_migrations()
    db = SessionLocal()

    # Create distinct test users
    user_a = UserService.get_by_email(db, "test_research_user_a@example.com")
    if not user_a:
        user_a = UserService.create_user(
            db, UserRegister(full_name="Researcher A", email="test_research_user_a@example.com", password="Password123!")
        )

    user_b = UserService.get_by_email(db, "test_research_user_b@example.com")
    if not user_b:
        user_b = UserService.create_user(
            db, UserRegister(full_name="Researcher B", email="test_research_user_b@example.com", password="Password123!")
        )

    # Clean existing test projects
    db.query(ResearchPaper).filter(ResearchPaper.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
    db.query(ProjectAnalysis).filter(ProjectAnalysis.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
    db.query(Project).filter(Project.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
    db.commit()

    # Create Project for User A
    project_a = ProjectService.create_project(
        db,
        ProjectCreate(
            title="Autonomous UAV Air Delivery Corridors",
            description="Multi-agent reinforcement learning system for urban air mobility delivery drones.",
            domain="Robotics & Autonomous Systems",
            technologies=["Python", "PyTorch", "ROS 2"],
            objectives="Optimize airspace corridors and collision deconfliction."
        ),
        user_id=user_a.id
    )

    # Create ProjectAnalysis for Project A
    analysis_a = ProjectAnalysis(
        project_id=project_a.id,
        user_id=user_a.id,
        version=1,
        project_summary="Autonomous UAV urban corridor routing framework.",
        problem_statement="Congested airspace and lack of automated lower-altitude routing.",
        proposed_solution="Decentralized multi-agent reinforcement learning routing policy.",
        primary_domain="Robotics & Autonomous Systems",
        secondary_domains=["Artificial Intelligence", "Internet of Things"],
        keywords=["Reinforcement Learning", "UAV Routing", "Urban Air Mobility", "Collision Avoidance"],
        user_technologies=["Python", "PyTorch"],
        recommended_technologies={"languages": ["Python", "C++"], "frameworks": ["ROS 2"]},
        objectives=["Establish 3D geofencing corridors", "Deconflict dynamic obstacles"],
        target_users=["Drone delivery operators"],
        project_type="Research-oriented",
        difficulty_level="Advanced",
        difficulty_reasoning="Complex 3D multi-agent optimization",
        requirements={"software_requirements": ["ROS 2"]},
        assumptions=["GPS connectivity"],
        risks={"technical_challenges": ["Sensor noise"]}
    )
    db.add(analysis_a)
    db.commit()

    # TEST 1: Successful arXiv Response Parsing
    print("\n[TEST 1] Successful arXiv Response Parsing:")
    arxiv_svc = ArxivService()
    arxiv_papers = arxiv_svc.parse_atom_feed(MOCK_ARXIV_XML)
    assert len(arxiv_papers) == 1
    p1 = arxiv_papers[0]
    print(f"  [OK] Parsed arXiv Paper: '{p1.title}' by {p1.authors}")
    assert p1.provider == "arxiv"
    assert p1.provider_paper_id == "2301.09876v1"
    assert p1.publication_year == 2023
    assert p1.open_access is True
    assert p1.doi == "10.1145/123456.7890"
    assert "arxiv.org/pdf" in (p1.pdf_url or "")

    # TEST 2: Successful Semantic Scholar Response Parsing
    print("\n[TEST 2] Successful Semantic Scholar Response Parsing:")
    s2_svc = SemanticScholarService()
    s2_papers = s2_svc.parse_response(MOCK_SEMANTIC_SCHOLAR_JSON)
    assert len(s2_papers) == 1
    p2 = s2_papers[0]
    print(f"  [OK] Parsed Semantic Scholar Paper: '{p2.title}' ({p2.publication_year})")
    assert p2.provider == "semantic_scholar"
    assert p2.provider_paper_id == "s2_paper_12345"
    assert p2.doi == "10.1109/tits.2022.987654"
    assert p2.citation_count == 42
    assert p2.open_access is True

    # TEST 3: Successful OpenAlex Response Parsing & Inverted Index Abstract
    print("\n[TEST 3] Successful OpenAlex Response Parsing:")
    oa_svc = OpenAlexService()
    oa_papers = oa_svc.parse_response(MOCK_OPENALEX_JSON)
    assert len(oa_papers) == 1
    p3 = oa_papers[0]
    print(f"  [OK] Parsed OpenAlex Paper: '{p3.title}'")
    print(f"  [OK] Reconstructed Abstract: '{p3.abstract}'")
    assert p3.provider == "openalex"
    assert p3.provider_paper_id == "W9988776655"
    assert p3.abstract == "Decentralized geofencing provides robust airspace deconfliction."
    assert p3.doi == "10.1002/rob.22150"
    assert p3.citation_count == 18
    assert p3.open_access is True

    # TEST 4: Missing Optional Metadata Handling
    print("\n[TEST 4] Missing Optional Metadata Handling:")
    sparse_arxiv_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2101.00001</id>
        <title>Minimal arXiv Paper Without DOI</title>
      </entry>
    </feed>
    """
    sparse_arxiv = arxiv_svc.parse_atom_feed(sparse_arxiv_xml)
    assert len(sparse_arxiv) == 1
    assert sparse_arxiv[0].doi is None
    assert sparse_arxiv[0].abstract is None
    assert sparse_arxiv[0].authors == []
    print("  [OK] Safely parsed minimal arXiv item without crashing or fabricating fields")

    sparse_s2 = s2_svc.parse_response({"data": [{"paperId": "sparse_1", "title": "Sparse S2 Paper"}]})
    assert len(sparse_s2) == 1
    assert sparse_s2[0].citation_count is None
    assert sparse_s2[0].doi is None
    assert sparse_s2[0].open_access is False
    print("  [OK] Safely parsed minimal Semantic Scholar item with null optional fields")

    sparse_oa = oa_svc.parse_response({"results": [{"id": "https://openalex.org/W_sparse", "title": "Sparse OA"}]})
    assert len(sparse_oa) == 1
    assert sparse_oa[0].abstract is None
    assert sparse_oa[0].doi is None
    assert sparse_oa[0].authors == []
    print("  [OK] Safely handled OpenAlex work without inverted index abstract")

    # TEST 5: Unified Schema Validation
    print("\n[TEST 5] Unified Schema Validation:")
    schema_paper = ResearchPaperSchema(
        provider="arxiv",
        provider_paper_id="2401.12345",
        title="Schema Validation Paper",
        abstract="Testing Pydantic schema validation strictly.",
        authors=["Alice", "Bob"],
        publication_year=2024,
        doi="10.1145/test.doi",
        open_access=True
    )
    schema_dict = schema_paper.model_dump()
    assert schema_dict["provider"] == "arxiv"
    assert schema_dict["publication_year"] == 2024
    print("  [OK] ResearchPaperSchema successfully validated attributes and types")

    # TEST 6: Duplicate Paper Detection
    print("\n[TEST 6] Duplicate Paper Detection:")
    discovery_svc = ResearchDiscoveryService()
    p_dup1 = ResearchPaperSchema(
        provider="arxiv",
        provider_paper_id="2301.09876v1",
        title="Deep Drone Routing",
        doi="10.1145/123456.7890"
    )
    p_dup2 = ResearchPaperSchema(
        provider="semantic_scholar",
        provider_paper_id="s2_dup_id",
        title="Deep Drone Routing Cross-Source",
        doi="10.1145/123456.7890"  # Exact matching normalized DOI
    )
    p_unique = ResearchPaperSchema(
        provider="openalex",
        provider_paper_id="oa_unique_id",
        title="A Truly Different Paper",
        doi="10.1002/different.doi"
    )
    # Deduplicate against empty existing list
    unique_list, dup_count = discovery_svc.deduplicate_papers([p_dup1, p_dup2, p_unique], [])
    print(f"  [OK] Batch Deduplication: {len(unique_list)} unique kept, {dup_count} duplicates skipped")
    assert len(unique_list) == 2  # p_dup2 dropped because of matching DOI
    assert dup_count == 1

    # Deduplicate against existing DB record
    existing_record = ResearchPaper(
        id="existing-1",
        project_id=project_a.id,
        user_id=user_a.id,
        provider="arxiv",
        provider_paper_id="2301.09876v1",
        title="Existing Stored Paper",
        doi="10.1145/123456.7890"
    )
    unique_list2, dup_count2 = discovery_svc.deduplicate_papers([p_dup1, p_unique], [existing_record])
    print(f"  [OK] DB-Backed Deduplication: {len(unique_list2)} unique, {dup_count2} duplicates skipped")
    assert len(unique_list2) == 1
    assert dup_count2 == 1
    assert unique_list2[0].provider_paper_id == "oa_unique_id"

    # TEST 7: Research Paper Database Persistence
    print("\n[TEST 7] Research Paper Database Persistence:")
    test_db_paper = ResearchPaper(
        project_id=project_a.id,
        analysis_id=analysis_a.id,
        user_id=user_a.id,
        provider="arxiv",
        provider_paper_id="2301.09876v1",
        title="Deep Autonomous Drone Routing in Urban Corridors",
        abstract="Reinforcement learning airspace routing.",
        authors=["Dr. Alice Chen", "Bob Smith"],
        publication_year=2023,
        venue="arXiv (cs.RO)",
        doi="10.1145/123456.7890",
        arxiv_id="2301.09876v1",
        open_access=True
    )
    db.add(test_db_paper)
    db.commit()
    db.refresh(test_db_paper)
    persisted = db.query(ResearchPaper).filter(ResearchPaper.id == test_db_paper.id).first()
    assert persisted is not None
    assert persisted.title == "Deep Autonomous Drone Routing in Urban Corridors"
    assert persisted.authors == ["Dr. Alice Chen", "Bob Smith"]
    print(f"  [OK] Successfully persisted paper with ID: {persisted.id}")

    # TEST 8: Project Ownership Enforcement
    print("\n[TEST 8] Project Ownership Enforcement:")
    # User A retrieving their project's research
    res_list_a = get_stored_research(project_id=project_a.id, current_user=user_a, db=db)
    print(f"  [OK] User A retrieved {res_list_a.total} stored papers for their project")
    assert res_list_a.total >= 1

    # TEST 9: Cross-User Access Rejection
    print("\n[TEST 9] Cross-User Access Rejection (User B attempting access to User A's project):")
    try:
        get_stored_research(project_id=project_a.id, current_user=user_b, db=db)
        assert False, "Should have raised 403 Forbidden"
    except HTTPException as e:
        print(f"  [OK] Correctly blocked cross-user access: Status {e.status_code} - {e.detail}")
        assert e.status_code == 403

    try:
        get_research_stats(project_id=project_a.id, current_user=user_b, db=db)
        assert False, "Should have raised 403 Forbidden for stats"
    except HTTPException as e:
        print(f"  [OK] Correctly blocked cross-user stats: Status {e.status_code}")
        assert e.status_code == 403

    try:
        get_stored_research(project_id="non-existent-proj-id", current_user=user_a, db=db)
        assert False, "Should have raised 404 Not Found"
    except HTTPException as e:
        print(f"  [OK] Non-existent project rejected with 404: {e.detail}")
        assert e.status_code == 404

    # TEST 10: Provider Timeout Handling
    print("\n[TEST 10] Provider Timeout Handling:")
    mock_timeout_client = AsyncMock()
    mock_timeout_client.get.side_effect = httpx.TimeoutException("Connection timed out")
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_timeout_client
    mock_cm.__aexit__.return_value = None
    with patch("app.services.research.arxiv_service.httpx.AsyncClient", return_value=mock_cm):
        timeout_arxiv = ArxivService(timeout=1.0)
        try:
            asyncio.run(timeout_arxiv.search("test query"))
            assert False, "Should raise ProviderTimeoutError"
        except ProviderTimeoutError as err:
            print(f"  [OK] Caught expected ProviderTimeoutError: {err}")
            assert err.provider == "arxiv"

    # TEST 11: HTTP 429 Rate Limit Handling
    print("\n[TEST 11] HTTP 429 Rate Limit Handling:")
    mock_429_resp = MagicMock()
    mock_429_resp.status_code = 429
    mock_429_resp.text = "Too Many Requests"
    mock_429_client = AsyncMock()
    mock_429_client.get.return_value = mock_429_resp
    mock_cm2 = AsyncMock()
    mock_cm2.__aenter__.return_value = mock_429_client
    mock_cm2.__aexit__.return_value = None
    with patch("app.services.research.semantic_scholar_service.httpx.AsyncClient", return_value=mock_cm2):
        rate_s2 = SemanticScholarService(timeout=1.0)
        try:
            asyncio.run(rate_s2.search("test query"))
            assert False, "Should raise ProviderRateLimitError"
        except ProviderRateLimitError as err:
            print(f"  [OK] Caught expected ProviderRateLimitError: {err}")
            assert err.status_code == 429

    # TEST 12: Partial Provider Failure Handling
    print("\n[TEST 12] Partial Provider Failure Handling:")
    # Arxiv fails with timeout, OpenAlex succeeds with 1 paper, Semantic Scholar succeeds with 1 paper
    mock_arxiv_fail = AsyncMock(spec=ArxivService)
    mock_arxiv_fail.provider_name = "arxiv"
    mock_arxiv_fail.search.side_effect = ProviderTimeoutError("arXiv timeout", "arxiv")

    mock_s2_ok = AsyncMock(spec=SemanticScholarService)
    mock_s2_ok.provider_name = "semantic_scholar"
    mock_s2_ok.search.return_value = [p2]

    mock_oa_ok = AsyncMock(spec=OpenAlexService)
    mock_oa_ok.provider_name = "openalex"
    mock_oa_ok.search.return_value = [p3]

    partial_discovery = ResearchDiscoveryService(
        arxiv_service=mock_arxiv_fail,
        semantic_scholar_service=mock_s2_ok,
        openalex_service=mock_oa_ok,
    )

    partial_resp = asyncio.run(
        partial_discovery.search_and_persist(
            db=db,
            project=project_a,
            user_id=user_a.id,
            max_results=5
        )
    )
    print(f"  [OK] Partial Failure Discovery Status: {partial_resp.status}")
    print(f"  [OK] Provider Errors Logged: {partial_resp.provider_errors}")
    print(f"  [OK] Successful Papers Stored: {partial_resp.new_stored}")
    assert partial_resp.status == "partial_success"
    assert "arxiv" in partial_resp.provider_errors
    assert partial_resp.provider_counts["semantic_scholar"] >= 1
    assert partial_resp.provider_counts["openalex"] >= 1

    # TEST 13: All-Provider Failure Handling
    print("\n[TEST 13] All-Provider Failure Handling:")
    mock_oa_fail = AsyncMock(spec=OpenAlexService)
    mock_oa_fail.provider_name = "openalex"
    mock_oa_fail.search.side_effect = ProviderAPIError("OpenAlex 500 error", "openalex", 500)

    mock_s2_fail = AsyncMock(spec=SemanticScholarService)
    mock_s2_fail.provider_name = "semantic_scholar"
    mock_s2_fail.search.side_effect = ProviderRateLimitError("S2 429", "semantic_scholar", 429)

    all_fail_discovery = ResearchDiscoveryService(
        arxiv_service=mock_arxiv_fail,
        semantic_scholar_service=mock_s2_fail,
        openalex_service=mock_oa_fail,
    )

    all_fail_resp = asyncio.run(
        all_fail_discovery.search_and_persist(
            db=db,
            project=project_a,
            user_id=user_a.id,
            max_results=5
        )
    )
    print(f"  [OK] All-Fail Discovery Status: {all_fail_resp.status}")
    print(f"  [OK] Provider Errors: {list(all_fail_resp.provider_errors.keys())}")
    assert all_fail_resp.status == "failed"
    assert len(all_fail_resp.provider_errors) == 3
    assert all_fail_resp.new_stored == 0

    # TEST 14: Research Retrieval Endpoint with Filters
    print("\n[TEST 14] Research Retrieval Endpoint (GET /api/projects/{id}/research):")
    # Query with provider filter = 'openalex'
    filtered_oa = get_stored_research(
        project_id=project_a.id,
        provider="openalex",
        current_user=user_a,
        db=db
    )
    print(f"  [OK] Retrieved {len(filtered_oa.items)} OpenAlex papers via provider filter")
    for item in filtered_oa.items:
        assert item.provider == "openalex"

    # Query with search keyword filter = 'Geofencing'
    filtered_search = get_stored_research(
        project_id=project_a.id,
        search="Geofencing",
        current_user=user_a,
        db=db
    )
    print(f"  [OK] Retrieved {filtered_search.total} papers matching keyword 'Geofencing'")
    assert filtered_search.total >= 1

    # TEST 15: Research Statistics Endpoint
    print("\n[TEST 15] Research Statistics Endpoint (GET /api/projects/{id}/research/stats):")
    stats = get_research_stats(project_id=project_a.id, current_user=user_a, db=db)
    print(f"  [OK] Total Stored Papers: {stats.total_papers}")
    print(f"  [OK] By Provider: {stats.by_provider}")
    print(f"  [OK] Open Access Count: {stats.open_access_count}")
    print(f"  [OK] Year Distribution: {stats.year_distribution}")
    assert stats.total_papers >= 2
    assert stats.open_access_count >= 1
    assert "2024" in stats.year_distribution or "2023" in stats.year_distribution or "2022" in stats.year_distribution

    db.close()
    print("\n================================================================")
    print(">>> ALL 15 PHASE 4.1 RESEARCH DISCOVERY TESTS PASSED 100%! <<<")
    print("================================================================")

if __name__ == "__main__":
    run_tests()
