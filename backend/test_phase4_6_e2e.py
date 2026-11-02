"""
Live HTTP End-to-End Test: Phase 4.6 Patent & Prior-Art Discovery Engine
Tests the complete HTTP workflow:
1. Live FastAPI server bootstrap on port 8899
2. User registration and project creation
3. Analysis and patent seeding
4. POST /api/projects/{id}/patents/search (patent search execution, normalization, deduplication & embedding)
5. GET /api/projects/{id}/patents (paginated listing with cosine similarities & bands)
6. GET /api/projects/{id}/patents/stats (aggregated statistics by provider, jurisdiction, classifications)
7. GET /api/projects/{id}/patents/{patent_id} (single patent detail retrieval)
8. POST /api/projects/{id}/patents/analyze (prior-art deep analysis generation)
9. GET /api/projects/{id}/patents/analysis (retrieval of prior-art analysis)
10. GET /api/projects/{id}/patents/evidence (patent evidence manifest explorer with EVID-PAT-01..N)
11. POST /api/projects/{id}/validation/generate (Phase 4.5 RAG integration: patents included in evidence manifest & report)
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
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, 'backend')
import uvicorn
from app.main import app
from app.database.session import SessionLocal
from app.models.patent import Patent
from app.models.analysis import ProjectAnalysis
from app.schemas.patent import PatentSchema


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
    user1_email = f'phase4_6_e2e_{int(time.time())}@projectdna.io'
    reg_data = json.dumps({
        'full_name': 'Patent Analysis Lead',
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
        'title': 'QuantumSecure Distributed Ledger',
        'description': 'Post-quantum lattice-based cryptographic consensus and zero-knowledge validation for distributed networks.',
        'domain': 'cybersecurity',
        'technologies': ['Rust', 'Python', 'FastAPI', 'Kyber']
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

    # 3. Seed Analysis Record
    db = SessionLocal()
    analysis = ProjectAnalysis(
        id=str(uuid.uuid4()),
        project_id=proj_id,
        user_id=user1_id,
        version=1,
        project_summary='Post-quantum cryptographic distributed ledger utilizing lattice consensus.',
        problem_statement='Vulnerability of classical elliptic curve consensus against Shor algorithm.',
        proposed_solution='Module-LWE and ring-SIS cryptographic consensus protocol.',
        primary_domain='cybersecurity',
        secondary_domains=['blockchain', 'cryptography'],
        keywords=['post-quantum', 'lattice cryptography', 'distributed ledger', 'zero-knowledge proofs'],
        user_technologies=['Rust', 'Kyber'],
        recommended_technologies={'framework': ['FastAPI', 'Substrate']},
        objectives=['Ensure 128-bit quantum security margin', 'Sub-2-second block finality'],
        target_users=['Financial institutions', 'Government security agencies'],
        project_type='Systems & Cryptography',
        difficulty_level='Advanced',
        difficulty_reasoning='Requires post-quantum lattice mathematics.',
        requirements={'cryptography': ['Kyber-768']},
        assumptions=['Standard lattice hardness bounds hold'],
        risks={'performance': ['Larger public key and ciphertext sizes']},
        model_name='test-model',
        analysis_status='completed'
    )
    db.add(analysis)
    db.commit()
    print('[E2E 3] Seeded ProjectAnalysis record')

    # Seed mock patents directly so search can deduplicate and persist
    mock_pat1 = Patent(
        project_id=proj_id,
        user_id=user1_id,
        provider='uspto',
        provider_patent_id='11444555',
        publication_number='US11444555B2',
        title='Lattice-Based Post-Quantum Consensus System',
        abstract='Discloses cryptographic consensus algorithms using module learning with errors over ring polynomial structures.',
        claims=['1. A cryptographic ledger method comprising lattice verification.'],
        inventors=['Dr. Claude Shannon'],
        assignees=['Quantum Defense Corp'],
        jurisdiction='US',
        cpc_classifications=['H04L9/08', 'H04L9/30', 'G06F21/60'],
        publication_date='2023-09-12',
        source_url='https://patents.google.com/patent/US11444555B2/en'
    )
    mock_pat2 = Patent(
        project_id=proj_id,
        user_id=user1_id,
        provider='epo',
        provider_patent_id='EP3888999',
        publication_number='EP3888999A1',
        title='Zero-Knowledge Lattice Proof Generation Apparatus',
        abstract='An apparatus for zero-knowledge argument construction utilizing short integer solution problems.',
        claims=['1. An electronic computing apparatus for generating lattice proofs.'],
        inventors=['Ada Lovelace'],
        assignees=['EuroCrypt Labs'],
        jurisdiction='EP',
        cpc_classifications=['H04L9/32'],
        publication_date='2022-11-05',
        source_url='https://patents.google.com/patent/EP3888999A1/en'
    )
    db.add_all([mock_pat1, mock_pat2])
    db.commit()
    pat1_id = mock_pat1.id
    pat2_id = mock_pat2.id
    db.close()
    print('[E2E 4] Seeded initial candidate Patent records in database')

    # 4. POST /api/projects/{id}/patents/search
    search_payload = json.dumps({
        'max_results': 10,
        'providers': ['uspto', 'epo']
    }).encode('utf-8')
    req_search = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/patents/search',
        data=search_payload,
        headers={'Content-Type': 'application/json'}
    )
    search_res = json.loads(opener1.open(req_search).read().decode('utf-8'))
    print(f'[E2E 5] Executed Patent Search: status={search_res["status"]}, total_stored={search_res["total_stored_patents"]}')
    assert search_res['total_stored_patents'] >= 2
    assert 'disclaimer' in search_res
    assert 'Preliminary research assistance' in search_res['disclaimer']

    # 5. GET /api/projects/{id}/patents
    req_list = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/patents?sort_by=similarity')
    list_res = json.loads(opener1.open(req_list).read().decode('utf-8'))
    print(f'[E2E 6] Retrieved Patents list: total={list_res["total"]}, items={len(list_res["items"])}')
    assert list_res['total'] >= 2
    first_item = list_res['items'][0]
    print(f'       Top Patent: {first_item["publication_number"]} | Similarity: {first_item.get("similarity_score")} | Band: {first_item.get("similarity_band")}')
    assert first_item['similarity_score'] is not None
    assert first_item['similarity_band'] in ['High semantic similarity', 'Moderate semantic similarity', 'Low semantic similarity']
    assert first_item['source_url'].startswith('https://patents.google.com')

    # 6. GET /api/projects/{id}/patents/stats
    req_stats = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/patents/stats')
    stats_res = json.loads(opener1.open(req_stats).read().decode('utf-8'))
    print(f'[E2E 7] Retrieved Patent Stats: total={stats_res["total_patents"]}, providers={stats_res["by_provider"]}, jurisdictions={stats_res["by_jurisdiction"]}')
    assert stats_res['total_patents'] >= 2
    assert 'US' in stats_res['by_jurisdiction']
    assert 'EP' in stats_res['by_jurisdiction']

    # 7. GET /api/projects/{id}/patents/{patent_id}
    req_single = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/patents/{pat1_id}')
    single_res = json.loads(opener1.open(req_single).read().decode('utf-8'))
    print(f'[E2E 8] Retrieved Single Patent: {single_res["publication_number"]} - {single_res["title"]}')
    assert single_res['id'] == pat1_id
    assert single_res['publication_number'] == 'US11444555B2'

    # 8. POST /api/projects/{id}/patents/analyze
    req_analyze = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/patents/analyze',
        data=json.dumps({'max_patents': 5}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    analyze_res = json.loads(opener1.open(req_analyze).read().decode('utf-8'))
    print(f'[E2E 9] Executed Prior-Art Deep Analysis: analyzed={analyze_res["total_analyzed"]}')
    assert analyze_res['total_analyzed'] >= 2
    assert len(analyze_res['prior_art_analyses']) >= 2
    first_analysis = analyze_res['prior_art_analyses'][0]
    print(f'       Problem: {first_analysis["technical_problem"][:80]}...')
    print(f'       Solution: {first_analysis["proposed_solution"][:80]}...')
    print(f'       Claims Overlap: {first_analysis["claims_overlap_analysis"][:80]}...')
    assert len(first_analysis['key_features']) > 0
    assert len(first_analysis['similarities_with_idea']) > 0
    assert len(first_analysis['differences_from_idea']) > 0
    assert len(analyze_res['technical_differentiation_opportunities']) > 0
    assert 'disclaimer' in analyze_res

    # 9. GET /api/projects/{id}/patents/analysis
    req_get_analysis = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/patents/analysis')
    get_analysis_res = json.loads(opener1.open(req_get_analysis).read().decode('utf-8'))
    print(f'[E2E 10] Retrieved Cached Prior-Art Analysis: analyzed={get_analysis_res["total_analyzed"]}')
    assert get_analysis_res['total_analyzed'] >= 2

    # 10. GET /api/projects/{id}/patents/evidence
    req_evid = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/patents/evidence')
    evid_res = json.loads(opener1.open(req_evid).read().decode('utf-8'))
    print(f'[E2E 11] Retrieved Patent Evidence Manifest: count={len(evid_res)}')
    assert len(evid_res) >= 2
    assert evid_res[0]['evidence_id'].startswith('EVID-PAT-')

    # 11. POST /api/projects/{id}/validation/generate (Phase 4.5 RAG integration test)
    val_payload = json.dumps({
        'force_regenerate': True,
        'include_embeddings': True
    }).encode('utf-8')
    req_val = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/projects/{proj_id}/validation/generate',
        data=val_payload,
        headers={'Content-Type': 'application/json'}
    )
    val_res = json.loads(opener1.open(req_val).read().decode('utf-8'))
    print(f'[E2E 12] Generated RAG Validation Report with Patent Integration: v{val_res["version"]}')
    assert val_res['report_status'] == 'completed'
    # Verify patent items exist in evidence manifest
    manifest_items = val_res.get('evidence_manifest', [])
    patent_evids = [e for e in manifest_items if e.get('source_type') == 'patent']
    print(f'        Found {len(patent_evids)} patent evidence items in RAG manifest (IDs: {[e["evidence_id"] for e in patent_evids]})')
    assert len(patent_evids) >= 2

    # 12. Multi-tenant security isolation check
    cj2 = http.cookiejar.CookieJar()
    opener2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj2))
    user2_email = f'phase4_6_intruder_{int(time.time())}@projectdna.io'
    req_u2 = urllib.request.Request(
        f'http://127.0.0.1:{port}/api/auth/register',
        data=json.dumps({'full_name': 'Unauthorized User', 'email': user2_email, 'password': 'Password123!'}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    opener2.open(req_u2)
    print(f'[E2E 13] Registered User 2: {user2_email}')

    # User 2 attempts to view User 1's patents
    try:
        req_unauth = urllib.request.Request(f'http://127.0.0.1:{port}/api/projects/{proj_id}/patents')
        opener2.open(req_unauth)
        raise AssertionError('Expected HTTP 403 Forbidden for unauthorized user!')
    except urllib.error.HTTPError as err:
        assert err.code == 403
        print(f'[E2E 14] Cross-user access correctly rejected with HTTP 403 Forbidden')

    print('\n========================================================================')
    print('ALL 14 E2E TEST CHECKS PASSED FOR PHASE 4.6 PATENT ENGINE SUCCESSFULLY!')
    print('========================================================================\n')


if __name__ == '__main__':
    run_e2e()

