import sys
sys.path.insert(0, 'backend')

from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.services.project_service import ProjectService
from app.routes.health import get_health
from app.routes.projects import list_projects, create_project, get_project
from app.schemas.project import ProjectCreate

def run_tests():
    print("--- 1. Initializing schema & seeding sample data ---")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    ProjectService.seed_initial_samples_if_empty(db)
    
    print("\n--- 2. Testing Health Route (GET /api/health) ---")
    health = get_health()
    print(f"Status: {health.status}, App: {health.app_name}, Dialect: {health.database.get('dialect')}")
    assert health.status in ("healthy", "degraded")
    assert health.database.get("status") == "connected"
    
    print("\n--- 3. Testing Project List Route (GET /api/projects) ---")
    projs_resp = list_projects(search=None, domain=None, status=None, page=1, limit=50, db=db)
    print(f"Total projects found: {projs_resp.total}")
    assert projs_resp.total >= 4
    for p in projs_resp.items[:2]:
        print(f"  - [{p.domain}] {p.title} (Status: {p.status})")
        
    print("\n--- 4. Testing Project Creation Route (POST /api/projects) ---")
    new_payload = ProjectCreate(
        title="Autonomous Bio-Sensor Mesh",
        description="Distributed edge sensing network for real-time groundwater contaminant detection using micro-optical resonance.",
        domain="IoT & Robotics",
        technologies=["Python", "FastAPI", "Rust", "Embedded C", "React"],
        objectives="Demonstrate <10ppb heavy metal detection with 99.2% uptime across 50 field nodes."
    )
    created = create_project(project_in=new_payload, db=db)
    print(f"Created Project ID: {created.id}")
    print(f"Title: {created.title}")
    print(f"Status: {created.status}")
    assert created.id is not None
    assert created.status == "pending_validation"
    assert created.title == new_payload.title
    
    print("\n--- 5. Testing Single Project Retrieval Route (GET /api/projects/{id}) ---")
    fetched = get_project(project_id=created.id, db=db)
    print(f"Retrieved: {fetched.title} (Domain: {fetched.domain})")
    assert fetched.id == created.id
    
    print("\n--- 6. Testing Search & Filtering ---")
    search_res = list_projects(search="Bio-Sensor", domain="IoT & Robotics", status=None, page=1, limit=50, db=db)
    print(f"Filtered search results: {search_res.total} matches")
    assert search_res.total >= 1
    assert any("Bio-Sensor" in item.title for item in search_res.items)

    db.close()
    print("\n=======================================================")
    print(">>> ALL 6 DATABASE & API ROUTE TESTS PASSED 100%! <<<")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
