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
from app.schemas.github import GitHubRepositorySchema, GitHubRateLimitInfo
from test_phase3_ai import get_sample_analysis_schema

def get_sample_github_repos():
    repo1 = GitHubRepositorySchema(
        github_repository_id=1234567,
        full_name="ros-planning/navigation2",
        name="navigation2",
        owner_login="ros-planning",
        owner_avatar_url="https://avatars.githubusercontent.com/u/445566",
        html_url="https://github.com/ros-planning/navigation2",
        description="ROS 2 Navigation Framework and System for Autonomous Mobile Robots.",
        language="C++",
        topics=["ros2", "navigation", "autonomous-robots", "path-planning"],
        stargazers_count=2150,
        forks_count=980,
        watchers_count=2150,
        open_issues_count=65,
        license_name="Apache License 2.0",
        license_spdx="Apache-2.0",
        archived=False,
        fork=False
    )
    repo2 = GitHubRepositorySchema(
        github_repository_id=2345678,
        full_name="PX4/PX4-Autopilot",
        name="PX4-Autopilot",
        owner_login="PX4",
        owner_avatar_url="https://avatars.githubusercontent.com/u/778899",
        html_url="https://github.com/PX4/PX4-Autopilot",
        description="PX4 Autopilot Software for drones and other autonomous vehicles.",
        language="C++",
        topics=["px4", "autopilot", "drone", "uav", "flight-controller"],
        stargazers_count=7400,
        forks_count=4100,
        watchers_count=7400,
        open_issues_count=320,
        license_name="BSD 3-Clause",
        license_spdx="BSD-3-Clause",
        archived=False,
        fork=False
    )
    repo3 = GitHubRepositorySchema(
        github_repository_id=3456789,
        full_name="mit-acl/uav_simulator",
        name="uav_simulator",
        owner_login="mit-acl",
        owner_avatar_url="https://avatars.githubusercontent.com/u/112233",
        html_url="https://github.com/mit-acl/uav_simulator",
        description="Simulation packages for aerial vehicle navigation, planning and collision avoidance.",
        language="Python",
        topics=["uav", "quadrotor", "simulation", "collision-avoidance"],
        stargazers_count=890,
        forks_count=310,
        watchers_count=890,
        open_issues_count=18,
        license_name="MIT License",
        license_spdx="MIT",
        archived=False,
        fork=False
    )
    return [repo1, repo2, repo3]

