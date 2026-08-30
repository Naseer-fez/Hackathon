"""Application settings and configuration loader."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field


class ServerSettings(BaseModel):
    """Server configuration parameters."""
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


class StorageSettings(BaseModel):
    """Storage directory and file path settings."""
    data_dir: str = "d:/CODE/Hackathon/backend/data"
    standards_file: str = "d:/CODE/Hackathon/backend/data/standards_database.json"
    qco_file: str = "d:/CODE/Hackathon/backend/data/qco_registry.json"
    upload_dir: str = "d:/CODE/Hackathon/backend/data/uploads"


class AiEngineSettings(BaseModel):
    """AI and semantic search settings."""
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    multilingual_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    similarity_threshold: float = 0.35
    top_k_recommendations: int = 5
    hybrid_alpha: float = 0.65
    enable_gpu: bool = False


class LlmSettings(BaseModel):
    """Abstracted LLM provider and reasoning settings."""
    provider: str = "fallback"
    model_name: str = "gemini-2.0-flash"
    api_key_env_var: str = "GEMINI_API_KEY"
    temperature: float = 0.2
    max_tokens: int = 1024


class BisScraperSettings(BaseModel):
    """BIS scraper settings."""
    base_url: str = "https://www.services.bis.gov.in"
    qco_portal_url: str = "https://www.bis.gov.in/product-certification"
    request_timeout_sec: int = 15
    user_agent: str = "Mozilla/5.0"


class AppSettings(BaseModel):
    """Global application settings."""
    server: ServerSettings = Field(default_factory=ServerSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    ai_engine: AiEngineSettings = Field(default_factory=AiEngineSettings)
    llm: LlmSettings = Field(default_factory=LlmSettings)
    bis_scraper: BisScraperSettings = Field(default_factory=BisScraperSettings)


def load_settings(config_path: str | Path | None = None) -> AppSettings:
    """Load settings from YAML configuration file and environment variables."""
    cfg_path = config_path or os.getenv(
        "APP_CONFIG_PATH", "d:/CODE/Hackathon/backend/config/config.yaml"
    )
    path_obj = Path(cfg_path)

    raw_data: dict[str, Any] = {}
    if path_obj.exists():
        try:
            with open(path_obj, "r", encoding="utf-8") as file_handle:
                parsed = yaml.safe_load(file_handle)
                if isinstance(parsed, dict):
                    raw_data = parsed
        except (yaml.YAMLError, OSError, ValueError):
            raw_data = {}

    return AppSettings.model_validate(raw_data)


app_settings: AppSettings = load_settings()
