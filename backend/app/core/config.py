import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory containing the app
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Resolve .env files relative to backend and project root
root_env_file = PROJECT_ROOT / ".env"
backend_env_file = BACKEND_DIR / ".env"

# Explicitly load .env into os.environ with priority (backend/.env overrides root .env)
if root_env_file.is_file():
    load_dotenv(dotenv_path=root_env_file, override=False)
if backend_env_file.is_file():
    load_dotenv(dotenv_path=backend_env_file, override=True)


class Settings(BaseSettings):
    APP_NAME: str = "AI ProjectDNA API"
    APP_VERSION: str = "4.6.0 - Phase 4.6 Patent & Prior-Art Discovery Engine"
    DEBUG: bool = True
    API_PREFIX: str = "/api"
    
    # Database configuration
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/aiprojectdna"
    FALLBACK_TO_SQLITE: bool = True
    SQLITE_URL: str = "sqlite:///./projectdna.db"
    
    # Authentication & Security
    JWT_SECRET_KEY: str = "ai-projectdna-secure-jwt-secret-key-phase2-prod-ready-32bytes-min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    AUTH_COOKIE_NAME: str = "projectdna_access_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    
    # Google Gemini AI Integration (Phase 3)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Research Paper Discovery Integration (Phase 4.1)
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    OPENALEX_EMAIL: str = ""
    RESEARCH_SEARCH_MAX_RESULTS: int = 20
    RESEARCH_PROVIDER_TIMEOUT: float = 20.0

    # GitHub Repository Discovery Integration (Phase 4.2)
    GITHUB_TOKEN: str = ""
    GITHUB_API_TIMEOUT: float = 20.0
    GITHUB_SEARCH_MAX_RESULTS: int = 30
    GITHUB_MAX_QUERIES: int = 5

    # GitHub Repository Deep Analysis & Innovation Gap Detection (Phase 4.3)
    GITHUB_ANALYSIS_MAX_REPOS: int = 10
    GITHUB_README_MAX_CHARS: int = 25000
    GITHUB_ANALYSIS_TIMEOUT: float = 30.0

    # Semantic Embedding & Cross-Source Similarity Engine (Phase 4.4)
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32
    SIMILARITY_HIGH_THRESHOLD: float = 0.70
    SIMILARITY_MODERATE_THRESHOLD: float = 0.50

    # RAG-Based Evidence & Research Gap Validation Engine (Phase 4.5)
    RAG_MAX_PAPERS: int = 15
    RAG_MAX_REPOS: int = 15
    RAG_MAX_GAPS: int = 20
    RAG_CONTEXT_MAX_CHARS: int = 40000
    RAG_EVIDENCE_MIN_SIMILARITY: float = 0.20

    # Patent & Prior-Art Discovery Engine (Phase 4.6)
    USPTO_API_KEY: str = ""
    USPTO_API_URL: str = "https://api.patentsview.org/patents/query"
    EPO_OPS_CONSUMER_KEY: str = ""
    EPO_OPS_CONSUMER_SECRET: str = ""
    PATENT_SEARCH_MAX_RESULTS: int = 25
    PATENT_PROVIDER_TIMEOUT: float = 20.0
    RAG_MAX_PATENTS: int = 15
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=[str(backend_env_file), str(root_env_file)],
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
