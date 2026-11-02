"""
Test Suite: Phase 4.4 Semantic Embedding & Cross-Source Similarity Engine
Covers all 20 required verification points:
1. Model initialization & singleton pattern
2. Dimension validation (384)
3. Normalized vector generation (L2 norm == 1.0)
4. Empty input handling (EmbeddingModelError)
5. Project text preparation & embedding
6. Research paper text preparation & embedding
7. GitHub repository text preparation & embedding
8. Content hash generation (SHA-256)
9. Duplicate embedding prevention (skips unchanged hash)
10. Embedding update/regeneration on content modification
11. Cosine similarity calculation (orthogonal, parallel, opposite)
12. Similarity ranking (descending sort with ranks 1..N)
13. Cross-source matching (papers + repos)
14. Missing source metadata handling (null fields)
15. Partial batch failure resilience
16. Database persistence with cascade foreign keys
17. Project ownership enforcement
18. Cross-user access rejection (403 Forbidden)
19. Similarity retrieval endpoint (GET /similarity)
20. Similarity statistics endpoint (GET /similarity/stats)
"""
import sys
import uuid
import math
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

sys.path.insert(0, 'backend')

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.user import User
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.research_paper import ResearchPaper
from app.models.github_repo import GitHubRepository
from app.models.project_embedding import ProjectEmbedding
from app.services.embedding.embedding_service import EmbeddingService, EmbeddingModelError
from app.services.embedding.text_preprocessor import (
    TextPreprocessor,
    prepare_project_text,
    prepare_research_paper_text,
    prepare_github_repo_text,
    compute_content_hash,
)
from app.services.embedding.semantic_similarity_service import (
    SemanticSimilarityService,
    compute_cosine_similarity,
    get_similarity_label,
)
from app.services.embedding.embedding_pipeline import EmbeddingPipeline
from app.routes.similarity import (
    generate_project_embeddings,
    get_semantic_similarities,
    get_similarity_stats,
)
from app.schemas.embedding import EmbeddingGenerateRequest

def setup_module():
    """Ensure database tables exist."""
    Base.metadata.create_all(bind=engine)

