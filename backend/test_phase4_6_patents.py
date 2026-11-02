"""
Unit & Integration Tests for Phase 4.6: Patent & Prior-Art Discovery Engine
AI ProjectDNA - Intelligent Innovation & Project Validation Platform
"""
import unittest
import uuid
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.user import User
from app.models.project import Project
from app.models.analysis import ProjectAnalysis
from app.models.patent import Patent
from app.models.project_embedding import ProjectEmbedding
from app.schemas.patent import (
    PatentSchema,
    PatentSearchRequest,
    PatentSearchResponse,
    PatentListResponse,
    PatentStatsResponse,
    PriorArtAnalysisItem,
    PatentAnalysisResponse,
    LEGAL_DISCLAIMER,
)
from app.services.patents.base import (
    normalize_publication_number,
    extract_jurisdiction,
    build_google_patents_url,
    clean_text,
    clean_list,
    PatentRateLimitError,
    PatentTimeoutError,
    PatentAPIError,
)
from app.services.patents.patent_query_generator import (
    PatentQueryGenerator,
    clean_term,
    DOMAIN_CPC_MAP,
)
from app.services.patents.uspto_service import UsptoPatentService
from app.services.patents.epo_service import EpoPatentService
from app.services.patents.patent_discovery_service import PatentDiscoveryService
from app.services.patents.patent_embedding_service import PatentEmbeddingService
from app.services.patents.patent_analysis_service import PatentAnalysisService
from app.services.embedding.text_preprocessor import TextPreprocessor
from app.services.rag.evidence_retrieval_service import EvidenceRetrievalService
from app.services.rag.context_builder import build_rag_context
from app.services.rag.citation_service import CitationService
from app.services.rag.heuristic_synthesizer import synthesize_deterministic_report
import httpx


