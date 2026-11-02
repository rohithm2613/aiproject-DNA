"""
Live HTTP End-to-End Test: Phase 4.4 Semantic Embedding & Cross-Source Similarity Engine
Tests the complete HTTP workflow:
1. Live FastAPI server bootstrap
2. User registration and project creation
3. Analysis, research paper, and GitHub repo seeding
4. POST /api/projects/{id}/embeddings/generate (Generation & Idempotency)
5. GET /api/projects/{id}/similarity (Cross-source ranking & filtering)
6. GET /api/projects/{id}/similarity/stats (Vector statistics & metadata)
7. Multi-tenant security (403 Forbidden cross-user rejection)
"""
import sys
import uuid
import threading
import time
import urllib.request
import urllib.error
import json
import http.cookiejar
from unittest.mock import patch

sys.path.insert(0, 'backend')
import uvicorn
from app.main import app
from app.database.session import SessionLocal
from app.models.research_paper import ResearchPaper
from app.models.github_repo import GitHubRepository
from app.services.ai_service import AIService
from test_phase3_ai import get_sample_analysis_schema

def run_e2e():
    port = 8877
    config = uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning')
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)

    cj1 = http.cookiejar.CookieJar()
    opener1 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj1))

    # 1. Register User 1
    user1_email = f'phase4_4_e2e_{int(time.time())}@projectdna.io'
    reg_data = json.dumps({
        'full_name': 'Vector Similarity Lead',
        'email': user1_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req1 = urllib.request.Request(f'http://127.0.0.1:{port}/api/auth/register', data=reg_data, headers={'Content-Type': 'application/json'})
    opener1.open(req1)
    print(f'[E2E 1] Registered User 1: {user1_email}')

    # 2. Create Project
    p_data = json.dumps({
        'title': 'Autonomous UAV Fleet Deconfliction & Air Routing',
        'description': 'Decentralized real-time collision avoidance and 3D airspace path planning for urban drone logistics.',
        'domain': 'Robotics & Autonomous Systems',
        'technologies': ['ROS 2', 'Python', 'FastAPI', 'PyTorch']
    }).encode('utf-8')
    req2 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects', data=p_data, headers={'Content-Type': 'application/json'})
    p_res = json.loads(opener1.open(req2).read().decode('utf-8'))
    proj_id = p_res['id']
    user1_id = p_res['user_id']
    print(f'[E2E 2] Created Project: {p_res["title"]} (ID: {proj_id})')

    # 3. Trigger Phase 3 AI Analysis
    with patch.object(AIService, 'analyze_project_idea', return_value=get_sample_analysis_schema()):
        req3 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/analyze', data=b'{}', headers={'Content-Type': 'application/json'})
        a_res = json.loads(opener1.open(req3).read().decode('utf-8'))
        print(f'[E2E 3] Analyzed Project: Version {a_res["version"]} | Keywords: {len(a_res["keywords"])}')

    # 4. Seed Research Paper and GitHub Repo directly in database
    db = SessionLocal()
    try:
        paper = ResearchPaper(
            id=str(uuid.uuid4()),
            project_id=proj_id,
            user_id=user1_id,
            provider="arxiv",
            provider_paper_id="2403.01234",
            title="Distributed Trajectory Optimization for Multi-UAV Air Mobility Systems",
            abstract="A comprehensive study on decentralized collision avoidance using proximal policy optimization in crowded airspace.",
            authors=["Dr. Alan Turing", "Dr. Ada Lovelace"],
            publication_year=2024,
            venue="IEEE Transactions on Robotics",
            doi="10.1109/TRO.2024.123456",
            primary_category="cs.RO",
            open_access=True,
        )
        db.add(paper)

        repo = GitHubRepository(
            id=str(uuid.uuid4()),
            project_id=proj_id,
            user_id=user1_id,
            github_repository_id=990101,
            full_name="aerial-mesh/uav-deconfliction-core",
            name="uav-deconfliction-core",
            owner_login="aerial-mesh",
            html_url="https://github.com/aerial-mesh/uav-deconfliction-core",
            description="High-performance C++ and Python framework for distributed UAV fleet routing and collision deconfliction.",
            language="Python",
            topics=["uav", "robotics", "collision-avoidance", "deconfliction"],
            stargazers_count=1850,
        )
        db.add(repo)
        db.commit()
        print(f'[E2E 4] Seeded 1 Research Paper and 1 GitHub Repository into database')
    finally:
        db.close()

    # 5. Generate Vector Embeddings via POST /api/projects/{id}/embeddings/generate
    gen_payload = json.dumps({'force_regenerate': False}).encode('utf-8')
    req5 = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/embeddings/generate',
        data=gen_payload,
        headers={'Content-Type': 'application/json'}
    )
    gen_res = json.loads(opener1.open(req5).read().decode('utf-8'))
    print(f'[E2E 5] Generated Embeddings: status={gen_res["status"]} | generated={gen_res["total_generated"]} | skipped={gen_res["total_skipped"]}')
    assert gen_res['status'] == 'completed'
    assert gen_res['total_generated'] == 3  # Project + Paper + Repo
    assert gen_res['total_skipped'] == 0
    assert gen_res['embedding_dimension'] == 384
    assert gen_res['counts_by_source']['project'] == 1
    assert gen_res['counts_by_source']['research_paper'] == 1
    assert gen_res['counts_by_source']['github_repository'] == 1

    # 6. Verify Duplicate Prevention (Idempotent Regeneration)
    req6 = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/embeddings/generate',
        data=gen_payload,
        headers={'Content-Type': 'application/json'}
    )
    gen_res2 = json.loads(opener1.open(req6).read().decode('utf-8'))
    print(f'[E2E 6] Duplicate Prevention Test: generated={gen_res2["total_generated"]} | skipped={gen_res2["total_skipped"]}')
    assert gen_res2['total_generated'] == 0
    assert gen_res2['total_skipped'] == 3

    # 7. Force Regeneration Test
    force_payload = json.dumps({'force_regenerate': True}).encode('utf-8')
    req7 = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/embeddings/generate',
        data=force_payload,
        headers={'Content-Type': 'application/json'}
    )
    gen_res3 = json.loads(opener1.open(req7).read().decode('utf-8'))
    print(f'[E2E 7] Force Regeneration Test: generated={gen_res3["total_generated"]} | skipped={gen_res3["total_skipped"]}')
    assert gen_res3['total_generated'] == 3
    assert gen_res3['total_skipped'] == 0

    # 8. Query Cross-Source Similarities via GET /api/projects/{id}/similarity
    req8 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/similarity')
    sim_res = json.loads(opener1.open(req8).read().decode('utf-8'))
    print(f'[E2E 8] Cross-Source Similarities: total_matches={sim_res["total_matches"]}')
    assert sim_res['project_id'] == proj_id
    assert sim_res['embedding_dimension'] == 384
    assert sim_res['total_matches'] == 2
    assert len(sim_res['matches']) == 2
    assert sim_res['disclaimer'] is not None

    first_match = sim_res['matches'][0]
    second_match = sim_res['matches'][1]
    assert first_match['rank'] == 1
    assert second_match['rank'] == 2
    assert first_match['similarity_score'] >= second_match['similarity_score']
    assert first_match['similarity_score'] > 0.0
    assert first_match['similarity_percentage'] > 0.0
    assert first_match['similarity_label'] in ['High semantic similarity', 'Moderate semantic similarity', 'Low semantic similarity']
    print(f'       Match #1: [{first_match["source_type"]}] {first_match["title"]} ({first_match["similarity_percentage"]}%) -> {first_match["similarity_label"]}')
    print(f'       Match #2: [{second_match["source_type"]}] {second_match["title"]} ({second_match["similarity_percentage"]}%) -> {second_match["similarity_label"]}')

    # 9. Query Filter: source_type=research_paper
    req9 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/similarity?source_type=research_paper')
    paper_sim = json.loads(opener1.open(req9).read().decode('utf-8'))
    print(f'[E2E 9] Filter source_type=research_paper: {paper_sim["total_matches"]} match(es)')
    assert paper_sim['total_matches'] == 1
    assert paper_sim['matches'][0]['source_type'] == 'research_paper'

    # 10. Query Filter: source_type=github_repository
    req10 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/similarity?source_type=github_repository')
    repo_sim = json.loads(opener1.open(req10).read().decode('utf-8'))
    print(f'[E2E 10] Filter source_type=github_repository: {repo_sim["total_matches"]} match(es)')
    assert repo_sim['total_matches'] == 1
    assert repo_sim['matches'][0]['source_type'] == 'github_repository'

    # 11. Query Statistics via GET /api/projects/{id}/similarity/stats
    req11 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/similarity/stats')
    stats_res = json.loads(opener1.open(req11).read().decode('utf-8'))
    print(f'[E2E 11] Stats: total_embeddings={stats_res["total_embeddings_stored"]} | has_project={stats_res["has_project_embedding"]} | model={stats_res["model_name"]}')
    assert stats_res['total_embeddings_stored'] == 3
    assert stats_res['has_project_embedding'] is True
    assert stats_res['total_matches_available'] == 2
    assert stats_res['model_name'] == 'sentence-transformers/all-MiniLM-L6-v2'
    assert stats_res['embedding_dimension'] == 384

    # 12. Register User 2 and Test Multi-Tenant Isolation (403 Forbidden)
    cj2 = http.cookiejar.CookieJar()
    opener2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj2))
    user2_email = f'phase4_4_intruder_{int(time.time())}@projectdna.io'
    reg_data2 = json.dumps({
        'full_name': 'Unauthorized Competitor',
        'email': user2_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req12 = urllib.request.Request(f'http://127.0.0.1:{port}/api/auth/register', data=reg_data2, headers={'Content-Type': 'application/json'})
    opener2.open(req12)

    # 12A. User 2 tries POST /embeddings/generate -> 403
    try:
        req_forbidden_gen = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/embeddings/generate',
            data=b'{}',
            headers={'Content-Type': 'application/json'}
        )
        opener2.open(req_forbidden_gen)
        assert False, "User 2 should have been rejected with 403 on POST /embeddings/generate"
    except urllib.error.HTTPError as err:
        print(f'[E2E 12A] Cross-User POST /embeddings/generate Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    # 12B. User 2 tries GET /similarity -> 403
    try:
        req_forbidden_sim = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/similarity')
        opener2.open(req_forbidden_sim)
        assert False, "User 2 should have been rejected with 403 on GET /similarity"
    except urllib.error.HTTPError as err:
        print(f'[E2E 12B] Cross-User GET /similarity Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    # 12C. User 2 tries GET /similarity/stats -> 403
    try:
        req_forbidden_stats = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/similarity/stats')
        opener2.open(req_forbidden_stats)
        assert False, "User 2 should have been rejected with 403 on GET /similarity/stats"
    except urllib.error.HTTPError as err:
        print(f'[E2E 12C] Cross-User GET /similarity/stats Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    server.should_exit = True
    print('\n================================================================')
    print('>>> ALL PHASE 4.4 END-TO-END HTTP WORKFLOW TESTS PASSED 100%! <<<')
    print('================================================================')

if __name__ == '__main__':
    run_e2e()
