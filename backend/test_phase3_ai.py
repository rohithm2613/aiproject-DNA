import sys
import time
from unittest.mock import MagicMock, patch
sys.path.insert(0, 'backend')

from fastapi import HTTPException
from app.database.base import Base
from app.database.session import engine, SessionLocal, apply_safe_schema_migrations
import app.models  # noqa: F401
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.schemas.user import UserRegister
from app.schemas.project import ProjectCreate
from app.schemas.analysis import (
    ProjectAnalysisSchema,
    RecommendedTechnologiesSchema,
    ProjectRequirementsSchema,
    ProjectRisksSchema,
)
from app.services.user_service import UserService
from app.services.project_service import ProjectService
from app.services.project_analysis_service import ProjectAnalysisService
from app.services.ai_service import AIService
from app.routes.analysis import (
    trigger_project_analysis,
    get_project_analysis,
    get_project_analysis_history,
    get_dashboard_stats,
    get_analysis_by_id,
)
from app.core.config import settings

def get_sample_analysis_schema() -> ProjectAnalysisSchema:
    return ProjectAnalysisSchema(
        project_summary="An autonomous drone routing system leveraging reinforcement learning to optimize urban air delivery corridors.",
        problem_statement="Urban delivery logistics suffer from congested ground transport, high carbon emissions, and lack of coordinated lower-altitude airspace corridors.",
        proposed_solution="A decentralized multi-agent routing network with dynamic geofencing, collision avoidance, and energy-aware battery charging dispatch.",
        primary_domain="Robotics & Autonomous Systems",
        secondary_domains=["Artificial Intelligence", "CleanTech & Smart Cities", "Internet of Things"],
        keywords=[
            "Reinforcement Learning", "UAV Path Planning", "Dynamic Geofencing", "Multi-Agent Systems",
            "Autonomous Navigation", "Airspace Deconfliction", "Edge Computing", "Sensor Fusion",
            "Swarm Intelligence", "Urban Air Mobility", "Battery Optimization", "ROS 2"
        ],
        recommended_technologies=RecommendedTechnologiesSchema(
            languages=["Python", "C++", "Rust"],
            frameworks=["PyTorch", "ROS 2 Humble", "Ray RLlib", "PX4 Autopilot"],
            algorithms=["Proximal Policy Optimization (PPO)", "Multi-Agent DDPG", "A* 3D Search"],
            hardware=["NVIDIA Jetson Orin Nano", "LiDAR Rangefinder", "RTK-GPS Receiver"],
            tools=["Gazebo Garden Simulator", "Docker", "Wireshark MAVLink"],
            infrastructure=["PostGIS Geospatial DB", "MQTT Broker", "FastAPI Edge Gateway"]
        ),
        objectives=[
            "Design a 3D airspace grid model with real-time dynamic obstacle geofencing.",
            "Train a multi-agent reinforcement learning policy for 20+ simultaneous delivery drones.",
            "Reduce total mission delivery energy consumption by >15% compared to static waypoints.",
            "Demonstrate fail-safe return-to-launch (RTL) protocol with <100ms trigger latency."
        ],
        target_users=[
            "Commercial drone delivery operators",
            "Municipal smart city planners",
            "Emergency medical delivery fleets",
            "Civil aviation regulatory bodies"
        ],
        project_type="Hybrid",
        difficulty_level="Advanced",
        difficulty_reasoning="Requires integration of real-time robotics middlewares (ROS 2), distributed multi-agent RL, safety-critical aerospace constraints, and edge hardware compute limits.",
        requirements=ProjectRequirementsSchema(
            possible_datasets=["NASA Urban Air Mobility Simulation Dataset (candidate)", "OpenStreetMap 3D City Models", "Stanford Flight Trajectory Logs"],
            hardware_requirements=["Onboard Jetson Orin with tensor cores", "3D solid-state LiDAR", "Dual-band RTK GPS"],
            software_requirements=["Ubuntu 22.04 LTS (Real-Time Kernel)", "ROS 2 Humble", "MAVLink protocol stack"],
            external_dependencies=["National Airspace Weather Radar API", "FAA LAANC Airspace Authorization API"],
            technical_constraints=["Maximum 250W onboard compute power budget", "<50ms sensor-to-actuation loop latency"]
        ),
        assumptions=[
            "UAVs have reliable 5G or direct mesh communication across the operational boundary.",
            "Local municipal micro-weather data is accessible via edge meteorological stations."
        ],
        risks=ProjectRisksSchema(
            technical_challenges=["Sim-to-real transfer gap in gusty micro-turbulent wind environments.", "GPS spoofing and signal multipath reflection in urban canyons."],
            implementation_risks=["FAA Part 107 regulatory compliance waivers required for Beyond Visual Line of Sight (BVLOS)."]
        )
    )