class TestPhase46PatentEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

        # Seed primary user
        self.user_id = str(uuid.uuid4())
        self.user = User(
            id=self.user_id,
            email=f"patent_user_{self.user_id[:8]}@example.com",
            full_name="Patent Engineer",
            hashed_password="hashed_pw_for_testing",
        )
        self.db.add(self.user)

        # Seed other user for auth isolation checks
        self.other_user_id = str(uuid.uuid4())
        self.other_user = User(
            id=self.other_user_id,
            email=f"other_{self.other_user_id[:8]}@example.com",
            full_name="Other User",
            hashed_password="hashed_pw_for_testing",
        )
        self.db.add(self.other_user)

        # Seed project
        self.project_id = str(uuid.uuid4())
        self.project = Project(
            id=self.project_id,
            user_id=self.user_id,
            title="BioGraphNet: Molecular Graph Neural Network",
            description="Deep learning system applying equivariant graph networks to macromolecular interaction modeling.",
            domain="artificial intelligence",
            technologies=["PyTorch", "PyTorch Geometric", "Docker"],
        )
        self.db.add(self.project)

        # Seed analysis
        self.analysis = ProjectAnalysis(
            id=str(uuid.uuid4()),
            project_id=self.project_id,
            user_id=self.user_id,
            version=1,
            project_summary="Equivariant neural network model predicting protein-ligand binding affinity.",
            problem_statement="High false discovery rates and conformational inaccuracy in rigid docking.",
            proposed_solution="3D SE(3)-equivariant continuous convolution layers predicting kinetic binding parameters.",
            primary_domain="artificial intelligence",
            secondary_domains=["biomedical", "machine learning"],
            keywords=["graph neural network", "equivariant", "binding affinity", "protein docking"],
            user_technologies=["PyTorch", "PyG"],
            recommended_technologies={"framework": ["PyTorch Geometric", "FastAPI"]},
            objectives=["Achieve state-of-the-art affinity ranking", "Run sub-second inference"],
            target_users=["Computational chemists", "Structural biologists"],
            project_type="Machine Learning System",
            difficulty_level="Advanced",
            difficulty_reasoning="Requires advanced mathematical group theory and SE(3) representations.",
            requirements={"hardware": ["GPU cluster"]},
            assumptions=["High quality PDB crystal structures available"],
            risks={"latency": ["Complex equivariance checks might degrade FPS"]},
            model_name="test-model",
            analysis_status="completed",
        )
        self.db.add(self.analysis)
        self.db.commit()

    def tearDown(self):
        self.db.query(Patent).delete()
        self.db.query(ProjectEmbedding).delete()
        self.db.query(ProjectAnalysis).delete()
        self.db.query(Project).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    # =========================================================================
    # 1. Normalization & Utility Helper Tests
    # =========================================================================

    def test_normalize_publication_number(self):
        """Tests that varied publication number formats are cleanly standardized."""
        self.assertEqual(normalize_publication_number("US-11,234,567-B2"), "US11234567B2")
        self.assertEqual(normalize_publication_number("  us 10987654 a1  "), "US10987654A1")
        self.assertEqual(normalize_publication_number("EP-3456789/A1"), "EP3456789A1")
        self.assertEqual(normalize_publication_number("WO.2023/123456.A1"), "WO2023123456A1")
        self.assertEqual(normalize_publication_number(""), "")
        self.assertEqual(normalize_publication_number(None), "")

    def test_extract_jurisdiction(self):
        """Tests extracting two-letter country/jurisdiction prefix."""
        self.assertEqual(extract_jurisdiction("US11234567B2"), "US")
        self.assertEqual(extract_jurisdiction("EP3456789A1"), "EP")
        self.assertEqual(extract_jurisdiction("WO2023012345"), "WO")
        self.assertEqual(extract_jurisdiction("CN11223344"), "CN")
        self.assertEqual(extract_jurisdiction("11234567"), "US")  # default fallback
        self.assertEqual(extract_jurisdiction(""), "UNKNOWN")

    def test_build_google_patents_url(self):
        """Tests building valid Google Patents URL without scraping."""
        url = build_google_patents_url("US-11,234,567-B2")
        self.assertEqual(url, "https://patents.google.com/patent/US11234567B2/en")
        self.assertIsNone(build_google_patents_url(None))
        self.assertIsNone(build_google_patents_url(""))

    def test_clean_text_and_clean_list(self):
        """Tests whitespace cleaning and multi-type list parsing."""
        raw = "   Apparatus   and \n system for   distributed  inference.  "
        self.assertEqual(clean_text(raw), "Apparatus and system for distributed inference.")
        self.assertIsNone(clean_text(None))

        raw_list = ["Alice Smith", {"name": "Bob Jones"}, "Alice Smith", " Charlie Brown , Dave Miller "]
        cleaned = clean_list(raw_list)
        self.assertIn("Alice Smith", cleaned)
        self.assertIn("Bob Jones", cleaned)
        self.assertIn("Charlie Brown", cleaned)
        self.assertIn("Dave Miller", cleaned)
        self.assertEqual(len(cleaned), 4)

    # =========================================================================
    # 2. Query Generator Tests
    # =========================================================================

    def test_query_generator_domain_cpc_mapping(self):
        """Tests domain and keyword mapping to Cooperative Patent Classification (CPC) codes."""
        cpcs = PatentQueryGenerator.infer_cpc_classifications(
            primary_domain="artificial intelligence",
            secondary_domains=["biomedical"],
            keywords=["deep learning", "neural network"]
        )
        self.assertTrue(any(c in cpcs for c in ["G06N", "G06F", "G16H", "A61B"]))

    def test_query_generator_stopword_removal(self):
        """Tests that common stop words and generic terms are filtered out."""
        cleaned = clean_term("novel")
        self.assertEqual(cleaned, "novel")

        analysis_dict = {
            "primary_domain": "cybersecurity",
            "keywords": ["novel", "system", "intrusion detection", "encryption"],
            "secondary_domains": [],
            "user_technologies": []
        }
        res = PatentQueryGenerator.generate_queries(analysis_dict)
        self.assertNotIn("novel", res["primary_keywords"])
        self.assertNotIn("system", res["primary_keywords"])
        self.assertTrue(any("intrusion" in k for k in res["primary_keywords"]))

    def test_query_generator_query_override(self):
        """Tests handling when user supplies a custom keyword query override."""
        res = PatentQueryGenerator.generate_queries({}, query_override="quantum annealing optimization")
        self.assertEqual(res["search_queries"], ["quantum annealing optimization"])
        self.assertIn("quantum", res["primary_keywords"])
        self.assertIn("annealing", res["primary_keywords"])

    # =========================================================================
    # 3. USPTO Provider Tests
    # =========================================================================

    @patch("httpx.AsyncClient.get")
    def test_uspto_provider_response_parsing(self, mock_get):
        """Tests that PatentsView mock JSON response is correctly parsed into PatentSchema objects."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "patents": [
                {
                    "patent_id": "11234567",
                    "patent_number": "11234567",
                    "patent_title": "Graph neural network for molecular affinity prediction",
                    "patent_abstract": "A neural network processing pipeline for 3D molecular conformations.",
                    "patent_date": "2023-05-16",
                    "app_date": "2021-02-10",
                    "inventors": [
                        {"inventor_first_name": "Alan", "inventor_last_name": "Turing"}
                    ],
                    "assignees": [
                        {"assignee_organization": "DeepBio Labs Inc."}
                    ],
                    "cpcs": [
                        {"cpc_subgroup_id": "G06N3/08"}
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        service = UsptoPatentService()
        import asyncio
        results = asyncio.run(service.search(keywords=["molecular", "graph", "neural"]))

        self.assertEqual(len(results), 1)
        pat = results[0]
        self.assertEqual(pat.provider, "uspto")
        self.assertEqual(pat.publication_number, "US11234567")
        self.assertEqual(pat.title, "Graph neural network for molecular affinity prediction")
        self.assertEqual(pat.inventors, ["Alan Turing"])
        self.assertEqual(pat.assignees, ["DeepBio Labs Inc."])
        self.assertEqual(pat.cpc_classifications, ["G06N3/08"])
        self.assertEqual(pat.jurisdiction, "US")
        self.assertIn("https://patents.google.com/patent/US11234567/en", pat.source_url)

    @patch("httpx.AsyncClient.get")
    def test_uspto_provider_rate_limit_handling(self, mock_get):
        """Tests that HTTP 429 raises PatentRateLimitError."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        service = UsptoPatentService()
        import asyncio
        with self.assertRaises(PatentRateLimitError):
            asyncio.run(service.search(keywords=["neural", "network"]))

    @patch("httpx.AsyncClient.get")
    def test_uspto_provider_timeout_handling(self, mock_get):
        """Tests that httpx.TimeoutException raises PatentTimeoutError."""
        mock_get.side_effect = httpx.TimeoutException("Connection timed out")

        service = UsptoPatentService()
        import asyncio
        with self.assertRaises(PatentTimeoutError):
            asyncio.run(service.search(keywords=["neural", "network"]))

    # =========================================================================
    # 4. EPO Provider Tests
    # =========================================================================

    def test_epo_provider_missing_credentials_graceful(self):
        """Tests that when EPO consumer key/secret are missing, it returns empty without crashing."""
        service = EpoPatentService()
        service.consumer_key = ""
        service.consumer_secret = ""

        import asyncio
        results = asyncio.run(service.search(keywords=["molecular", "docking"]))
        self.assertEqual(results, [])

    @patch.object(EpoPatentService, "_get_auth_token", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.get")
    def test_epo_provider_response_parsing(self, mock_get, mock_auth):
        """Tests parsing of mock EPO OPS published-data response into PatentSchema."""
        mock_auth.return_value = "mock_bearer_token_123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ops:world-patent-data": {
                "ops:biblio-search": {
                    "ops:search-result": {
                        "ops:publication-reference": [
                            {
                                "document-id": {
                                    "country": {"$": "EP"},
                                    "doc-number": {"$": "3456789"},
                                    "kind": {"$": "A1"},
                                    "date": {"$": "20220315"}
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        service = EpoPatentService()
        service.consumer_key = "test_key"
        service.consumer_secret = "test_secret"

        import asyncio
        results = asyncio.run(service.search(keywords=["graph", "affinity"]))
        self.assertEqual(len(results), 1)
        pat = results[0]
        self.assertEqual(pat.provider, "epo")
        self.assertEqual(pat.publication_number, "EP3456789A1")
        self.assertEqual(pat.jurisdiction, "EP")
        self.assertIn("https://patents.google.com/patent/EP3456789A1/en", pat.source_url)

    # =========================================================================
    # 5. Model & Deduplication Tests
    # =========================================================================

    def test_patent_model_creation_and_to_dict(self):
        """Tests creating a Patent model and converting to dict."""
        pat = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="US9988776",
            publication_number="US9988776B2",
            title="Continuous Convolution Molecular Modeling",
            abstract="A spatial convolution algorithm for atomic coordinates.",
            claims=["1. A method for equivariant spatial convolution."],
            inventors=["Marie Curie"],
            assignees=["Sorbonne Tech"],
            jurisdiction="US",
            cpc_classifications=["G06N3/04", "G16B15/00"],
            source_url="https://patents.google.com/patent/US9988776B2/en"
        )
        self.db.add(pat)
        self.db.commit()

        d = pat.to_dict()
        self.assertEqual(d["publication_number"], "US9988776B2")
        self.assertEqual(d["provider"], "uspto")
        self.assertEqual(d["jurisdiction"], "US")
        self.assertEqual(len(d["claims"]), 1)
        self.assertEqual(d["inventors"], ["Marie Curie"])

    def test_deduplication_exact_and_formatted_variants(self):
        """Tests deduplicating incoming patent publications against DB records."""
        existing_pat = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="10111222",
            publication_number="US10111222B2",
            title="Existing Patent",
            jurisdiction="US"
        )
        self.db.add(existing_pat)
        self.db.commit()

        service = PatentDiscoveryService()
        incoming = [
            # Formatted variant of existing patent
            PatentSchema(
                provider="uspto",
                provider_patent_id="10111222",
                publication_number="US-10,111,222-B2",
                title="Existing Variant"
            ),
            # New patent
            PatentSchema(
                provider="uspto",
                provider_patent_id="10333444",
                publication_number="US-10,333,444-B1",
                title="Brand New Patent"
            ),
            # Duplicate of new patent in same batch
            PatentSchema(
                provider="epo",
                provider_patent_id="10333444",
                publication_number="US10333444B1",
                title="Brand New Patent Duplicate"
            ),
        ]

        unique_new, skipped = service.deduplicate_patents(incoming, [existing_pat])
        self.assertEqual(len(unique_new), 1)
        self.assertEqual(unique_new[0].publication_number, "US10333444B1")
        self.assertEqual(skipped, 2)

    # =========================================================================
    # 6. Text Preprocessor & Embedding Tests
    # =========================================================================

    def test_text_preprocessor_patent_formatting(self):
        """Tests that TextPreprocessor builds structured, character-capped patent representations."""
        pat = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="US12345",
            publication_number="US12345678B2",
            title="Neural Architecture for Molecular Structure Analysis",
            abstract="Discloses equivariant layers operating on coordinate geometries.",
            claims=["Claim 1: An equivariant neural apparatus."],
            assignees=["BioTech Corp"],
            cpc_classifications=["G06N", "G16B"],
            jurisdiction="US"
        )
        prep = TextPreprocessor.prepare_patent_text(pat)
        self.assertIn("Patent Publication: US12345678B2", prep["text"])
        self.assertIn("Assignees/Applicants: BioTech Corp", prep["text"])
        self.assertIn("CPC Classifications: G06N, G16B", prep["text"])
        self.assertIn("Abstract: Discloses equivariant layers", prep["text"])
        self.assertIn("content_hash", prep)
        self.assertEqual(len(prep["content_hash"]), 64)

    def test_patent_embedding_generation_and_cosine_similarity(self):
        """Tests generating embeddings for patents and calculating cosine similarity."""
        pat1 = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="P1",
            publication_number="US11111111",
            title="Equivariant Graph Neural Network for Macromolecular Modeling",
            abstract="3D equivariant convolutions for molecular graphs and binding affinities.",
            jurisdiction="US"
        )
        pat2 = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="P2",
            publication_number="US22222222",
            title="Automated Concrete Mixer Hydraulic Valve",
            abstract="A hydraulic valve system for cement rotation in construction equipment.",
            jurisdiction="US"
        )
        self.db.add_all([pat1, pat2])
        self.db.commit()

        service = PatentEmbeddingService(self.db)
        service.ensure_patent_embeddings(self.project_id, [pat1, pat2])

        # Verify embeddings saved
        embs = self.db.query(ProjectEmbedding).filter(
            ProjectEmbedding.project_id == self.project_id,
            ProjectEmbedding.source_type == "patent"
        ).all()
        self.assertEqual(len(embs), 2)

        # Get similarities
        sim_map = service.get_patent_similarities(self.project_id, [pat1, pat2])
        self.assertIn(pat1.id, sim_map)
        self.assertIn(pat2.id, sim_map)

        score_bio, band_bio = sim_map[pat1.id]
        score_concrete, band_concrete = sim_map[pat2.id]

        # Bio patent should have significantly higher similarity than concrete mixer
        self.assertGreater(score_bio, score_concrete)
        self.assertIn(band_bio, ["High semantic similarity", "Moderate semantic similarity"])
        self.assertEqual(band_concrete, "Low semantic similarity")

    def test_patent_similarity_threshold_bands(self):
        """Tests that similarity bands match Phase 4.4 conventions."""
        from app.services.embedding.semantic_similarity_service import get_similarity_label
        self.assertEqual(get_similarity_label(0.75), "High semantic similarity")
        self.assertEqual(get_similarity_label(0.70), "High semantic similarity")
        self.assertEqual(get_similarity_label(0.55), "Moderate semantic similarity")
        self.assertEqual(get_similarity_label(0.50), "Moderate semantic similarity")
        self.assertEqual(get_similarity_label(0.49), "Low semantic similarity")
        self.assertEqual(get_similarity_label(0.12), "Low semantic similarity")

    # =========================================================================
    # 7. Prior-Art Analysis Tests
    # =========================================================================

    def test_prior_art_heuristic_analysis(self):
        """Tests heuristic analysis synthesis (problem, solution, features, similarities, differences, claims)."""
        pat = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="P100",
            publication_number="US9988111B2",
            title="System for 3D Protein Coordinate Estimation",
            abstract="Coordinates estimated through spatial convolution and distance geometry.",
            claims=["1. A computer-implemented system estimating 3D protein coordinates."],
            assignees=["BioMed Systems LLC"],
            cpc_classifications=["G06N3/08", "G16B15/00"],
            jurisdiction="US"
        )
        self.db.add(pat)
        self.db.commit()

        analysis_service = PatentAnalysisService(self.db)
        resp = analysis_service.analyze_prior_art(self.project_id, self.user_id, max_patents=5)

        self.assertEqual(resp.total_analyzed, 1)
        item = resp.prior_art_analyses[0]
        self.assertEqual(item.publication_number, "US9988111B2")
        self.assertIn("protein", item.title.lower())
        self.assertTrue(len(item.key_features) > 0)
        self.assertTrue(len(item.similarities_with_idea) > 0)
        self.assertTrue(len(item.differences_from_idea) > 0)
        self.assertIn("Preliminary analysis against publication", item.claims_overlap_analysis)
        self.assertIn("Preliminary research assistance only", resp.disclaimer)

    # =========================================================================
    # 8. RAG Integration & Citation Tests
    # =========================================================================

    def test_rag_evidence_manifest_includes_patents(self):
        """Tests that EvidenceRetrievalService retrieves patents and assigns EVID-PAT-01..N IDs."""
        pat = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="PAT_TEST",
            publication_number="US10555666B2",
            title="Continuous Equivariant Molecular Filters",
            abstract="Continuous filter representations for molecular geometries.",
            jurisdiction="US",
            assignees=["AlphaFold Tech"],
            cpc_classifications=["G06N"],
            publication_date="2021-08-10"
        )
        self.db.add(pat)
        self.db.commit()

        retriever = EvidenceRetrievalService(self.db)
        manifest, meta = retriever.retrieve_evidence_manifest(self.project)

        patent_items = [e for e in manifest if e.source_type == "patent"]
        self.assertEqual(len(patent_items), 1)
        pat_evid = patent_items[0]
        self.assertEqual(pat_evid.evidence_id, "EVID-PAT-01")
        self.assertIn("US10555666B2", pat_evid.source_title)
        self.assertEqual(pat_evid.source_author, "AlphaFold Tech")
        self.assertEqual(pat_evid.publication_year, 2021)
        self.assertEqual(meta["patents_included"], 1)

    def test_rag_context_builder_includes_patents(self):
        """Tests that build_rag_context formats patent blocks with clean delimiters."""
        pat = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="PAT_TEST",
            publication_number="US10555666B2",
            title="Continuous Equivariant Molecular Filters",
            abstract="Continuous filter representations for molecular geometries.",
            jurisdiction="US"
        )
        self.db.add(pat)
        self.db.commit()

        retriever = EvidenceRetrievalService(self.db)
        manifest, _ = retriever.retrieve_evidence_manifest(self.project)
        context = build_rag_context(self.project, self.analysis, manifest)

        self.assertIn("RETRIEVED PATENT & PRIOR-ART EVIDENCE", context)
        self.assertIn("--- EVIDENCE BLOCK [EVID-PAT-01] ---", context)
        self.assertIn("US10555666B2", context)
        self.assertIn("--- END [EVID-PAT-01] ---", context)

    def test_citation_service_validates_patent_ids(self):
        """Tests that CitationService correctly extracts and validates EVID-PAT-xx IDs."""
        text = "This claim is supported by EVID-PAP-01 and prior art in EVID-PAT-02, whereas EVID-REP-03 shows code."
        ids = CitationService.extract_evidence_ids(text)
        self.assertIn("EVID-PAP-01", ids)
        self.assertIn("EVID-PAT-02", ids)
        self.assertIn("EVID-REP-03", ids)

    def test_heuristic_synthesizer_includes_patents(self):
        """Tests that synthesize_deterministic_report includes top patents in SimilarityAssessment."""
        pat = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="PAT_TEST",
            publication_number="US10555666B2",
            title="Continuous Equivariant Molecular Filters",
            abstract="Continuous filter representations for molecular geometries.",
            jurisdiction="US"
        )
        self.db.add(pat)
        self.db.commit()

        retriever = EvidenceRetrievalService(self.db)
        manifest, meta = retriever.retrieve_evidence_manifest(self.project)
        report = synthesize_deterministic_report(self.project, self.analysis, manifest, meta)

        self.assertIsNotNone(report.similarity_assessment)
        self.assertTrue(len(report.similarity_assessment.top_patents) > 0)
        self.assertEqual(report.similarity_assessment.top_patents[0]["evidence_id"], "EVID-PAT-01")

    # =========================================================================
    # 9. Statistics & Service Discovery Tests
    # =========================================================================

    def test_patent_stats_computation(self):
        """Tests calculating patent statistics: counts by provider, jurisdiction, classifications."""
        pat1 = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="P1",
            publication_number="US10000001",
            title="Patent 1",
            jurisdiction="US",
            assignees=["Google LLC"],
            cpc_classifications=["G06N", "G06F"]
        )
        pat2 = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="epo",
            provider_patent_id="P2",
            publication_number="EP20000002",
            title="Patent 2",
            jurisdiction="EP",
            assignees=["Siemens AG"],
            cpc_classifications=["G06N"]
        )
        self.db.add_all([pat1, pat2])
        self.db.commit()

        service = PatentDiscoveryService()
        stats = service.get_patent_stats(self.db, self.project_id)

        self.assertEqual(stats.total_patents, 2)
        self.assertEqual(stats.by_provider.get("uspto"), 1)
        self.assertEqual(stats.by_provider.get("epo"), 1)
        self.assertEqual(stats.by_jurisdiction.get("US"), 1)
        self.assertEqual(stats.by_jurisdiction.get("EP"), 1)
        self.assertEqual(stats.top_classifications.get("G06N"), 2)
        self.assertEqual(stats.top_assignees.get("Google LLC"), 1)
        self.assertIn("Preliminary research assistance only", stats.disclaimer)

    def test_patent_search_endpoint_auth_isolation(self):
        """Tests that accessing another user's project patents is forbidden (403)."""
        from app.routes.patents import verify_project_ownership
        from fastapi import HTTPException

        # Owner access succeeds
        proj = verify_project_ownership(self.project_id, self.user, self.db)
        self.assertEqual(proj.id, self.project_id)

        # Other user access raises 403 Forbidden
        with self.assertRaises(HTTPException) as ctx:
            verify_project_ownership(self.project_id, self.other_user, self.db)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_patent_embedding_populate_schema_similarities(self):
        """Tests enriching PatentSchema list with calculated similarities and bands."""
        pat = Patent(
            project_id=self.project_id,
            user_id=self.user_id,
            provider="uspto",
            provider_patent_id="P_POP",
            publication_number="US9988776B2",
            title="Equivariant Graph Molecular Docking",
            jurisdiction="US"
        )
        self.db.add(pat)
        self.db.commit()

        service = PatentEmbeddingService(self.db)
        service.ensure_patent_embeddings(self.project_id, [pat])

        schema = PatentSchema.model_validate(pat.to_dict())
        self.assertIsNone(schema.similarity_score)

        enriched = service.populate_schema_similarities(self.project_id, [schema], [pat])
        self.assertEqual(len(enriched), 1)
        self.assertIsNotNone(enriched[0].similarity_score)
        self.assertIsNotNone(enriched[0].similarity_band)

    def test_patent_query_generator_empty_fallback(self):
        """Tests that completely empty inputs safely fall back to reasonable default queries."""
        res = PatentQueryGenerator.generate_queries({})
        self.assertTrue(len(res["search_queries"]) > 0)
        self.assertTrue(len(res["cpc_codes"]) > 0)


if __name__ == "__main__":
    unittest.main()

