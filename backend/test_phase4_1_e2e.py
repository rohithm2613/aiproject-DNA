import sys
import threading
import time
import urllib.request
import urllib.error
import json
import http.cookiejar
from unittest.mock import patch, AsyncMock

sys.path.insert(0, 'backend')
import uvicorn
from app.main import app
from app.services.ai_service import AIService
from app.services.research.arxiv_service import ArxivService
from app.services.research.semantic_scholar_service import SemanticScholarService
from app.services.research.openalex_service import OpenAlexService
from app.schemas.research import ResearchPaperSchema
from test_phase3_ai import get_sample_analysis_schema

def get_sample_papers():
    p_arxiv = ResearchPaperSchema(
        provider="arxiv",
        provider_paper_id="2301.11111",
        title="Autonomous Airspace Routing with Reinforcement Learning",
        abstract="Deep reinforcement learning for 3D trajectory deconfliction.",
        authors=["Dr. Alan Turing", "Grace Hopper"],
        publication_year=2023,
        venue="arXiv (cs.RO)",
        doi="10.1145/e2e.arxiv.1",
        arxiv_id="2301.11111",
        open_access=True
    )
    p_s2 = ResearchPaperSchema(
        provider="semantic_scholar",
        provider_paper_id="s2_22222",
        title="Decentralized Multi-Agent Collision Avoidance for Delivery Drones",
        abstract="Novel geometric algorithms for drone swarm coordination.",
        authors=["Ada Lovelace"],
        publication_year=2023,
        venue="IEEE Robotics and Automation Letters",
        doi="10.1109/e2e.s2.2",
        citation_count=35,
        open_access=True
    )
    p_oa = ResearchPaperSchema(
        provider="openalex",
        provider_paper_id="W33333",
        title="Urban Air Mobility Infrastructure and Safety Geofencing",
        abstract="Regulatory and architectural frameworks for lower-altitude airspace.",
        authors=["Claude Shannon"],
        publication_year=2024,
        venue="Journal of Air Transportation",
        doi="10.2514/e2e.oa.3",
        citation_count=12,
        open_access=False
    )
    return [p_arxiv], [p_s2], [p_oa]