def run_phase3_tests():
    print("================================================================")
    print(">>> AI ProjectDNA - Phase 3 AI Idea Analyzer Test Suite <<<")
    print("================================================================")

    Base.metadata.create_all(bind=engine)
    apply_safe_schema_migrations()
    db = SessionLocal()

    # Setup User A
    ts = int(time.time())
    user_a = UserService.create_user(db, UserRegister(
        full_name="Dr. Hedy Lamarr",
        email=f"hedy_{ts}@projectdna.io",
        password="Password12345!"
    ))

    # Setup User B
    user_b = UserService.create_user(db, UserRegister(
        full_name="Dr. Claude Shannon",
        email=f"shannon_{ts}@projectdna.io",
        password="Password12345!"
    ))

    # Setup Project for User A
    project_a = ProjectService.create_project(
        db=db,
        project_in=ProjectCreate(
            title="AeroSwarm: Urban Drone Fleet Orchestrator",
            description="Autonomous multi-UAV routing and collision avoidance utilizing distributed reinforcement learning and dynamic 3D geofencing.",
            domain="Robotics & Autonomous Systems",
            technologies=["Python", "C++", "ROS 2", "PyTorch"],
            objectives="Coordinate autonomous air delivery corridors with sub-50ms collision avoidance."
        ),
        user_id=user_a.id
    )

    # 1. Successful Gemini Analysis (Mocked AI Service Class)
    print("\n[TEST 1] Successful Gemini Analysis:")
    mock_ai_service = MagicMock()
    sample_schema = get_sample_analysis_schema()
    mock_ai_service.analyze_project_idea.return_value = sample_schema

    analysis_res_1 = ProjectAnalysisService.analyze_project(
        db=db,
        project=project_a,
        user=user_a,
        ai_service_cls=mock_ai_service
    )
    print(f"  [OK] Analysis generated: Version {analysis_res_1.version} (ID: {analysis_res_1.id})")
    assert analysis_res_1.version == 1
    assert analysis_res_1.primary_domain == "Robotics & Autonomous Systems"
    assert len(analysis_res_1.keywords) >= 10
    assert len(analysis_res_1.objectives) >= 4
    assert project_a.status == "analysis_completed"

    # 2. Invalid Project ID (404)
    print("\n[TEST 2] Invalid Project ID Handling (404):")
    try:
        trigger_project_analysis(project_id="non-existent-proj-uuid", current_user=user_a, db=db)
        assert False, "Should have raised 404"
    except HTTPException as e:
        print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
        assert e.status_code == 404

    # 3. Unauthorized Project Analysis (403 for User B on User A's project)
    print("\n[TEST 3] Cross-User Unauthorized Project Analysis (403):")
    try:
        trigger_project_analysis(project_id=project_a.id, current_user=user_b, db=db)
        assert False, "Should have raised 403"
    except HTTPException as e:
        print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
        assert e.status_code == 403

    # 4. Missing API Key Handling (503)
    print("\n[TEST 4] Missing API Key Handling (503):")
    with patch.object(settings, "GEMINI_API_KEY", ""):
        try:
            AIService.get_client()
            assert False, "Should have raised 503 for missing API key"
        except HTTPException as e:
            print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
            assert e.status_code == 503

    # 5. Gemini API Failure Handling (502)
    print("\n[TEST 5] Gemini API Error Handling (502 / No Fabrication):")
    mock_failing_client = MagicMock()
    mock_failing_client.models.generate_content.side_effect = Exception("Simulated Gemini connection timeout / service failure")
    with patch.object(AIService, "get_client", return_value=mock_failing_client):
        try:
            AIService.analyze_project_idea("Title", "Desc", "Domain", [])
            assert False, "Should have raised 502"
        except HTTPException as e:
            print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
            assert e.status_code == 502

    # 6. Invalid Model JSON Response (502)
    print("\n[TEST 6] Invalid Model Output Format Handling (502):")
    mock_invalid_json_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = '{"corrupted": "missing required fields"}'
    mock_invalid_json_client.models.generate_content.return_value = mock_resp
    with patch.object(AIService, "get_client", return_value=mock_invalid_json_client):
        try:
            AIService.analyze_project_idea("Title", "Desc", "Domain", [])
            assert False, "Should have raised 502 for schema mismatch"
        except HTTPException as e:
            print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
            assert e.status_code == 502

    # 7. Database Persistence Verification
    print("\n[TEST 7] Database Persistence Verification:")
    persisted = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_res_1.id).first()
    print(f"  [OK] Persisted record found in 'project_analyses': ID={persisted.id}, Status={persisted.analysis_status}")
    assert persisted is not None
    assert persisted.project_id == project_a.id
    assert persisted.user_id == user_a.id

    # 8. Retrieving Analysis via API
    print("\n[TEST 8] Retrieve Latest Analysis Route (GET /api/projects/{id}/analysis):")
    fetched_analysis = get_project_analysis(project_id=project_a.id, version=None, current_user=user_a, db=db)
    print(f"  [OK] Retrieved analysis summary: '{fetched_analysis.project_summary[:50]}...'")
    assert fetched_analysis.id == analysis_res_1.id

    # 9. Multiple Analysis Versions Support
    print("\n[TEST 9] Multiple Analysis Versions Support:")
    mock_ai_service.analyze_project_idea.return_value = sample_schema
    analysis_res_2 = ProjectAnalysisService.analyze_project(
        db=db,
        project=project_a,
        user=user_a,
        ai_service_cls=mock_ai_service
    )
    print(f"  [OK] Created Version {analysis_res_2.version} (ID: {analysis_res_2.id})")
    assert analysis_res_2.version == 2
    
    # Verify history returns both versions
    history = get_project_analysis_history(project_id=project_a.id, current_user=user_a, db=db)
    print(f"  [OK] Total versions in history: {history.total_versions}")
    assert history.total_versions == 2
    assert history.analyses[0].version == 2  # Latest first
    assert history.analyses[1].version == 1

    # 10. User-Specific Analysis Access Isolation
    print("\n[TEST 10] User-Specific Analysis Access Isolation:")
    # User B cannot get User A's project analysis
    try:
        get_project_analysis(project_id=project_a.id, version=None, current_user=user_b, db=db)
        assert False, "User B should be blocked with 403"
    except HTTPException as e:
        print(f"  [OK] Caught expected HTTPException for User B: Status {e.status_code} - {e.detail}")
        assert e.status_code == 403

    # User B cannot get User A's analysis record by ID
    try:
        get_analysis_by_id(analysis_id=analysis_res_1.id, current_user=user_b, db=db)
        assert False, "User B should not access User A's analysis by ID"
    except HTTPException as e:
        print(f"  [OK] Caught expected HTTPException: Status {e.status_code} - {e.detail}")
        assert e.status_code == 404

    # Dashboard analytics reflects real metrics
    dashboard_stats = get_dashboard_stats(current_user=user_a, db=db)
    print(f"  [OK] User A Dashboard Analytics: Total Projects={dashboard_stats.total_projects}, Ideas Analyzed={dashboard_stats.ideas_analyzed}, Completed Runs={dashboard_stats.completed_analyses}")
    assert dashboard_stats.ideas_analyzed >= 1

    db.close()
    print("\n================================================================")
    print(">>> ALL 10 PHASE 3 AI IDEA ANALYZER TESTS PASSED 100%! <<<")
    print("================================================================")

if __name__ == "__main__":
    run_phase3_tests()

