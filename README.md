# AI ProjectDNA – Intelligent Innovation & Project Validation Platform
> **Phase 4.6: Patent & Prior-Art Discovery Engine**

AI ProjectDNA empowers students, academic researchers, and startup founders to validate project ideas, benchmark technical feasibility, discover prior art, analyze existing open-source implementations in depth, and synthesize concrete opportunities for differentiated innovation.

This milestone (**Phase 4.6**) introduces an intelligent **Patent & Prior-Art Discovery Engine**. It discovers existing patents and published patent applications relevant to a user's project idea using the USPTO PatentsView REST API and EPO Open Patent Services (OPS). Discovered patents are normalized, vector-embedded using Sentence Transformers (Phase 4.4), compared via dense cosine similarity, analyzed for prior-art technical claims, and fully integrated into the Phase 4.5 RAG Evidence Manifest as traceable `EVID-PAT-xx` citation tokens.

---

### Platform Discovery & Intelligence Pipeline
1. **Academic Research Discovery (Phase 4.1)**:
   - **arXiv API** (Official Atom 1.0 XML query feed)
   - **Semantic Scholar API** (Academic Graph REST API)
   - **OpenAlex API** (Open Scholarly Works API with inverted index abstract reconstruction)
2. **GitHub Existing Projects Discovery (Phase 4.2)**:
   - **Official GitHub REST API** (`api.github.com/search/repositories`)
   - Intelligent query synthesis generating 2–4 targeted queries from Phase 3 analyses
   - Comprehensive repository metadata, duplicate prevention, and automatic live metrics update on rediscovery
3. **GitHub Repository Deep Analysis & Innovation Gaps (Phase 4.3)**:
   - **README & Dependency Manifest Retrieval**: Fetches repository documentation and dependency manifests (`requirements.txt`, `package.json`, `pyproject.toml`) via GitHub API.
   - **7-Category Technology Stack Detection**: Categorizes languages, frontend frameworks, backend frameworks, databases, AI/ML libraries, cloud platforms, and DevOps tools with evidence citations.
   - **Feature Extraction & Classification**: Extracts project capabilities with confidence scores and documented vs. inferred classification.
   - **Architecture Topology Decomposition**: Details frontend, backend, database layer, AI/ML pipelines, and deployment infrastructure.
   - **Multi-Factor Similarity Model**: Computes transparent similarity alignments (Problem 30%, Feature 30%, Tech Stack 25%, Domain 15%) with detailed explanatory rationales.
   - **Synthesized Innovation Gap Detection**: Identifies missing features, partially implemented prototypes, modernization opportunities, and differentiating capabilities, clearly labeled as *"not found in the analyzed repositories"*.
   - **Dual AI & Heuristic Fallback Engine**: Uses Google Gemini 2.5 Flash for deep synthesis with automatic deterministic fallback if the API is offline or quota-limited.
4. **Semantic Embedding & Cross-Source Similarity Engine (Phase 4.4)**:
   - **Dense Text Embeddings**: Uses `sentence-transformers/all-MiniLM-L6-v2` producing 384-dimensional dense semantic vectors with CPU/GPU support and singleton caching.
   - **Text Synthesis & Normalization**: Standardized `TextPreprocessor` formats project ideas, research papers, and GitHub repositories with markdown cleaning and SHA-256 content hashing to avoid redundant computations.
   - **Vector Persistence & Dual Dialect Compatibility**: `ProjectEmbedding` model with custom `VectorType` using native `pgvector` on PostgreSQL and JSON fallback on SQLite.
   - **Cosine Similarity & Cross-Source Ranking**: Computes unit vector dot products, ranks matches in descending order, extracts overlapping conceptual facets, and classifies proximity into High, Moderate, and Low semantic similarity.
   - **Multi-Source Filtering**: Allows querying by source type (`research_paper`, `github_repository`, `patent`), minimum similarity threshold, and result limits.
