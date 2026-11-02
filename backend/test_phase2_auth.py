import sys
import time
from datetime import timedelta
sys.path.insert(0, 'backend')

from app.database.base import Base
from app.database.session import engine, SessionLocal, apply_safe_schema_migrations
import app.models  # noqa: F401
from app.schemas.user import UserRegister, UserLogin
from app.schemas.project import ProjectCreate
from app.services.user_service import UserService
from app.services.project_service import ProjectService
from app.core.security import create_access_token, decode_access_token
from app.routes.auth import register, login, logout, get_current_user_profile
from app.routes.projects import list_projects, create_project, get_project
from app.routes.health import get_health
from fastapi import HTTPException, Response

def run_phase2_tests():
    print("================================================================")
    print(">>> AI ProjectDNA - Phase 2 Comprehensive Test Suite <<<")
    print("================================================================")

    # Database setup & migrations
    Base.metadata.create_all(bind=engine)
    apply_safe_schema_migrations()
    db = SessionLocal()
    ProjectService.seed_initial_samples_if_empty(db)

    # 1. New user registration
    print("\n[TEST 1] User Registration:")
    user_a_email = f"user_a_{int(time.time())}@projectdna.io"
    user_a_payload = UserRegister(
        full_name="Dr. Alan Turing",
        email=user_a_email,
        password="SuperSecretPassword123!"
    )
    resp = Response()
    auth_res_a = register(user_in=user_a_payload, response=resp, db=db)
    user_a = auth_res_a.user
    token_a = auth_res_a.access_token
    print(f"  [OK] User A registered: {user_a.email} (ID: {user_a.id})")
    assert user_a.id is not None
    assert token_a is not None
    assert "projectdna_access_token" in resp.headers.get("set-cookie", "")

    # 2. Duplicate email registration rejection
    print("\n[TEST 2] Duplicate Email Registration Rejection:")
    try:
        register(user_in=user_a_payload, response=Response(), db=db)
        assert False, "Duplicate email registration should have raised HTTPException 409"
    except HTTPException as e:
        print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
        assert e.status_code == 409

    # 3. Login with correct credentials
    print("\n[TEST 3] Login with Correct Credentials:")
    login_payload = UserLogin(email=user_a_email, password="SuperSecretPassword123!")
    login_resp = Response()
    auth_login = login(credentials=login_payload, response=login_resp, db=db)
    print(f"  [OK] Successfully authenticated: {auth_login.user.email}")
    assert auth_login.user.id == user_a.id
    assert auth_login.access_token is not None

    # 4. Login with incorrect credentials
    print("\n[TEST 4] Login with Incorrect Credentials:")
    bad_login = UserLogin(email=user_a_email, password="WrongPassword999!")
    try:
        login(credentials=bad_login, response=Response(), db=db)
        assert False, "Invalid password should have raised HTTPException 401"
    except HTTPException as e:
        print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
        assert e.status_code == 401

    # 5. Access protected APIs without authentication
    print("\n[TEST 5] Unauthenticated Access Protection:")
    from fastapi import Request
    from app.core.deps import get_current_user

    dummy_request = Request({"type": "http", "method": "GET", "path": "/api/projects", "headers": []})
    try:
        get_current_user(request=dummy_request, auth_header=None, db=db)
        assert False, "Accessing protected endpoint without token should raise 401"
    except HTTPException as e:
        print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
        assert e.status_code == 401

    # 6. Create a project as User A
    print("\n[TEST 6] Create Project as User A:")
    user_a_db_model = UserService.get_by_id(db, user_a.id)
    proj_a_payload = ProjectCreate(
        title="Neural Quantum Simulator",
        description="Simulating noisy intermediate-scale quantum circuits on edge GPU clusters.",
        domain="Artificial Intelligence & ML",
        technologies=["Python", "PyTorch", "CUDA", "FastAPI"],
        objectives="Achieve 40-qubit circuit simulation under 200ms latency."
    )
    proj_a = create_project(project_in=proj_a_payload, current_user=user_a_db_model, db=db)
    print(f"  [OK] Project created: '{proj_a.title}' (ID: {proj_a.id}, Owner: {proj_a.user_id})")
    assert proj_a.user_id == user_a.id

    # Verify User A can list their project
    user_a_projs = list_projects(search=None, domain=None, status=None, page=1, limit=50, current_user=user_a_db_model, db=db)
    print(f"  [OK] User A project count: {user_a_projs.total}")
    assert user_a_projs.total >= 1
    assert any(p.id == proj_a.id for p in user_a_projs.items)

    # 7. Register User B and verify User A's project is strictly inaccessible
    print("\n[TEST 7] Multi-Tenant Isolation (User B cannot access User A's project):")
    user_b_email = f"user_b_{int(time.time())}@projectdna.io"
    user_b_payload = UserRegister(
        full_name="Ada Lovelace",
        email=user_b_email,
        password="AdaPassword456!"
    )
    auth_res_b = register(user_in=user_b_payload, response=Response(), db=db)
    user_b_db_model = UserService.get_by_id(db, auth_res_b.user.id)

    # User B list should NOT show User A's project
    user_b_projs = list_projects(search=None, domain=None, status=None, page=1, limit=50, current_user=user_b_db_model, db=db)
    print(f"  [OK] User B sees only their projects: count = {user_b_projs.total}")
    assert not any(p.id == proj_a.id for p in user_b_projs.items)

    # User B attempting to fetch User A's project by ID should receive 403 Forbidden
    try:
        get_project(project_id=proj_a.id, current_user=user_b_db_model, db=db)
        assert False, "User B should not be able to retrieve User A's project"
    except HTTPException as e:
        print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
        assert e.status_code == 403

    # 8. Logout verification
    print("\n[TEST 8] User Logout:")
    logout_resp = Response()
    logout_res = logout(response=logout_resp)
    print(f"  [OK] Logout response: {logout_res['message']}")
    set_cookie_header = logout_resp.headers.get("set-cookie", "")
    assert "projectdna_access_token" in set_cookie_header

    # 9. Token Expiration Handling
    print("\n[TEST 9] Token Expiration Handling:")
    expired_token = create_access_token(
        subject=user_a.id,
        expires_delta=timedelta(seconds=-10)  # already expired
    )
    decoded = decode_access_token(expired_token)
    print(f"  [OK] Expired token validation result: {decoded}")
    assert decoded is None

    # 10. Phase 1 compatibility check
    print("\n[TEST 10] Phase 1 Functionality Preservation:")
    health = get_health()
    print(f"  [OK] Health check: status='{health.status}', app='{health.app_name}', db='{health.database.get('status')}'")
    assert health.status in ("healthy", "degraded")

    db.close()
    print("\n================================================================")
    print(">>> ALL 10 PHASE 2 BACKEND & AUTH TESTS PASSED 100%! <<<")
    print("================================================================")

if __name__ == "__main__":
    run_phase2_tests()
