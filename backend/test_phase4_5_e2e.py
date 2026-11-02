"""
Live HTTP End-to-End Test: Phase 4.5 RAG-Based Evidence & Research Gap Validation Engine
Tests the complete HTTP workflow:
1. Live FastAPI server bootstrap on port 8888
2. User registration and project creation
3. Analysis, research paper, GitHub repo, and innovation gap seeding
4. Embedding generation (Phase 4.4 integration)
5. POST /api/projects/{id}/validation/generate (v1 report generation & manifest verification)
6. GET /api/projects/{id}/validation (Latest report retrieval)
7. POST /api/projects/{id}/validation/generate (Caching when force_regenerate=False)
8. POST /api/projects/{id}/validation/generate (Version incrementing when force_regenerate=True)
9. GET /api/projects/{id}/validation/history (History list v2, v1)
10. GET /api/projects/{id}/validation/{report_id} (Specific report retrieval)
11. GET /api/projects/{id}/validation/evidence (Evidence manifest explorer)
12. Multi-tenant security isolation (403 Forbidden cross-user rejection)
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
from app.models.repository_analysis import RepositoryAnalysis
from app.models.innovation_gap import InnovationGap
from app.services.ai_service import AIService
from test_phase3_ai import get_sample_analysis_schema


def run_e2e():
    port = 8888
    config = uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning')
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)

    cj1 = http.cookiejar.CookieJar()
    opener1 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj1))

    # 1. Register User 1
    user1_email = f'phase4_5_e2e_{int(time.time())}@projectdna.io'
    reg_data = json.dumps({
        'full_name': 'RAG Validation Lead',
        'email': user1_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req1 = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/auth/register',
        data=reg_data,
        headers={'Content-Type': 'application/json'}
    )
    opener1.open(req1)
    print(f'[E2E 1] Registered User 1: {user1_email}')

    # 2. Create Project
    p_data = json.dumps({
        'title': 'Autonomous Multi-Agent Drone Fleet Coordination',
        'description': 'Decentralized real-time collision avoidance and 3D airspace path planning for urban drone logistics.',
        'domain': 'Robotics & Autonomous Systems',
        'technologies': ['ROS 2', 'Python', 'FastAPI', 'PyTorch']
    }).encode('utf-8')
    req2 = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects',
        data=p_data,
        headers={'Content-Type': 'application/json'}
    )
    p_res = json.loads(opener1.open(req2).read().decode('utf-8'))
    proj_id = p_res['id']
    user1_id = p_res['user_id']
    print(f'[E2E 2] Created Project: {p_res["title"]} (ID: {proj_id})')

    # 3. Trigger Phase 3 AI Analysis
    with patch.object(AIService, 'analyze_project_idea', return_value=get_sample_analysis_schema()):
        req3 = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/analyze',
            data=b'{}',
            headers={'Content-Type': 'application/json'}
        )
        a_res = json.loads(opener1.open(req3).read().decode('utf-8'))
        print(f'[E2E 3] Analyzed Project: Version {a_res["version"]} | Keywords: {len(a_res["keywords"])}')

    # 4. Seed Multi-Source Artifacts into Database
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

        repo_analysis = RepositoryAnalysis(
            id=str(uuid.uuid4()),
            project_id=proj_id,
            github_repo_id=repo.id,
            user_id=user1_id,
            repo_full_name=repo.full_name,
            summary="Decentralized trajectory solver for simulated fixed-wing drones.",
            features=[
                {"feature_name": "Kinematic Feasibility Checker", "description": "Validates yaw and climb angle limits"},
                {"feature_name": "A* Path Planning", "description": "Static grid-based collision-free pathfinder"}
            ],
            detected_technologies={"frameworks": ["PyTorch", "ROS 2"]},
            readme_present=True,
            analysis_status="completed",
        )
        db.add(repo_analysis)

        gap = InnovationGap(
            id=str(uuid.uuid4()),
            project_id=proj_id,
            user_id=user1_id,
            gap_title="Dynamic Micro-Weather Wind Shear Adaptation",
            category="capability",
            description="Existing solvers assume static zero-wind conditions; real-time wind shear adaptation is missing.",
            why_it_matters="Critical for low-altitude urban delivery drones facing micro-gusts between skyscrapers.",
            suggested_implementation="Incorporate Kalman-filter based wind vector estimation with model-predictive contouring.",
            priority="high",
            confidence_level="high",
            supporting_evidence={"analyzed_repositories": [repo.full_name]},
        )
        db.add(gap)
        db.commit()
        print(f'[E2E 4] Seeded: 1 Paper, 1 Repo, 1 Repo Analysis, 1 Innovation Gap')
    finally:
        db.close()

    # 5. Generate Vector Embeddings (Phase 4.4 pipeline)
    gen_emb_req = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/embeddings/generate',
        data=json.dumps({'force_regenerate': False}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    emb_res = json.loads(opener1.open(gen_emb_req).read().decode('utf-8'))
    print(f'[E2E 5] Generated Embeddings: total_generated={emb_res["total_generated"]} | status={emb_res["status"]}')

    # 6. Generate Validation Report v1 via POST /api/projects/{id}/validation/generate
    val_req1 = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/generate',
        data=json.dumps({'force_regenerate': True}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    v1_res = json.loads(opener1.open(val_req1).read().decode('utf-8'))
    print(f'[E2E 6] Generated Validation Report: v{v1_res["version"]} | status={v1_res["report_status"]} | model={v1_res["model_name"]}')
    assert v1_res['version'] == 1
    assert v1_res['report_status'] == 'completed'
    assert v1_res['project_id'] == proj_id

    # Verify 10 report sections
    rep = v1_res['report']
    assert rep['project_overview']['project_title'] == 'Autonomous Multi-Agent Drone Fleet Coordination'
    assert len(rep['academic_research']['relevant_papers']) >= 1
    assert len(rep['software_implementations']['relevant_repositories']) >= 1
    assert len(rep['validated_research_gaps']['validated_gaps']) >= 1
    assert len(rep['innovation_opportunities']['differentiating_capabilities']) >= 1
    assert rep['risks_and_limitations']['false_positive_negative_risks'] is not None
    assert 'does not certify global originality' in rep['final_assessment']['explicit_novelty_limitation'].lower()

    # Verify Evidence Manifest
    manifest = v1_res['evidence_manifest']
    assert len(manifest) >= 3
    evid_ids = [e['evidence_id'] for e in manifest]
    print(f'       Evidence IDs in Manifest: {evid_ids}')
    assert any('EVID-PAP' in eid for eid in evid_ids)
    assert any('EVID-REP' in eid for eid in evid_ids)
    assert any('EVID-GAP' in eid for eid in evid_ids)

    # 7. GET /api/projects/{id}/validation (Fetch Latest)
    get_req = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation')
    latest_res = json.loads(opener1.open(get_req).read().decode('utf-8'))
    print(f'[E2E 7] GET Latest Report: v{latest_res["version"]} | id={latest_res["id"]}')
    assert latest_res['id'] == v1_res['id']
    assert latest_res['version'] == 1

    # 8. Caching Test: POST with force_regenerate=False -> returns same report
    cached_req = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/generate',
        data=json.dumps({'force_regenerate': False}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    cached_res = json.loads(opener1.open(cached_req).read().decode('utf-8'))
    print(f'[E2E 8] Cache Test (force=False): returned existing v{cached_res["version"]} (same id: {cached_res["id"] == v1_res["id"]})')
    assert cached_res['id'] == v1_res['id']
    assert cached_res['version'] == 1

    # 9. Force Regeneration Test: POST with force_regenerate=True -> creates v2
    v2_req = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/generate',
        data=json.dumps({'force_regenerate': True}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    v2_res = json.loads(opener1.open(v2_req).read().decode('utf-8'))
    print(f'[E2E 9] Force Regeneration (force=True): created v{v2_res["version"]} | id={v2_res["id"]}')
    assert v2_res['version'] == 2
    assert v2_res['id'] != v1_res['id']

    # 10. GET /api/projects/{id}/validation/history
    hist_req = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/history')
    hist_res = json.loads(opener1.open(hist_req).read().decode('utf-8'))
    print(f'[E2E 10] Validation History: total_reports={hist_res["total_reports"]}')
    assert hist_res['total_reports'] == 2
    assert hist_res['reports'][0]['version'] == 2
    assert hist_res['reports'][1]['version'] == 1

    # 11. GET /api/projects/{id}/validation/{report_id}
    v1_id = v1_res['id']
    get_v1_req = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/{v1_id}')
    spec_res = json.loads(opener1.open(get_v1_req).read().decode('utf-8'))
    print(f'[E2E 11] Specific Report Query by ID: requested v1 -> got v{spec_res["version"]}')
    assert spec_res['id'] == v1_id
    assert spec_res['version'] == 1

    # 12. GET /api/projects/{id}/validation/evidence (Evidence Manifest Explorer)
    ev_req = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/evidence')
    ev_res = json.loads(opener1.open(ev_req).read().decode('utf-8'))
    print(f'[E2E 12] Evidence Manifest: total_items={ev_res["total_evidence_items"]} | sources={ev_res["counts_by_source"]}')
    assert ev_res['total_evidence_items'] >= 3
    assert 'research_paper' in ev_res['counts_by_source']
    assert 'github_repository' in ev_res['counts_by_source']
    assert 'innovation_gap' in ev_res['counts_by_source']

    # 13. Register User 2 and Test Multi-Tenant Security Isolation (403 Forbidden)
    cj2 = http.cookiejar.CookieJar()
    opener2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj2))
    user2_email = f'phase4_5_intruder_{int(time.time())}@projectdna.io'
    reg_data2 = json.dumps({
        'full_name': 'Unauthorized Competitor',
        'email': user2_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req13 = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/auth/register',
        data=reg_data2,
        headers={'Content-Type': 'application/json'}
    )
    opener2.open(req13)

    # 13A. User 2 tries POST /validation/generate -> 403
    try:
        req_forbid_gen = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/generate',
            data=b'{}',
            headers={'Content-Type': 'application/json'}
        )
        opener2.open(req_forbid_gen)
        assert False, "User 2 should have been rejected with 403 on POST /validation/generate"
    except urllib.error.HTTPError as err:
        print(f'[E2E 13A] Cross-User POST /validation/generate Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    # 13B. User 2 tries GET /validation -> 403
    try:
        req_forbid_get = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation')
        opener2.open(req_forbid_get)
        assert False, "User 2 should have been rejected with 403 on GET /validation"
    except urllib.error.HTTPError as err:
        print(f'[E2E 13B] Cross-User GET /validation Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    # 13C. User 2 tries GET /validation/history -> 403
    try:
        req_forbid_hist = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/history')
        opener2.open(req_forbid_hist)
        assert False, "User 2 should have been rejected with 403 on GET /validation/history"
    except urllib.error.HTTPError as err:
        print(f'[E2E 13C] Cross-User GET /validation/history Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    # 13D. User 2 tries GET /validation/evidence -> 403
    try:
        req_forbid_ev = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/evidence')
        opener2.open(req_forbid_ev)
        assert False, "User 2 should have been rejected with 403 on GET /validation/evidence"
    except urllib.error.HTTPError as err:
        print(f'[E2E 13D] Cross-User GET /validation/evidence Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    server.should_exit = True
    print('\n================================================================')
    print('>>> ALL PHASE 4.5 END-TO-END HTTP WORKFLOW TESTS PASSED 100%! <<<')
    print('================================================================')


if __name__ == '__main__':
    run_e2e()