5. **RAG-Based Evidence & Research Gap Validation Engine (Phase 4.5)**:
   - **Normalized Evidence Retrieval & Manifest**: Unifies papers, repos, and gap candidates into normalized `EvidenceItem` records with deterministic citation tokens (`EVID-PAP-xx`, `EVID-REP-xx`, `EVID-GAP-xx`, `EVID-PAT-xx`), evidence strength evaluation (`strong`, `moderate`, `weak`, `insufficient`), and documented vs. inferred categorization.
   - **Untrusted Content Sanitization & Context Building**: Sanitizes external metadata (abstracts, README excerpts) against prompt injection attempts, formats tagged contextual blocks, and enforces character budgeting.
   - **Citation Integrity Verification**: `CitationService` scans generated reports, verifying that every cited evidence ID exists in the retrieved manifest and purging hallucinated citations.
   - **Empirical Gap Classification**: `ResearchGapValidator` classifies candidate innovation gaps into `supported_gap`, `partially_supported_gap`, `not_supported_gap`, or `insufficient_evidence` with categorical confidence levels and grounded reasoning.
   - **Dual LLM & Deterministic Fallback**: Uses Google Gemini 2.5 Flash with structured JSON output enforcement (`ProjectValidationReportSchema`) and seamless deterministic fallback.
   - **Report Version History**: Version-tracked persistence (`ProjectValidationReport` model) enabling auditability across iterative project refinements.
6. **Patent & Prior-Art Discovery Engine (Phase 4.6)**:
   - **Multi-Provider Patent Search**: Integrates **USPTO PatentsView REST API** and **EPO Open Patent Services (OPS) API** with CPC classification mapping and query synthesis.
   - **Google Patents Integration**: Constructs deterministic canonical links (`https://patents.google.com/patent/{id}/en`) without brittle web scraping.
   - **Semantic Similarity Analysis**: Computes 384-dimensional dense embeddings for patent titles, abstracts, and claims, ranking patents into High ($\ge 0.70$), Moderate ($\ge 0.50$), and Low ($< 0.50$) semantic similarity against the project idea.
   - **Prior-Art Deep Analysis**: Extracts technical problem, proposed solution, key features, overlap analysis, technical differences, and claim boundaries using Gemini LLM and deterministic fallback.
   - **RAG & Evidence Manifest Integration**: Surfaces patents in Section 16/17 and attaches `EVID-PAT-xx` tokens to Phase 4.5 RAG validation reports.
   - **Legal Compliance & Boundaries**: Prominently features non-legal research disclaimers across API outputs, report sections, and UI drawers.

---

## 1. System Architecture & Tech Stack

