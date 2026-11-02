import sys
import threading
import time
import urllib.request
import json
import http.cookiejar
from unittest.mock import patch

sys.path.insert(0, 'backend')
import uvicorn
from app.main import app
from app.services.ai_service import AIService
from test_phase3_ai import get_sample_analysis_schema

def run_e2e():
    config = uvicorn.Config(app, host='127.0.0.1', port=8866, log_level='warning')
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. Register User
    reg_data = json.dumps({
        'full_name': 'E2E Phase 3 User',
        'email': f'e2e_{int(time.time())}@projectdna.io',
        'password': 'Password123!'
    }).encode('utf-8')
    req1 = urllib.request.Request('http://127.0.0.1:8866/api/auth/register', data=reg_data, headers={'Content-Type': 'application/json'})
    opener.open(req1)

    # 2. Create Project
    p_data = json.dumps({
        'title': 'DeepGeo: Hyperspectral Mineral Mapping',
        'description': 'Deep convolutional neural network for real-time mineral classification from satellite imagery.',
        'domain': 'Artificial Intelligence & ML',
        'technologies': ['PyTorch', 'FastAPI', 'CUDA']
    }).encode('utf-8')
    req2 = urllib.request.Request('http://127.0.0.1:8866/api/projects', data=p_data, headers={'Content-Type': 'application/json'})
    p_res = json.loads(opener.open(req2).read().decode('utf-8'))
    proj_id = p_res['id']
    print(f'[E2E-P3 1] Created project: {p_res["title"]} (ID: {proj_id})')

    # 3. Trigger Analysis via POST /api/projects/{id}/analyze
    with patch.object(AIService, 'analyze_project_idea', return_value=get_sample_analysis_schema()):
        req3 = urllib.request.Request(f'http://127.0.0.1:8866/api/projects/{proj_id}/analyze', data=b'{}', headers={'Content-Type': 'application/json'})
        a_res = json.loads(opener.open(req3).read().decode('utf-8'))
        print(f'[E2E-P3 2] Analyzed project: Version {a_res["version"]} | Domain: {a_res["primary_domain"]}')
        assert a_res['version'] == 1
        assert len(a_res['keywords']) >= 10

    # 4. Retrieve Analysis via GET /api/projects/{id}/analysis
    req4 = urllib.request.Request(f'http://127.0.0.1:8866/api/projects/{proj_id}/analysis')
    get_a = json.loads(opener.open(req4).read().decode('utf-8'))
    print(f'[E2E-P3 3] Retrieved latest analysis: Difficulty = {get_a["difficulty_level"]}')
    assert get_a['id'] == a_res['id']

    # 5. Query Dashboard Stats
    req5 = urllib.request.Request('http://127.0.0.1:8866/api/analyses/dashboard/stats')
    stats = json.loads(opener.open(req5).read().decode('utf-8'))
    print(f'[E2E-P3 4] Dashboard stats verified: Ideas Analyzed = {stats["ideas_analyzed"]}, Completed Runs = {stats["completed_analyses"]}')
    assert stats['ideas_analyzed'] >= 1
    assert stats['completed_analyses'] >= 1

    server.should_exit = True
    print('\n>>> PHASE 3 END-TO-END HTTP WORKFLOW TEST PASSED 100%! <<<')

if __name__ == '__main__':
    run_e2e()

