"""Centralized dynamic path resolution and directory management for BIS-SpecAI.

Resolves PROJECT_ROOT / BASE_DIR dynamically to guarantee absolute cross-platform
compatibility without any hardcoded drive letters or static machine-specific paths.
Supports environment variable overrides and automatic directory creation.
"""
from __future__ import annotations

import os
from pathlib import Path

# Dynamically locate project root (2 levels up from backend/config/paths.py)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
BASE_DIR: Path = PROJECT_ROOT

# Backend directories
BACKEND_DIR: Path = PROJECT_ROOT / "backend"
CONFIG_DIR: Path = BACKEND_DIR / "config"
DATA_DIR: Path = Path(os.getenv("APP_DATA_DIR", str(BACKEND_DIR / "data")))
LOGS_DIR: Path = Path(os.getenv("APP_LOGS_DIR", str(BACKEND_DIR / "logs")))
UPLOADS_DIR: Path = Path(os.getenv("APP_UPLOADS_DIR", str(DATA_DIR / "uploads")))
CACHE_DIR: Path = DATA_DIR

# Configuration files
CONFIG_YAML_PATH: Path = Path(os.getenv("APP_CONFIG_PATH", str(CONFIG_DIR / "config.yaml")))
DOMAIN_EXPANSIONS_PATH: Path = Path(os.getenv("DOMAIN_EXPANSIONS_PATH", str(CONFIG_DIR / "domain_expansions.yaml")))

# Core dataset files
STANDARDS_DB_PATH: Path = Path(os.getenv("STANDARDS_DATABASE_PATH", str(DATA_DIR / "standards_database.json")))
QCO_REGISTRY_PATH: Path = Path(os.getenv("QCO_REGISTRY_PATH", str(DATA_DIR / "qco_registry.json")))
RAG_GOLDEN_DATASET_PATH: Path = Path(os.getenv("RAG_GOLDEN_DATASET_PATH", str(DATA_DIR / "rag_golden_dataset.json")))
SEMANTIC_CACHE_DB_PATH: Path = Path(os.getenv("SEMANTIC_CACHE_DB_PATH", str(DATA_DIR / "semantic_cache.db")))

# AI Models & LLM directory
LLM_DIR: Path = Path(os.getenv("LLM_DIR", str(PROJECT_ROOT / "llm")))
EMBEDDING_MODEL_PATH: Path = Path(os.getenv("EMBEDDING_MODEL_PATH", str(LLM_DIR / "paraphrase-multilingual-MiniLM-L12-v2")))
RERANKER_MODEL_PATH: Path = Path(os.getenv("RERANKER_MODEL_PATH", str(LLM_DIR / "bge-reranker-small")))
DEFAULT_GGUF_MODEL_PATH: Path = Path(os.getenv("DEFAULT_GGUF_MODEL_PATH", str(LLM_DIR / "Qwen2.5-7B-Instruct-Q4_K_M.gguf")))
GRAMMAR_FILE_PATH: Path = Path(os.getenv("GRAMMAR_FILE_PATH", str(BACKEND_DIR / "engine" / "grammars" / "bis_output.gbnf")))

# Voice model paths
STT_MODEL_PATH: Path = Path(os.getenv("STT_MODEL_PATH", str(LLM_DIR / "faster-whisper-tiny")))
TTS_ENG_MODEL_PATH: Path = Path(os.getenv("TTS_ENG_MODEL_PATH", str(LLM_DIR / "mms-tts-eng")))
TTS_HIN_MODEL_PATH: Path = Path(os.getenv("TTS_HIN_MODEL_PATH", str(LLM_DIR / "mms-tts-hin")))

# Vector DB directories
VECTORDB_DIR: Path = Path(os.getenv("VECTORDB_PATH", str(PROJECT_ROOT / "vectordb")))
VECTORDB_DATA_DIR: Path = VECTORDB_DIR / "data"
VECTORDB_CHROMA_DIR: Path = Path(os.getenv("DOCUMENT_VECTORDB_PATH", str(VECTORDB_DATA_DIR / "chroma")))


def ensure_runtime_directories() -> None:
    """Safely ensure all runtime output, data, upload, cache, and log directories exist."""
    runtime_dirs: list[Path] = [
        DATA_DIR,
        LOGS_DIR,
        UPLOADS_DIR,
        CACHE_DIR,
        VECTORDB_DIR,
        VECTORDB_DATA_DIR,
        VECTORDB_CHROMA_DIR,
    ]
    for d in runtime_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass


# Automatically ensure core runtime directories on import
ensure_runtime_directories()