### Frontend
- **Framework**: [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Bundler & Tooling**: [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) (Navy `#0B0F19` background, electric blue `#38BDF8` & purple `#8B5CF6` accents)
- **Routing**: [React Router v6](https://reactrouter.com/) (Protected and Public-only route guards)
- **State Management**: React Context (`AuthContext` with automatic session bootstrap)
- **HTTP Client**: [Axios](https://axios-http.com/) configured with `withCredentials: true`
- **Dashboard Sections in `AnalysisPage.tsx`**:
  - Sections 1–10: Comprehensive Gemini AI structured idea analysis
  - Section 11: Engineering Assumptions & Technical Challenges / Risks
  - Section 12: Academic Research Discovery (arXiv, Semantic Scholar, OpenAlex)
  - Section 13: GitHub Existing Projects Discovery (interactive repository cards, filters, and live search)
  - Section 14: GitHub Repository Deep Analysis & Innovation Gaps (metrics overview, priority-filtered innovation gap cards, multi-factor similarity meters, categorized technical stack badges with evidence hover, architecture topology, and analysis controls)
  - Section 15: Semantic Similarity & Cross-Source Matching (Phase 4.4)
  - Section 16: Evidence-Based Research Gap Validation (Phase 4.5) (KPI overview, version selector, interactive report tabs across 10 sections, validated gap cards with evidence pills and confidence badges, and interactive Evidence Manifest Explorer modal)
  - Section 17: **Patent & Prior-Art Discovery (Phase 4.6)** (USPTO & EPO discovery, similarity meters, abstract toggles, prior-art deep analysis modal, Google Patents verification links, pagination, and legal compliance disclaimer)

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- **Patent & Prior-Art Discovery Engine (Phase 4.6)**: `PatentDiscoveryService`, `PatentQueryGenerator` (CPC classification mapping), `USPTOService` (PatentsView REST API), `EPOService` (EPO Open Patent Services), `PatentEmbeddingService` (384-d semantic vectors), and `PatentAnalysisService` (prior-art differentiation & claims analysis)
- **RAG Validation Engine (Phase 4.5)**: `EvidenceRetrievalService` (normalized manifest construction with `EVID-PAT-xx` support), `ContextBuilder` (prompt sanitization and character budgeting), `CitationService` (citation integrity and hallucination purging), `ResearchGapValidator` (empirical gap classification), and `RAGService` (orchestration, Gemini synthesis, versioning, and persistence)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` via [Sentence Transformers](https://www.sbert.net/) & PyTorch (dimension 384, L2-normalized)
- **AI / LLM SDK**: Official [Google GenAI SDK (`google-genai`)](https://github.com/googleapis/python-genai) with Pydantic Structured Output (`gemini-2.5-flash`)
- **HTTP Client for External APIs**: [HTTPX](https://www.python-httpx.org/) (Async HTTP client with customizable timeouts and polite user-agents)
- **Embedding Pipeline**: `EmbeddingService` (singleton), `TextPreprocessor` (hashing and text preparation), `EmbeddingPipeline` (batch generation & upsert), and `SemanticSimilarityService` (cosine similarity & ranking)
- **ORM & Migrations**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/)
- **Vector Extension**: [pgvector-python](https://github.com/pgvector/pgvector-python) with dual-compatible `VectorType` fallback
- **Password Cryptography**: [Bcrypt](https://pypi.org/project/bcrypt/) (Cost factor 12)
- **Token Security**: [PyJWT](https://pyjwt.readthedocs.io/) (HS256 signed tokens stored in secure HttpOnly cookies)

### Database
- **Database Engine**: [PostgreSQL 16](https://www.postgresql.org/) with `pgvector` extension (with local SQLite fallback for standalone development)
- **Multi-Tenancy & Data Isolation**:
  - `projects.user_id -> users.id`
  - `project_analyses.project_id -> projects.id`
  - `research_papers.project_id -> projects.id` (ON DELETE CASCADE)
  - `github_repositories.project_id -> projects.id` (ON DELETE CASCADE)
  - `repository_analyses.project_id -> projects.id` (ON DELETE CASCADE)
  - `innovation_gaps.project_id -> projects.id` (ON DELETE CASCADE)
  - `project_embeddings.project_id -> projects.id` (ON DELETE CASCADE)
  - `project_validation_reports.project_id -> projects.id` (ON DELETE CASCADE)
  - `patents.project_id -> projects.id` (ON DELETE CASCADE, unique `(project_id, publication_number)`)
  - Composite Index: `(project_id, version)` on `project_validation_reports`

---

## 2. Directory Structure

```
AI ProjectDNA/
├── .env.example                       # Root environment variable template
├── .gitignore                         # Git exclusion rules
├── docker-compose.yml                 # Multi-service Docker configuration
├── README.md                          # Comprehensive documentation
│
├── backend/
│   ├── .env                           # Backend environment variables
│   ├── .env.example                   # Backend environment template with Phase 4.4 keys
│   ├── alembic.ini                    # Alembic migration configuration
│   ├── Dockerfile                     # Python 3.12 production containerfile
│   ├── requirements.txt               # Backend dependencies (includes sentence-transformers & pgvector)
│   ├── test_api.py                    # Phase 1 route test suite
│   ├── test_phase2_auth.py            # Phase 2 auth & multi-tenancy test suite
│   ├── test_phase3_ai.py              # Phase 3 AI Idea Analyzer test suite
│   ├── test_phase4_1_research.py      # Phase 4.1 Research Discovery unit test suite
│   ├── test_phase4_1_e2e.py           # Phase 4.1 Live HTTP end-to-end test runner
│   ├── test_phase4_2_github.py        # Phase 4.2 GitHub Discovery unit test suite
│   ├── test_phase4_2_e2e.py           # Phase 4.2 Live HTTP end-to-end test runner
│   ├── test_phase4_3_analysis.py      # Phase 4.3 Deep Analysis & Gaps unit tests
│   ├── test_phase4_3_e2e.py           # Phase 4.3 Live HTTP end-to-end test runner
│   ├── test_phase4_4_embeddings.py    # Phase 4.4 20-point Semantic Embedding unit tests
│   ├── test_phase4_4_e2e.py           # Phase 4.4 Live HTTP end-to-end test runner
│   ├── test_phase4_5_rag.py           # Phase 4.5 30-point RAG Validation unit tests
│   ├── test_phase4_5_e2e.py           # Phase 4.5 Live HTTP end-to-end test runner
│   ├── test_phase4_6_patents.py       # Phase 4.6 26-point Patent & Prior-Art unit tests
│   ├── test_phase4_6_e2e.py           # Phase 4.6 14-step Live HTTP end-to-end test runner
│   │
│   ├── alembic/                       # Database migrations
│   │   ├── env.py                     # Alembic runner with dynamic DB URL & model metadata
│   │   └── versions/
│   │       ├── 0001_phase2_auth_and_ownership.py
│   │       ├── 0002_phase3_project_analyses.py
│   │       ├── 0003_phase4_1_research_papers.py
│   │       ├── 0004_phase4_2_github_repositories.py
│   │       ├── 0005_phase4_3_repository_analysis.py
│   │       ├── 0006_phase4_4_project_embeddings.py
│   │       ├── 0007_phase4_5_project_validation_reports.py
│   │       └── 0008_phase4_6_patents.py # Phase 4.6 Patents Table
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py                    # FastAPI application, CORS, routers (Phases 1-4.6)
│       ├── core/
│       │   ├── config.py              # Patent, RAG, and Embedding settings
│       │   ├── security.py            # Bcrypt hashing & PyJWT token utilities
│       │   └── deps.py                # Database sessions & user authentication dependencies
│       ├── models/
│       │   ├── user.py, project.py, analysis.py, research_paper.py, github_repo.py
│       │   ├── repository_analysis.py, innovation_gap.py, project_embedding.py
│       │   ├── project_validation_report.py
│       │   └── patent.py              # Patent model with publication uniqueness & legal metadata
│       ├── schemas/
│       │   ├── user.py, project.py, analysis.py, research.py, github.py, repository_analysis.py
│       │   ├── embedding.py, validation.py
│       │   └── patent.py              # Pydantic v2 schemas for patent discovery & prior-art analysis
│       ├── services/
│       │   ├── ai_service.py          # Google Gemini 2.5 Flash SDK integration
│       │   ├── research/              # Academic paper services (arXiv, Semantic Scholar, OpenAlex)
│       │   ├── github/                # GitHub discovery and deep analysis modules
│       │   ├── embedding/             # Dense vector encoders, preprocessor, and pipeline
│       │   ├── rag/                   # Evidence retrieval, context builder, citation, and validator
│       │   └── patents/               # PatentsView, EPO OPS, query gen, embedding, and prior art
│       └── routes/
│           ├── auth.py, projects.py, analysis.py, research.py, github.py, repository_analysis.py
│           ├── similarity.py, validation.py
│           └── patents.py             # REST endpoints for patent search, stats, prior-art & evidence
│
└── frontend/
    ├── src/
    │   ├── types/
    │   │   ├── auth.ts, project.ts, analysis.ts, research.ts, github.ts, repositoryAnalysis.ts
    │   │   ├── embedding.ts, validation.ts
    │   │   └── patent.ts              # TypeScript interfaces for patent discovery & prior art
    │   ├── services/
    │   │   ├── api.ts, authService.ts, projectService.ts, analysisService.ts
    │   │   ├── researchService.ts, githubService.ts, repositoryAnalysisService.ts
    │   │   ├── embeddingService.ts, validationService.ts
    │   │   └── patentService.ts       # Axios client for patent discovery, stats & prior art
    │   └── pages/
    │       └── AnalysisPage.tsx       # Unified Dashboard featuring Section 17 Patent Discovery
```

---

## 3. Semantic Embedding & Cosine Similarity Methodology

### A. Dense Vector Embeddings
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Output Dimension**: 384 dimensions
- **Execution Mode**: CPU / GPU singleton cached instance.
- **Normalization**: All output vectors are strictly $L_2$-normalized:
  $$\|\vec{v}\|_2 = \sqrt{\sum_{i=1}^{384} v_i^2} = 1.0$$
  Consequently, cosine similarity simplifies to the Euclidean dot product:
  $$\cos(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\|_2 \|\vec{v}\|_2} = \vec{u} \cdot \vec{v}$$

### B. Similarity Categorization
- **High semantic similarity**: $\text{Cosine Similarity} \ge 0.70$ (Strong thematic overlap and shared methodology)
- **Moderate semantic similarity**: $0.50 \le \text{Cosine Similarity} < 0.70$ (Related problem space or related architecture)
- **Low semantic similarity**: $\text{Cosine Similarity} < 0.50$ (Distant technical connection)

### C. Distinction Between Phase 4.3 & Phase 4.4 Similarities
- **Phase 4.3 Multi-Factor Heuristic**: Evaluates structural, explicit token overlap across 4 discrete dimensions (Problem 30%, Features 30%, Tech Stack 25%, Domain 15%).
- **Phase 4.4 Dense Vector Similarity**: Evaluates conceptual proximity in a 384-dimensional latent embedding space, recognizing related projects even when differing keywords or programming languages are used.

> **Disclaimer**: Semantic similarity reflects conceptual proximity in dense vector space under the designated model. It does not constitute conclusive proof of duplication or novelty.

---

## 4. API Endpoints

### Phase 4.6: Patent & Prior-Art Discovery Engine
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/projects/{project_id}/patents/search` | **Required** | Executes patent search across USPTO PatentsView and EPO OPS, normalizes metadata, generates dense vector embeddings, computes semantic similarity against project idea, and persists results. Supports `max_results`, `providers`, and `force_refresh`. |
| `GET` | `/api/projects/{project_id}/patents` | **Required** | Retrieves discovered patents for the project with sorting (`similarity_score`, `filing_date`, `publication_date`), filtering by `provider`, `similarity_band`, and pagination (`page`, `page_size`). |
| `GET` | `/api/projects/{project_id}/patents/stats` | **Required** | Retrieves patent statistics: total patents found, provider breakdown, similarity band distribution, average similarity score, and latest search timestamp. |
| `GET` | `/api/projects/{project_id}/patents/evidence` | **Required** | Retrieves normalized patent evidence items with deterministic `EVID-PAT-xx` tokens, strength tiers, and Google Patents URLs for RAG integration. |
| `POST` | `/api/projects/{project_id}/patents/analyze` | **Required** | Conducts deep prior-art comparative analysis using Gemini LLM (with deterministic fallback) across top patents or specified `patent_ids`. |
| `GET` | `/api/projects/{project_id}/patents/analysis` | **Required** | Retrieves existing prior-art deep analysis results and summary metrics for the project. |
| `GET` | `/api/projects/{project_id}/patents/{patent_id}` | **Required** | Retrieves complete details for a single patent, including claims, abstract, and CPC classifications. |

### Phase 4.5: RAG Research Gap Validation Engine
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/projects/{project_id}/validation/generate` | **Required** | Executes RAG validation synthesis, evaluates candidate innovation gaps against evidence (including patents), sanitizes citations, and creates a versioned report. Supports `force_regenerate`. |
| `GET` | `/api/projects/{project_id}/validation` | **Required** | Retrieves latest generated RAG validation report for the project. |
| `GET` | `/api/projects/{project_id}/validation/history` | **Required** | Retrieves version history and summary metrics for all validation reports of this project. |
| `GET` | `/api/projects/{project_id}/validation/{report_id}` | **Required** | Retrieves a specific validation report by its unique ID. |
| `GET` | `/api/projects/{project_id}/validation/evidence` | **Required** | Retrieves the normalized, traceable evidence manifest (`EVID-PAP-xx`, `EVID-REP-xx`, `EVID-GAP-xx`, `EVID-PAT-xx`) with strength tiers and source breakdown. |

### Phase 4.4: Semantic Embedding & Vector Similarity
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/projects/{project_id}/embeddings/generate` | **Required** | Generates 384-d dense vector embeddings for the project idea, stored research papers, GitHub repositories, and patents. Skips items with unchanged SHA-256 `content_hash` unless `force_regenerate=true`. |
| `GET` | `/api/projects/{project_id}/similarity` | **Required** | Computes and ranks cross-source semantic cosine similarities against the project idea anchor vector. Supports `source_type` (`research_paper`, `github_repository`, `patent`), `min_similarity`, and `limit`. |
| `GET` | `/api/projects/{project_id}/similarity/stats` | **Required** | Retrieves embedding storage statistics: total stored vectors, breakdown by source type, latest generation timestamp, model name, and dimension. |

---

## 5. Environment Configuration

Add the following variables to `backend/.env`:
```ini
# Google Gemini AI Integration (Phase 3)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Academic Research Paper Discovery (Phase 4.1)
SEMANTIC_SCHOLAR_API_KEY=
OPENALEX_EMAIL=admin@projectdna.local
RESEARCH_SEARCH_MAX_RESULTS=20
RESEARCH_PROVIDER_TIMEOUT=20.0

# GitHub Repository Discovery (Phase 4.2)
GITHUB_TOKEN=your_personal_access_token_here_optional
GITHUB_API_TIMEOUT=20.0
GITHUB_SEARCH_MAX_RESULTS=30
GITHUB_MAX_QUERIES=4

# GitHub Repository Deep Analysis & Innovation Gaps (Phase 4.3)
GITHUB_ANALYSIS_MAX_REPOS=10
GITHUB_README_MAX_CHARS=25000
GITHUB_ANALYSIS_TIMEOUT=30.0

# Semantic Embedding & Vector Similarity (Phase 4.4)
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
EMBEDDING_BATCH_SIZE=32
SIMILARITY_HIGH_THRESHOLD=0.70
SIMILARITY_MODERATE_THRESHOLD=0.50

# RAG Research Gap Validation Engine (Phase 4.5)
RAG_MAX_PAPERS=15
RAG_MAX_REPOS=15
RAG_MAX_GAPS=20
RAG_CONTEXT_MAX_CHARS=40000
RAG_EVIDENCE_MIN_SIMILARITY=0.20

# Patent & Prior-Art Discovery Engine (Phase 4.6)
USPTO_API_KEY=
USPTO_API_URL=https://api.patentsview.org/patents/query
EPO_OPS_CONSUMER_KEY=
EPO_OPS_CONSUMER_SECRET=
PATENT_SEARCH_MAX_RESULTS=20
PATENT_PROVIDER_TIMEOUT=25.0
RAG_MAX_PATENTS=10
```

---

## 6. Automated Testing & Verification

### A. Run Phase 4.6 Unit Test Suite (26 Tests)
```powershell
.\backend\venv\Scripts\python.exe backend\test_phase4_6_patents.py
```
**Test Coverage**:
1. Publication number normalization across USPTO, EPO, and WIPO formats.
2. Jurisdiction code extraction (`US`, `EP`, `WO`, `JP`, etc.).
3. Google Patents URL builder (`https://patents.google.com/patent/{id}/en`).
4. Abstract cleaning and tokenized inventor list sanitizer.
5. Technical domain to CPC classification code mapper (`G06N`, `G06F`, `G16H`, `H04L`, etc.).
6. Query generator keyword combinations synthesis from Phase 3 idea analysis.
7. PatentsView REST API query builder and response normalization.
8. EPO Open Patent Services (OPS) search query and XML parser.
9. Patent dense text embedding text preparation (`prepare_patent_text`).
10. Cosine similarity calculation against project idea anchor vector.
11. Similarity band categorization (`High`, `Moderate`, `Low semantic similarity`).
12. Multi-provider deduplication by `(project_id, publication_number)`.
13. Patent database persistence and foreign key integrity.
14. Prior-art deep analysis prompt construction and claims evaluation.
15. Deterministic fallback for prior-art analysis when LLM is unavailable.
16. Normalized evidence item manifest generation (`EVID-PAT-xx`).
17. Evidence strength categorization for patents (`strong`, `moderate`, `weak`).
18. Multi-tenant access control and ownership validation (`403 Forbidden`).
19. Search endpoint query validation and provider filtering.
20. Pagination, sorting, and similarity threshold filters.
21. Patent summary statistics aggregation.
22. Deep prior-art analysis endpoint execution and persistence.
23. Single patent detail retrieval by ID.
24. Evidence manifest endpoint retrieval.
25. RAG context builder patent block formatting (`=== PATENT PRIOR ART ===`).
26. Legal disclaimer presence on all responses and schema validation.

### B. Run Phase 4.6 Live End-to-End HTTP Socket Test (14 Steps)
```powershell
.\backend\venv\Scripts\python.exe backend\test_phase4_6_e2e.py
```
Tests the complete end-to-end patent discovery and RAG validation workflow on live HTTP sockets:
1. Live FastAPI server bootstrap on isolated port.
2. User registration and cookie authentication.
3. Project creation and Phase 3 AI Analysis.
4. Triggering patent discovery search (`POST /api/projects/{id}/patents/search`).
5. Vector embedding generation and dense semantic similarity ranking.
6. Verification of similarity categorization (`High`, `Moderate`, `Low`).
7. Querying patent listing with pagination and filters (`GET /api/projects/{id}/patents`).
8. Verifying summary statistics (`GET /api/projects/{id}/patents/stats`).
9. Retrieving single patent detail with claims and CPC classifications (`GET /api/projects/{id}/patents/{id}`).
10. Executing deep prior-art comparative analysis (`POST /api/projects/{id}/patents/analyze`).
11. Verifying prior-art analysis results (`GET /api/projects/{id}/patents/analysis`).
12. Generating normalized patent evidence manifest (`GET /api/projects/{id}/patents/evidence`).
13. RAG Validation report integration: verifying `EVID-PAT-xx` citation tokens and patent prior-art blocks in Phase 4.5 report.
14. Multi-tenant security testing: unauthorized competitor user rejected with `403 Forbidden` across all patent endpoints.

### C. Run Full Platform Regression Suites
```powershell
.\backend\venv\Scripts\python.exe backend\test_phase2_auth.py
.\backend\venv\Scripts\python.exe backend\test_phase3_ai.py
.\backend\venv\Scripts\python.exe backend\test_phase4_1_research.py
.\backend\venv\Scripts\python.exe backend\test_phase4_2_github.py
.\backend\venv\Scripts\python.exe backend\test_phase4_3_analysis.py
.\backend\venv\Scripts\python.exe backend\test_phase4_4_embeddings.py
.\backend\venv\Scripts\python.exe backend\test_phase4_5_rag.py
.\backend\venv\Scripts\python.exe backend\test_phase4_6_patents.py
```

### D. Build Frontend
```powershell
npm --prefix frontend run build
```

---

## 7. Scope Boundaries & Legal Disclaimers

### Implemented in Phase 4.6:
- Multi-provider patent retrieval via official REST APIs: **USPTO PatentsView** and **EPO Open Patent Services (OPS)**.
- Google Patents canonical reference links for transparent verification.
- Cooperative Patent Classification (CPC) mapping based on technical domain.
- Dense semantic vector embeddings (384 dimensions) and cosine similarity scoring.
- Deep prior-art comparative analysis (technical problem, solution, claims breakdown, similarities, differences, and limitations).
- Seamless RAG integration: patent evidence items assigned deterministic `EVID-PAT-xx` tokens and incorporated into Phase 4.5 validation reports.
- Comprehensive UI (Section 17) with stats summary, search controls, similarity score meters, abstract toggles, prior-art analysis drawer, and Evidence Explorer patent filter tab.

### Legal Guardrails & Scope Constraints:
- **Preliminary Research Only**: All outputs are intended solely for academic, research, and technical ideation purposes.
- **No Formal Patentability Opinion**: This platform **does not** provide legal counsel, formal freedom-to-operate (FTO) opinions, or legally binding patentability certifications.
- **Absence of Evidence Principle**: The system never claims an idea is "globally unpatented"; it strictly reports findings as *"not found in the analyzed patent sources"*.
- **No Scraping**: Strictly adheres to published REST APIs and user-navigable external links without brittle HTML scraping.
