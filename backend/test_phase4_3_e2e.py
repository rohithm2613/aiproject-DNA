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
from app.services.github.github_service import GitHubService
from app.services.github.repository_analyzer import RepositoryAnalyzer
from app.schemas.github import GitHubRepositorySchema, GitHubRateLimitInfo
from test_phase3_ai import get_sample_analysis_schema

def get_sample_github_repos():
    repo1 = GitHubRepositorySchema(
        github_repository_id=8801,
        full_name="autonomous-systems/drone-nav",
        name="drone-nav",
        owner_login="autonomous-systems",
        owner_avatar_url="https://avatars.githubusercontent.com/u/8801",
        html_url="https://github.com/autonomous-systems/drone-nav",
        description="Autonomous drone navigation system using ROS 2, FastDDS, and Python.",
        language="Python",
        topics=["drone", "ros2", "navigation", "collision-avoidance"],
        stargazers_count=1450,
        forks_count=420,
        watchers_count=1450,
        open_issues_count=12,
        license_name="MIT License",
        license_spdx="MIT",
        archived=False,
        fork=False
    )
    repo2 = GitHubRepositorySchema(
        github_repository_id=8802,
        full_name="uav-core/autopilot-hub",
        name="autopilot-hub",
        owner_login="uav-core",
        owner_avatar_url="https://avatars.githubusercontent.com/u/8802",
        html_url="https://github.com/uav-core/autopilot-hub",
        description="Core UAV autopilot framework with telemetry dashboard in React and FastAPI backend.",
        language="Python",
        topics=["uav", "telemetry", "fastapi", "react"],
        stargazers_count=3200,
        forks_count=890,
        watchers_count=3200,
        open_issues_count=35,
        license_name="Apache License 2.0",
        license_spdx="Apache-2.0",
        archived=False,
        fork=False
    )
    return [repo1, repo2]

SAMPLE_README_1 = """# Drone Nav - Autonomous Navigation
A production-ready autonomous drone navigation and waypoint mission planner.
## Features
- Dynamic obstacle detection using 3D LiDAR sensors.
- FastDDS telemetry synchronization between companion computer and ground station.
- Automated return-to-home fail-safe mechanisms on signal loss.
## Architecture
Frontend ground control in React and WebSockets.
Backend microservices in Python with FastAPI and ROS 2 middleware.
PostgreSQL database for mission flight logs.
Docker containers with Kubernetes orchestration.
## Installation
```bash
pip install fastapi uvicorn ros2-client
docker compose up
```
"""

SAMPLE_README_2 = """# Autopilot Hub
UAV autopilot and flight control server.
## Key Capabilities
- Mission waypoint trajectory planner.
- Real-time video streaming with WebRTC.
- Geospatial geofencing alerts for no-fly zones.
## Tech Stack
Built with Python 3.11, FastAPI, Celery, Redis, and PyTorch for edge object recognition.
Deployed on AWS ECS with Terraform.
"""