def run_e2e():
    port = 8899
    config = uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning')
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)

    cj1 = http.cookiejar.CookieJar()
    opener1 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj1))

    # 1. Register User 1
    user1_email = f'github_e2e_{int(time.time())}@projectdna.io'
    reg_data = json.dumps({
        'full_name': 'GitHub Discovery Engineer',
        'email': user1_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req1 = urllib.request.Request(f'http://127.0.0.1:{port}/api/auth/register', data=reg_data, headers={'Content-Type': 'application/json'})
    opener1.open(req1)
    print(f'[E2E 1] Registered User 1: {user1_email}')

    # 2. Create Project
    p_data = json.dumps({
        'title': 'Autonomous Drone Delivery Routing & Collision Avoidance',
        'description': 'Decentralized multi-drone routing and 3D geofencing system for urban airspace logistics.',
        'domain': 'Robotics & Autonomous Systems',
        'technologies': ['ROS 2', 'PX4', 'Python', 'C++']
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

    # 4. Trigger GitHub Repository Discovery via POST /api/projects/{id}/github/search
    sample_repos = get_sample_github_repos()
    rate_limit_info = GitHubRateLimitInfo(limit=60, remaining=55, reset=int(time.time()) + 3600)

    with patch.object(GitHubService, 'search_repositories', new_callable=AsyncMock) as mock_gh_search:
        mock_gh_search.return_value = (sample_repos, rate_limit_info)

        search_payload = json.dumps({'max_results': 10}).encode('utf-8')
        req4 = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/search',
            data=search_payload,
            headers={'Content-Type': 'application/json'}
        )
        search_res = json.loads(opener1.open(req4).read().decode('utf-8'))
        print(f'[E2E 4] GitHub Discovery Status: {search_res["status"]} | Stored: {search_res["new_stored"]} repos | Total: {search_res["total_stored_repositories"]}')
        assert search_res['status'] == 'completed'
        assert search_res['new_stored'] == 3
        assert search_res['total_stored_repositories'] == 3
        assert search_res['rate_limit']['remaining'] == 55

        # 5. Re-run search to verify deduplication and existing_updated
        req5 = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/search',
            data=search_payload,
            headers={'Content-Type': 'application/json'}
        )
        search_res2 = json.loads(opener1.open(req5).read().decode('utf-8'))
        print(f'[E2E 5] Re-run Deduplication: New Stored = {search_res2["new_stored"]}, Updated = {search_res2["existing_updated"]}')
        assert search_res2['new_stored'] == 0
        assert search_res2['existing_updated'] == 3
        assert search_res2['total_stored_repositories'] == 3

    # 6. Retrieve Stored Repositories via GET /api/projects/{id}/github
    req6 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github?page=1&page_size=10')
    repos_res = json.loads(opener1.open(req6).read().decode('utf-8'))
    print(f'[E2E 6] Retrieved {repos_res["total"]} repositories via GET /api/projects/{proj_id}/github')
    assert repos_res['total'] == 3
    assert len(repos_res['items']) == 3

    # 7. Test Retrieval Filters (language='Python')
    req7_py = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github?language=Python')
    py_filter_res = json.loads(opener1.open(req7_py).read().decode('utf-8'))
    print(f'[E2E 7A] Filter language=Python: {py_filter_res["total"]} repository found')
    assert py_filter_res['total'] == 1
    assert py_filter_res['items'][0]['language'] == 'Python'

    # Filter min_stars=5000
    req7_stars = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github?min_stars=5000')
    stars_filter_res = json.loads(opener1.open(req7_stars).read().decode('utf-8'))
    print(f'[E2E 7B] Filter min_stars=5000: {stars_filter_res["total"]} repository found')
    assert stars_filter_res['total'] == 1
    assert stars_filter_res['items'][0]['name'] == 'PX4-Autopilot'

    # Filter search text = 'navigation'
    req7_search = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github?search=navigation')
    search_filter_res = json.loads(opener1.open(req7_search).read().decode('utf-8'))
    print(f'[E2E 7C] Filter search=navigation: {search_filter_res["total"]} repository found')
    assert search_filter_res['total'] >= 1

    # 8. Query Repository Stats via GET /api/projects/{id}/github/stats
    req8 = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/stats')
    stats_res = json.loads(opener1.open(req8).read().decode('utf-8'))
    print(f'[E2E 8] GitHub Stats: Total = {stats_res["total_repositories"]} | Stars = {stats_res["total_stars"]} | Forks = {stats_res["total_forks"]} | Langs = {stats_res["language_distribution"]}')
    assert stats_res['total_repositories'] == 3
    assert stats_res['total_stars'] == 2150 + 7400 + 890
    assert stats_res['total_forks'] == 980 + 4100 + 310
    assert stats_res['language_distribution'].get('C++') == 2
    assert stats_res['language_distribution'].get('Python') == 1

    # 9. Register User 2 and Test Cross-User Isolation
    cj2 = http.cookiejar.CookieJar()
    opener2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj2))
    user2_email = f'github_intruder_{int(time.time())}@projectdna.io'
    reg_data2 = json.dumps({
        'full_name': 'E2E Intruder User',
        'email': user2_email,
        'password': 'Password123!'
    }).encode('utf-8')
    req9 = urllib.request.Request(f'http://127.0.0.1:{port}/api/auth/register', data=reg_data2, headers={'Content-Type': 'application/json'})
    opener2.open(req9)

    # User 2 tries to access User 1's GitHub repositories
    try:
        req_forbidden = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github')
        opener2.open(req_forbidden)
        assert False, "User 2 should have been rejected with 403 on GET /github"
    except urllib.error.HTTPError as err:
        print(f'[E2E 9A] Cross-User GET Repos Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    try:
        req_forbidden_stats = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/stats')
        opener2.open(req_forbidden_stats)
        assert False, "User 2 should have been rejected with 403 on GET /github/stats"
    except urllib.error.HTTPError as err:
        print(f'[E2E 9B] Cross-User GET Stats Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    try:
        req_forbidden_search = urllib.request.Request(
            f'http://127.0.0.1:{port}/api/projects/{proj_id}/github/search',
            data=b'{"max_results": 10}',
            headers={'Content-Type': 'application/json'}
        )
        opener2.open(req_forbidden_search)
        assert False, "User 2 should have been rejected with 403 on POST /github/search"
    except urllib.error.HTTPError as err:
        print(f'[E2E 9C] Cross-User Search Blocked: Status {err.code} (Forbidden)')
        assert err.code == 403

    server.should_exit = True
    print('\n================================================================')
    print('>>> ALL PHASE 4.2 END-TO-END HTTP WORKFLOW TESTS PASSED 100%! <<<')
    print('================================================================')

if __name__ == '__main__':
    run_e2e()