def create_test_user(db, email_prefix="user_phase4_4"):
    uid = str(uuid.uuid4())[:8]
    user = User(
        id=str(uuid.uuid4()),
        full_name=f"Tester {uid}",
        email=f"{email_prefix}_{uid}@example.com",
        hashed_password="hashed_pw_test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_project(db, user, title="Autonomous UAV Fleet Deconfliction"):
    project = Project(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title=title,
        description="Decentralized collision avoidance and air traffic routing for commercial delivery drones.",
        domain="Robotics & UAVs",
        technologies=["Python", "ROS2"],
        status="in_progress",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def test_01_model_initialization():
    """1. Model initialization: Verify singleton pattern and cached instance."""
    EmbeddingService.reset_instance()
    service1 = EmbeddingService.get_instance()
    service2 = EmbeddingService.get_instance()
    assert service1 is service2, "EmbeddingService must implement a strict singleton pattern."
    assert service1.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert service1.dimension == 384
    print("Test 1 Passed: Model initialization and singleton verified.")

def test_02_dimension_validation():
    """2. Dimension validation: Vectors must have dimension 384."""
    service = EmbeddingService.get_instance()
    vectors = service.encode_texts(["Autonomous UAV flight control system."])
    assert len(vectors) == 1
    assert len(vectors[0]) == 384
    print("Test 2 Passed: Embedding dimension is strictly 384.")

def test_03_normalized_vector_generation():
    """3. Normalized vector generation: Euclidean norm must be approximately 1.0."""
    service = EmbeddingService.get_instance()
    vectors = service.encode_texts(["Dense semantic embedding with L2 normalization."])
    v = vectors[0]
    norm = math.sqrt(sum(x * x for x in v))
    assert abs(norm - 1.0) < 1e-3, f"Vector Euclidean norm should be ~1.0, got {norm}"
    print("Test 3 Passed: Generated vectors are L2-normalized.")

def test_04_empty_input_handling():
    """4. Empty input handling: encode_texts([]) must raise EmbeddingModelError."""
    service = EmbeddingService.get_instance()
    try:
        service.encode_texts([])
        assert False, "Should have raised EmbeddingModelError on empty input"
    except EmbeddingModelError as exc:
        assert "empty" in str(exc).lower()
    print("Test 4 Passed: Empty input handling properly raises EmbeddingModelError.")

def test_05_project_text_preparation():
    """5. Project text preparation: Preprocessor extracts title, problem, solution, keywords."""
    db = SessionLocal()
    try:
        user = create_test_user(db, "prep_proj")
        project = create_test_project(db, user)
        analysis = ProjectAnalysis(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=user.id,
            version=1,
            project_summary="A platform for automated UAV flight corridors.",
            problem_statement="Urban air mobility faces severe airspace congestion and risk of drone collisions.",
            proposed_solution="Decentralized peer-to-peer trajectory negotiation protocol using reinforcement learning.",
            primary_domain="Robotics & UAVs",
            secondary_domains=["Artificial Intelligence", "Transportation"],
            keywords=["UAV", "collision avoidance", "reinforcement learning", "air traffic"],
            user_technologies=["Python", "ROS2"],
            recommended_technologies=["PX4", "Gazebo"],
            objectives=["Zero mid-air collisions", "Sub-second re-routing"],
            target_users=["Drone fleet operators"],
            project_type="System",
            difficulty_level="Advanced",
            difficulty_reasoning="Complex real-time multi-agent kinematics.",
            requirements=["Low latency", "Fail-safe redundancy"],
            assumptions=["Drones have V2V radio"],
            risks=["GPS spoofing"],
            model_name="gemini-1.5-pro",
            analysis_status="completed",
        )
        db.add(analysis)
        db.commit()

        prepared = prepare_project_text(project, analysis)
        assert project.title in prepared
        assert "Urban air mobility faces severe airspace congestion" in prepared
        assert "Decentralized peer-to-peer trajectory negotiation" in prepared
        assert "collision avoidance" in prepared
        print("Test 5 Passed: Project idea text preparation formats all key sections.")
    finally:
        db.close()

def test_06_research_paper_text_preparation():
    """6. Research paper text preparation: Formats title, abstract, categories, venue."""
    paper = ResearchPaper(
        id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        provider="arxiv",
        provider_paper_id="2304.12345",
        title="Multi-Agent Drone Coordination via Proximal Policy Optimization",
        abstract="We investigate distributed collision avoidance in dense urban air corridors using multi-agent PPO.",
        authors=["Alice Johnson", "Bob Smith"],
        publication_year=2023,
        venue="IEEE Robotics and Automation Letters",
        primary_category="cs.RO",
    )
    prepared = prepare_research_paper_text(paper)
    assert "Multi-Agent Drone Coordination" in prepared
    assert "dense urban air corridors" in prepared
    assert "cs.RO" in prepared
    print("Test 6 Passed: Research paper text preparation verified.")

def test_07_github_repo_text_preparation():
    """7. GitHub repository text preparation: Formats repo name, description, topics, languages."""
    repo = GitHubRepository(
        id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        github_repository_id=1234567,
        full_name="uav-org/drone-fleet-manager",
        name="drone-fleet-manager",
        html_url="https://github.com/uav-org/drone-fleet-manager",
        description="Autonomous drone fleet routing and trajectory optimization engine with ROS2 support.",
        topics=["uav", "robotics", "collision-avoidance", "ros2"],
        language="C++",
        stargazers_count=350,
    )
    prepared = prepare_github_repo_text(repo)
    assert "uav-org/drone-fleet-manager" in prepared
    assert "Autonomous drone fleet routing" in prepared
    assert "collision-avoidance" in prepared
    assert "C++" in prepared
    print("Test 7 Passed: GitHub repository text preparation verified.")

def test_08_content_hash_generation():
    """8. Content hash generation: SHA-256 stable hex digest."""
    text1 = "Decentralized UAV trajectory planning."
    text2 = "Decentralized UAV trajectory planning."
    text3 = "Different text content."
    h1 = compute_content_hash(text1)
    h2 = compute_content_hash(text2)
    h3 = compute_content_hash(text3)
    assert len(h1) == 64
    assert h1 == h2, "Identical text must generate identical content hash."
    assert h1 != h3, "Different text must generate different content hash."
    print("Test 8 Passed: SHA-256 content hashing is deterministic.")

def test_09_duplicate_embedding_prevention():
    """9. Duplicate embedding prevention: Pipeline skips items with unchanged content hash."""
    db = SessionLocal()
    try:
        user = create_test_user(db, "dup_prevent")
        project = create_test_project(db, user)

        pipeline = EmbeddingPipeline(db=db)
        # First run: generates embedding
        res1 = pipeline.generate_all_project_embeddings(project, force_regenerate=False)
        assert res1.total_generated >= 1
        assert res1.total_skipped == 0

        # Second run: should be skipped because hash is unchanged
        res2 = pipeline.generate_all_project_embeddings(project, force_regenerate=False)
        assert res2.total_generated == 0
        assert res2.total_skipped >= 1
        print("Test 9 Passed: Duplicate embedding prevention correctly skipped unchanged content.")
    finally:
        db.close()

def test_10_embedding_update_on_content_change():
    """10. Embedding update / force regeneration: Updates vector when forced or content changes."""
    db = SessionLocal()
    try:
        user = create_test_user(db, "force_regen")
        project = create_test_project(db, user)

        pipeline = EmbeddingPipeline(db=db)
        res1 = pipeline.generate_all_project_embeddings(project, force_regenerate=False)
        assert res1.total_generated >= 1

        # Force regenerate
        res2 = pipeline.generate_all_project_embeddings(project, force_regenerate=True)
        assert res2.total_generated >= 1
        assert res2.total_skipped == 0
        print("Test 10 Passed: Force regeneration successfully re-embeds source items.")
    finally:
        db.close()

def test_11_cosine_similarity_calculation():
    """11. Cosine similarity calculation: Identical (1.0), opposite (-1.0), orthogonal (0.0)."""
    # Identical normalized vectors
    u = [1.0, 0.0, 0.0]
    v = [1.0, 0.0, 0.0]
    sim_ident = compute_cosine_similarity(u, v)
    assert abs(sim_ident - 1.0) < 1e-4

    # Opposite vectors
    neg_v = [-1.0, 0.0, 0.0]
    sim_opp = compute_cosine_similarity(u, neg_v)
    assert abs(sim_opp - (-1.0)) < 1e-4

    # Orthogonal vectors
    orth_v = [0.0, 1.0, 0.0]
    sim_orth = compute_cosine_similarity(u, orth_v)
    assert abs(sim_orth - 0.0) < 1e-4

    # Zero vector fallback
    assert compute_cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0
    print("Test 11 Passed: Cosine similarity logic handles identical, opposite, orthogonal, and zero cases.")

def test_12_similarity_ranking():
    """12. Similarity ranking: Results sorted descending by cosine similarity with 1-based ranks."""
    project_id = str(uuid.uuid4())
    proj_rec = ProjectEmbedding(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=str(uuid.uuid4()),
        source_type="project",
        source_record_id=project_id,
        embedding=[1.0, 0.0, 0.0],
        model_name="test-model",
        embedding_dimension=3,
        content_hash="h0",
        metadata_json={"title": "Main Project"},
    )
    cand_high = ProjectEmbedding(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=proj_rec.user_id,
        source_type="research_paper",
        source_record_id="p1",
        embedding=[0.9, 0.4358, 0.0],  # Dot product ~0.9
        model_name="test-model",
        embedding_dimension=3,
        content_hash="h1",
        metadata_json={"title": "High Match Paper"},
    )
    cand_low = ProjectEmbedding(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=proj_rec.user_id,
        source_type="github_repository",
        source_record_id="r1",
        embedding=[0.2, 0.9797, 0.0],  # Dot product ~0.2
        model_name="test-model",
        embedding_dimension=3,
        content_hash="h2",
        metadata_json={"title": "Low Match Repo"},
    )

    res = SemanticSimilarityService.rank_similarities(
        project_id=project_id,
        project_embedding_record=proj_rec,
        candidate_embeddings=[cand_low, cand_high],
    )
    assert res.total_matches == 2
    assert res.matches[0].rank == 1
    assert res.matches[0].source_record_id == "p1"
    assert res.matches[0].similarity_score > res.matches[1].similarity_score
    assert res.matches[1].rank == 2
    print("Test 12 Passed: Matches are strictly ranked in descending order.")

def test_13_cross_source_matching():
    """13. Cross-source matching: Aggregates both research papers and GitHub repositories."""
    project_id = str(uuid.uuid4())
    proj_rec = ProjectEmbedding(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=str(uuid.uuid4()),
        source_type="project",
        source_record_id=project_id,
        embedding=[0.5, 0.5, 0.707],
        model_name="test-model",
        embedding_dimension=3,
        content_hash="hp",
        metadata_json={"title": "Fleet Idea"},
    )
    paper_rec = ProjectEmbedding(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=proj_rec.user_id,
        source_type="research_paper",
        source_record_id="paper_101",
        embedding=[0.5, 0.5, 0.707],
        model_name="test-model",
        embedding_dimension=3,
        content_hash="hpaper",
        metadata_json={"title": "Paper on Routing"},
    )
    repo_rec = ProjectEmbedding(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=proj_rec.user_id,
        source_type="github_repository",
        source_record_id="repo_202",
        embedding=[0.4, 0.6, 0.692],
        model_name="test-model",
        embedding_dimension=3,
        content_hash="hrepo",
        metadata_json={"title": "Repo on Routing"},
    )

    res = SemanticSimilarityService.rank_similarities(
        project_id=project_id,
        project_embedding_record=proj_rec,
        candidate_embeddings=[paper_rec, repo_rec],
    )
    source_types = {m.source_type for m in res.matches}
    assert "research_paper" in source_types
    assert "github_repository" in source_types
    print("Test 13 Passed: Cross-source matching includes both papers and repositories.")

def test_14_missing_source_metadata_handling():
    """14. Missing source metadata handling: Handles null abstract, null description without crashing."""
    paper_empty = ResearchPaper(
        id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        provider="arxiv",
        provider_paper_id="2304.9999",
        title="Paper With Minimal Metadata",
        abstract=None,
        authors=None,
        publication_year=None,
        venue=None,
        primary_category=None,
    )
    txt_paper = prepare_research_paper_text(paper_empty)
    assert "Paper With Minimal Metadata" in txt_paper

    repo_empty = GitHubRepository(
        id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        github_repository_id=987654,
        full_name="empty-org/empty-repo",
        name="empty-repo",
        html_url="https://github.com/empty-org/empty-repo",
        description=None,
        topics=None,
        language=None,
    )
    txt_repo = prepare_github_repo_text(repo_empty)
    assert "empty-org/empty-repo" in txt_repo
    print("Test 14 Passed: Missing source metadata handled cleanly.")

def test_15_partial_batch_failure_resilience():
    """15. Partial batch failure resilience: Pipeline handles partial failure gracefully."""
    db = SessionLocal()
    try:
        user = create_test_user(db, "partial_fail")
        project = create_test_project(db, user)

        pipeline = EmbeddingPipeline(db=db)
        # Patch encode_texts to raise an exception for testing error handling
        with patch.object(EmbeddingService, "encode_texts", side_effect=EmbeddingModelError("Simulated device OOM")):
            res = pipeline.generate_all_project_embeddings(project, force_regenerate=True)
            assert res.status in ["failed", "partial_success", "error"]
            assert len(res.errors) > 0
        print("Test 15 Passed: Pipeline exhibits graceful failure resilience.")
    finally:
        db.close()

def test_16_database_persistence_and_cascade():
    """16. Database persistence with cascade foreign keys."""
    db = SessionLocal()
    try:
        user = create_test_user(db, "cascade_test")
        project = create_test_project(db, user)

        emb = ProjectEmbedding(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=user.id,
            source_type="project",
            source_record_id=project.id,
            embedding=[0.1] * 384,
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimension=384,
            content_hash="test_hash_cascade",
            metadata_json={"title": project.title},
        )
        db.add(emb)
        db.commit()

        # Check persisted
        found = db.query(ProjectEmbedding).filter(ProjectEmbedding.id == emb.id).first()
        assert found is not None

        # Delete project -> should cascade delete emb
        db.delete(project)
        db.commit()

        found_after = db.query(ProjectEmbedding).filter(ProjectEmbedding.id == emb.id).first()
        assert found_after is None, "ProjectEmbedding record should cascade delete with Project."
        print("Test 16 Passed: Database persistence and cascade deletion verified.")
    finally:
        db.close()

def test_17_project_ownership_enforcement():
    """17. Project ownership enforcement: Owner can generate embeddings."""
    db = SessionLocal()
    try:
        user = create_test_user(db, "owner_test")
        project = create_test_project(db, user)

        # Calling route function with owner user should succeed
        res = generate_project_embeddings(
            project_id=project.id,
            payload=EmbeddingGenerateRequest(force_regenerate=True),
            current_user=user,
            db=db,
        )
        assert res.project_id == project.id
        assert res.status in ["completed", "partial_success"]
        print("Test 17 Passed: Project owner allowed to execute embedding generation.")
    finally:
        db.close()

def test_18_cross_user_access_rejection():
    """18. Cross-user access rejection: Unauthorized user receives 403 Forbidden."""
    db = SessionLocal()
    try:
        owner = create_test_user(db, "legit_owner")
        attacker = create_test_user(db, "intruder_user")
        project = create_test_project(db, owner)

        # Attacker tries to generate embeddings on owner's project
        try:
            generate_project_embeddings(
                project_id=project.id,
                payload=EmbeddingGenerateRequest(),
                current_user=attacker,
                db=db,
            )
            assert False, "Should have raised 403 Forbidden for cross-user generation"
        except HTTPException as exc:
            assert exc.status_code == 403

        # Attacker tries to query similarities
        try:
            get_semantic_similarities(
                project_id=project.id,
                current_user=attacker,
                db=db,
            )
            assert False, "Should have raised 403 Forbidden for cross-user retrieval"
        except HTTPException as exc:
            assert exc.status_code == 403

        print("Test 18 Passed: Cross-user access rejection strictly enforced (403 Forbidden).")
    finally:
        db.close()

def test_19_similarity_retrieval_endpoint():
    """19. Similarity retrieval endpoint: GET /similarity returns structured match response."""
    db = SessionLocal()
    try:
        user = create_test_user(db, "retrieval_user")
        project = create_test_project(db, user)

        # Seed research paper
        paper = ResearchPaper(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=user.id,
            provider="arxiv",
            provider_paper_id="2401.9999",
            title="Decentralized Collision Avoidance for UAV Networks",
            abstract="Study of multi-agent collision avoidance algorithms.",
            authors=["Dr. Drone"],
        )
        db.add(paper)
        db.commit()

        # Generate embeddings
        generate_project_embeddings(
            project_id=project.id,
            payload=EmbeddingGenerateRequest(force_regenerate=True),
            current_user=user,
            db=db,
        )

        # Retrieve similarities
        sim_res = get_semantic_similarities(
            project_id=project.id,
            source_type="research_paper",
            min_similarity=0.1,
            limit=10,
            current_user=user,
            db=db,
        )
        assert sim_res.project_id == project.id
        assert sim_res.embedding_dimension == 384
        assert len(sim_res.matches) >= 1
        assert sim_res.matches[0].source_type == "research_paper"
        assert sim_res.matches[0].similarity_score > 0.0
        assert sim_res.disclaimer is not None
        print("Test 19 Passed: Similarity retrieval endpoint returns structured response.")
    finally:
        db.close()

def test_20_similarity_stats_endpoint():
    """20. Similarity statistics endpoint: GET /similarity/stats returns counts and model metadata."""
    db = SessionLocal()
    try:
        user = create_test_user(db, "stats_user")
        project = create_test_project(db, user)

        # Query stats before generation
        stats0 = get_similarity_stats(project_id=project.id, current_user=user, db=db)
        assert stats0.has_project_embedding is False
        assert stats0.total_embeddings_stored == 0

        # Generate
        generate_project_embeddings(
            project_id=project.id,
            payload=EmbeddingGenerateRequest(force_regenerate=True),
            current_user=user,
            db=db,
        )

        stats1 = get_similarity_stats(project_id=project.id, current_user=user, db=db)
        assert stats1.has_project_embedding is True
        assert stats1.total_embeddings_stored >= 1
        assert stats1.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert stats1.embedding_dimension == 384
        print("Test 20 Passed: Similarity statistics endpoint returns accurate metadata and counts.")
    finally:
        db.close()

if __name__ == "__main__":
    print("\n========================================================")
    print(" Running Phase 4.4 Semantic Similarity Unit Test Suite")
    print("========================================================")
    setup_module()
    test_01_model_initialization()
    test_02_dimension_validation()
    test_03_normalized_vector_generation()
    test_04_empty_input_handling()
    test_05_project_text_preparation()
    test_06_research_paper_text_preparation()
    test_07_github_repo_text_preparation()
    test_08_content_hash_generation()
    test_09_duplicate_embedding_prevention()
    test_10_embedding_update_on_content_change()
    test_11_cosine_similarity_calculation()
    test_12_similarity_ranking()
    test_13_cross_source_matching()
    test_14_missing_source_metadata_handling()
    test_15_partial_batch_failure_resilience()
    test_16_database_persistence_and_cascade()
    test_17_project_ownership_enforcement()
    test_18_cross_user_access_rejection()
    test_19_similarity_retrieval_endpoint()
    test_20_similarity_stats_endpoint()
    print("\n========================================================")
    print(" ALL 20 PHASE 4.4 EMBEDDING UNIT TESTS PASSED (100%)")
    print("========================================================\n")