def run_e2e():
    port = 8866
    config = uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning')
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)

    cj1 = http.cookiejar.CookieJar()
    opener1 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj1))

    # 1. Register User 1
    user1_email = f'phase4_3_e2e_{int(time.time())}@projectdna.io'
    reg_data = json.dumps({
        'full_name': 'Deep Analysis Lead',
        'email': user1_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req1 = urllib.request.Request(f'http://127.0.0.1:{port}/api/auth/register', data=reg_data, headers={'Content-Type': 'application/json'})
    opener1.open(req1)
    print(f'[E2E 1] Registered User 1: {user1_email}')

    # 2. Create Project
    p_data = json.dumps({
        'title': 'Autonomous Drone Delivery & Airspace Routing Network',
        'description': 'AI-driven multi-drone delivery system featuring real-time decentralized collision avoidance, dynamic 3D geofencing, and edge computer vision.',
        'domain': 'Robotics & Autonomous Systems',
        'technologies': ['ROS 2', 'Python', 'FastAPI', 'PyTorch', 'Docker']
    }).encode('utf-8')
    req2 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects', data=p_data, headers={'Content-Type': 'application/json'})
    p_res = json.loads(opener1.open(req2).read().decode('utf-8'))
    proj_id = p_res['id']
    print(f'[E2E 2] Created Project: {p_res["title"]} (ID: {proj_id})')

    # 3. Trigger Phase 3 AI Analysis
    with patch.object(AIService, 'analyze_project_idea', return_value=get_sample_analysis_schema()):
        req3 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/analyze', data=b'{}', headers={'Content-Type': 'application/json'})
        a_res = json.loads(opener1.open(req3).read().decode('utf-8'))
        print(f'[E2E 3] Analyzed Project: Version {a_res["version"]} | Keywords: {len(a_res["keywords"])}')

    # 4. Seed Discovered Repositories via GitHub Search
    sample_repos = get_sample_github_repos()
    rate_limit_info = GitHubRateLimitInfo(limit=60, remaining=58, reset=int(time.time()) + 3600)
    with patch.object(GitHubService, 'search_repositories', new_callable=AsyncMock) as mock_gh_search:
        mock_gh_search.return_value = (sample_repos, rate_limit_info)
        search_payload = json.dumps({'max_results': 5}).encode('utf-8')
        req4 = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/search',
            data=search_payload,
            headers={'Content-Type': 'application/json'}
        )
        search_res = json.loads(opener1.open(req4).read().decode('utf-8'))
        print(f'[E2E 4] Seeded Repositories: {search_res["new_stored"]} stored')
        assert search_res['new_stored'] == 2

    # 5. Trigger GitHub Deep Analysis via POST /api/projects/{id}/github/analyze
    async def mock_fetch_readme(owner, repo):
        if 'drone-nav' in repo:
            return True, SAMPLE_README_1, f"https://github.com/{owner}/{repo}#readme", len(SAMPLE_README_1)
        return True, SAMPLE_README_2, f"https://github.com/{owner}/{repo}#readme", len(SAMPLE_README_2)

    async def mock_fetch_deps(owner, repo):
        return {'requirements.txt': 'fastapi==0.104.0\nuvicorn==0.24.0\ntorch==2.1.0'}

    with patch.object(RepositoryAnalyzer, 'fetch_readme', side_effect=mock_fetch_readme), \
         patch.object(RepositoryAnalyzer, 'fetch_dependency_files', side_effect=mock_fetch_deps):

        analyze_payload = json.dumps({'force_refresh': False, 'max_repos': 5}).encode('utf-8')
        req5 = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/analyze',
            data=analyze_payload,
            headers={'Content-Type': 'application/json'}
        )
        analyze_res = json.loads(opener1.open(req5).read().decode('utf-8'))
        print(f'[E2E 5] Deep Analysis Completed: Analyzed {analyze_res["total_analyzed"]} repos | Gaps: {len(analyze_res["innovation_gaps"])} | Mode: {analyze_res["analysis_mode"]}')
        assert analyze_res['status'] == 'completed'
        assert analyze_res['total_analyzed'] == 2
        assert len(analyze_res['innovation_gaps']) >= 1
        assert len(analyze_res['analyzed_repositories']) == 2

        # 6. Re-run Deep Analysis to test idempotent updates
        req6 = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/analyze',
            data=analyze_payload,
            headers={'Content-Type': 'application/json'}
        )
        analyze_res2 = json.loads(opener1.open(req6).read().decode('utf-8'))
        print(f'[E2E 6] Re-run Deep Analysis Idempotency: Analyzed {analyze_res2["total_analyzed"]} repos (updated in-place)')
        assert analyze_res2['total_analyzed'] == 2

    # 7. Retrieve Stored Analyses via GET /api/projects/{id}/github/analysis
    req7 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/analysis?page=1&page_size=10')
    analysis_list_res = json.loads(opener1.open(req7).read().decode('utf-8'))
    print(f'[E2E 7] Retrieved {analysis_list_res["total"]} analyses from GET /analysis')
    assert analysis_list_res['total'] == 2
    first_analysis = analysis_list_res['items'][0]
    first_id = first_analysis['id']
    assert 'detected_technologies' in first_analysis
    assert 'features' in first_analysis
    assert 'similarity' in first_analysis
    assert first_analysis['similarity']['overall_score'] >= 0

    # 8. Retrieve Single Analysis via GET /api/projects/{id}/github/analysis/{analysis_id}
    req8 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/analysis/{first_id}')
    single_res = json.loads(opener1.open(req8).read().decode('utf-8'))
    print(f'[E2E 8] Retrieved single analysis for repo: {single_res["repo_full_name"]}')
    assert single_res['id'] == first_id
    assert single_res['repo_full_name'] in ['autonomous-systems/drone-nav', 'uav-core/autopilot-hub']

    # 9. Retrieve Innovation Gaps via GET /api/projects/{id}/github/innovation-gaps
    req9 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/innovation-gaps')
    gaps_res = json.loads(opener1.open(req9).read().decode('utf-8'))
    print(f'[E2E 9A] Retrieved {gaps_res["total"]} Innovation Gaps')
    assert gaps_res['total'] >= 1
    sample_gap = gaps_res['items'][0]
    assert 'analyzed repositories' in sample_gap['description'].lower()
    assert any('not found in' in g['description'].lower() for g in gaps_res['items'])
    assert sample_gap['priority'] in ['high', 'medium', 'low']

    # Test filtering by priority
    req9_high = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/innovation-gaps?priority=high')
    gaps_high_res = json.loads(opener1.open(req9_high).read().decode('utf-8'))
    print(f'[E2E 9B] Filter priority=high: {gaps_high_res["total"]} gaps found')
    for g in gaps_high_res['items']:
        assert g['priority'] == 'high'

    # 10. Query Analysis Stats via GET /api/projects/{id}/github/analysis/stats
    req10 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/analysis/stats')
    stats_res = json.loads(opener1.open(req10).read().decode('utf-8'))
    print(f'[E2E 10] Deep Analysis Stats: Total Analyzed={stats_res["total_analyzed_repositories"]} | Avg Sim={stats_res["average_similarity_score"]}% | Techs={len(stats_res["technology_distribution"])} | Features={stats_res["total_features_extracted"]} | Gaps={stats_res["innovation_gaps_count"]}')
    assert stats_res['total_analyzed_repositories'] == 2
    assert len(stats_res['technology_distribution']) >= 1
    assert stats_res['total_features_extracted'] >= 1
    assert stats_res['innovation_gaps_count'] >= 1

    # 11. Register User 2 and Test Cross-User Isolation
    cj2 = http.cookiejar.CookieJar()
    opener2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj2))
    user2_email = f'phase4_3_intruder_{int(time.time())}@projectdna.io'
    reg_data2 = json.dumps({
        'full_name': 'Unauthorized Competitor',
        'email': user2_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req11 = urllib.request.Request(f'http://127.0.0.1:{port}/api/auth/register', data=reg_data2, headers={'Content-Type': 'application/json'})
    opener2.open(req11)

    # 11A. User 2 tries POST /analyze on User 1's project -> 403
    try:
        req_forbidden_analyze = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/analyze',
            data=b'{}',
            headers={'Content-Type': 'application/json'}
        )
        opener2.open(req_forbidden_analyze)
        assert False, "User 2 should have been rejected with 403 on POST /analyze"
    except urllib.error.HTTPError as err:
        print(f'[E2E 11A] Cross-User POST /analyze Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    # 11B. User 2 tries GET /analysis on User 1's project -> 403
    try:
        req_forbidden_get = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/analysis')
        opener2.open(req_forbidden_get)
        assert False, "User 2 should have been rejected with 403 on GET /analysis"
    except urllib.error.HTTPError as err:
        print(f'[E2E 11B] Cross-User GET /analysis Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    # 11C. User 2 tries GET /analysis/{id} on User 1's analysis -> 403
    try:
        req_forbidden_single = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/analysis/{first_id}')
        opener2.open(req_forbidden_single)
        assert False, "User 2 should have been rejected with 403 on GET /analysis/{id}"
    except urllib.error.HTTPError as err:
        print(f'[E2E 11C] Cross-User GET /analysis/{{id}} Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    # 11D. User 2 tries GET /innovation-gaps on User 1's project -> 403
    try:
        req_forbidden_gaps = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/innovation-gaps')
        opener2.open(req_forbidden_gaps)
        assert False, "User 2 should have been rejected with 403 on GET /innovation-gaps"
    except urllib.error.HTTPError as err:
        print(f'[E2E 11D] Cross-User GET /innovation-gaps Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    # 11E. User 2 tries GET /analysis/stats on User 1's project -> 403
    try:
        req_forbidden_stats = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/analysis/stats')
        opener2.open(req_forbidden_stats)
        assert False, "User 2 should have been rejected with 403 on GET /analysis/stats"
    except urllib.error.HTTPError as err:
        print(f'[E2E 11E] Cross-User GET /analysis/stats Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    server.should_exit = True
    print('\n================================================================')
    print('>>> ALL PHASE 4.3 END-TO-END HTTP WORKFLOW TESTS PASSED 100%! <<<')
    print('================================================================')

if __name__ == '__main__':
    run_e2e()