def run_e2e():
    config = uvicorn.Config(app, host='127.0.0.1', port=8877, log_level='warning')
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)

    cj1 = http.cookiejar.CookieJar()
    opener1 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj1))

    # 1. Register User 1
    user1_email = f'researcher_e2e_{int(time.time())}@projectdna.io'
    reg_data = json.dumps({
        'full_name': 'E2E Research Scientist',
        'email': user1_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req1 = urllib.request.Request('http://127.0.0.1:8877/api/auth/register', data=reg_data, headers={'Content-Type': 'application/json'})
    opener1.open(req1)
    print(f'[E2E 1] Registered User 1: {user1_email}')

    # 2. Create Project
    p_data = json.dumps({
        'title': 'Autonomous UAV Lower-Altitude Air Delivery Network',
        'description': 'Real-time multi-agent routing network for urban aerial logistics.',
        'domain': 'Robotics & Autonomous Systems',
        'technologies': ['ROS 2', 'PyTorch', 'PX4']
    }).encode('utf-8')
    req2 = urllib.request.Request('http://127.0.0.1:8877/api/projects', data=p_data, headers={'Content-Type': 'application/json'})
    p_res = json.loads(opener1.open(req2).read().decode('utf-8'))
    proj_id = p_res['id']
    print(f'[E2E 2] Created Project: {p_res["title"]} (ID: {proj_id})')

    # 3. Trigger Phase 3 AI Analysis
    with patch.object(AIService, 'analyze_project_idea', return_value=get_sample_analysis_schema()):
        req3 = urllib.request.Request(f'http://127.0.0.1:8877/api/projects/{proj_id}/analyze', data=b'{}', headers={'Content-Type': 'application/json'})
        a_res = json.loads(opener1.open(req3).read().decode('utf-8'))
        print(f'[E2E 3] Analyzed Project: Version {a_res["version"]} | Keywords: {len(a_res["keywords"])}')

    # 4. Trigger Research Paper Discovery via POST /api/projects/{id}/research/search
    papers_arxiv, papers_s2, papers_oa = get_sample_papers()
    with patch.object(ArxivService, 'search', new_callable=AsyncMock) as mock_arxiv_search, \
         patch.object(SemanticScholarService, 'search', new_callable=AsyncMock) as mock_s2_search, \
         patch.object(OpenAlexService, 'search', new_callable=AsyncMock) as mock_oa_search:

        mock_arxiv_search.return_value = papers_arxiv
        mock_s2_search.return_value = papers_s2
        mock_oa_search.return_value = papers_oa

        search_payload = json.dumps({'max_results': 10}).encode('utf-8')
        req4 = urllib.request.Request(
            f'http://127.0.0.1:8877/api/projects/{proj_id}/research/search',
            data=search_payload,
            headers={'Content-Type': 'application/json'}
        )
        search_res = json.loads(opener1.open(req4).read().decode('utf-8'))
        print(f'[E2E 4] Research Discovery Status: {search_res["status"]} | Stored: {search_res["new_stored"]} papers | Total: {search_res["total_stored_papers"]}')
        assert search_res['status'] == 'completed'
        assert search_res['new_stored'] == 3
        assert search_res['total_stored_papers'] == 3
        assert 'arxiv' in search_res['provider_counts']
        assert 'semantic_scholar' in search_res['provider_counts']
        assert 'openalex' in search_res['provider_counts']

        # 5. Re-run search to verify deduplication
        req5 = urllib.request.Request(
            f'http://127.0.0.1:8877/api/projects/{proj_id}/research/search',
            data=search_payload,
            headers={'Content-Type': 'application/json'}
        )
        search_res2 = json.loads(opener1.open(req5).read().decode('utf-8'))
        print(f'[E2E 5] Re-run Deduplication: New Stored = {search_res2["new_stored"]}, Duplicates Skipped = {search_res2["duplicates_skipped"]}')
        assert search_res2['new_stored'] == 0
        assert search_res2['duplicates_skipped'] == 3

    # 6. Retrieve Stored Papers via GET /api/projects/{id}/research
    req6 = urllib.request.Request(f'http://127.0.0.1:8877/api/projects/{proj_id}/research?page=1&page_size=10')
    papers_res = json.loads(opener1.open(req6).read().decode('utf-8'))
    print(f'[E2E 6] Retrieved {papers_res["total"]} papers via GET /api/projects/{proj_id}/research')
    assert papers_res['total'] == 3
    assert len(papers_res['items']) == 3

    # 7. Test Retrieval Filters (provider='arxiv')
    req7 = urllib.request.Request(f'http://127.0.0.1:8877/api/projects/{proj_id}/research?provider=arxiv')
    arxiv_filter_res = json.loads(opener1.open(req7).read().decode('utf-8'))
    print(f'[E2E 7] Filter provider=arxiv: {arxiv_filter_res["total"]} paper(s) found')
    assert arxiv_filter_res['total'] == 1
    assert arxiv_filter_res['items'][0]['provider'] == 'arxiv'

    # 8. Query Research Stats via GET /api/projects/{id}/research/stats
    req8 = urllib.request.Request(f'http://127.0.0.1:8877/api/projects/{proj_id}/research/stats')
    stats_res = json.loads(opener1.open(req8).read().decode('utf-8'))
    print(f'[E2E 8] Research Stats: Total = {stats_res["total_papers"]} | Open Access = {stats_res["open_access_count"]} | Providers = {stats_res["by_provider"]}')
    assert stats_res['total_papers'] == 3
    assert stats_res['open_access_count'] == 2  # 1 from arXiv, 1 from S2
    assert stats_res['by_provider'].get('arxiv') == 1
    assert stats_res['by_provider'].get('semantic_scholar') == 1
    assert stats_res['by_provider'].get('openalex') == 1

    # 9. Register User 2 and Test Cross-User Isolation
    cj2 = http.cookiejar.CookieJar()
    opener2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj2))
    user2_email = f'intruder_e2e_{int(time.time())}@projectdna.io'
    reg_data2 = json.dumps({
        'full_name': 'E2E Intruder User',
        'email': user2_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req9 = urllib.request.Request('http://127.0.0.1:8877/api/auth/register', data=reg_data2, headers={'Content-Type': 'application/json'})
    opener2.open(req9)

    # User 2 tries to access User 1's research
    try:
        req_forbidden = urllib.request.Request(f'http://127.0.0.1:8877/api/projects/{proj_id}/research')
        opener2.open(req_forbidden)
        assert False, "User 2 should have been rejected with 403"
    except urllib.error.HTTPError as err:
        print(f'[E2E 9] Cross-User Access Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    server.should_exit = True
    print('\n================================================================')
    print('>>> ALL PHASE 4.1 END-TO-END HTTP WORKFLOW TESTS PASSED 100%! <<<')
    print('================================================================')

if __name__ == '__main__':
    run_e2e()

