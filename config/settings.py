"""
ResearchAI - Central Configuration
All settings loaded from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class APISettings(BaseSettings):
    """External API configuration (all free tier)."""
    # Semantic Scholar (free, optional key for higher rate limits)
    semantic_scholar_api_key: str = ""
    semantic_scholar_base_url: str = "https://api.semanticscholar.org/graph/v1"

    # arXiv (completely free, no key needed)
    arxiv_max_results: int = 50

    # PubMed (free Entrez API)
    pubmed_base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    pubmed_email: str = ""  # Required by NCBI for identification

    # HuggingFace (free, optional token for gated models)
    huggingface_api_token: str = ""


class ModelSettings(BaseSettings):
    """AI model configuration (all free/open-source)."""
    # Summarization - facebook/bart-large-cnn (free, runs locally)
    summarization_model: str = "facebook/bart-large-cnn"

    # Embeddings - all-MiniLM-L6-v2 (free, fast, runs locally)
    embedding_model: str = "all-MiniLM-L6-v2"

    # Text generation fallback (small model for demo)
    text_generation_model: str = "google/flan-t5-base"

    # Device configuration
    device: str = "cuda" if os.environ.get("USE_GPU", "false").lower() == "true" else "cpu"


class StorageSettings(BaseSettings):
    """Storage and caching configuration."""
    # Cache directory for API responses
    cache_dir: str = str(PROJECT_ROOT / "data" / "cache")
    cache_enabled: bool = True

    # ChromaDB persistence
    chroma_persist_dir: str = str(PROJECT_ROOT / "data" / "chroma_db")

    # Knowledge graph storage
    graph_save_path: str = str(PROJECT_ROOT / "data" / "knowledge_graph.json")

    # SQLite database for paper metadata
    sqlite_db_path: str = str(PROJECT_ROOT / "data" / "researchai.db")


class AppSettings(BaseSettings):
    """Application-level settings."""
    log_level: str = "INFO"
    max_papers_per_query: int = 50
    summary_max_length: int = 300
    summary_min_length: int = 80
    chunk_size: int = 512
    chunk_overlap: int = 50


# Singleton instances
api_settings = APISettings()
model_settings = ModelSettings()
storage_settings = StorageSettings()
app_settings = AppSettings()
