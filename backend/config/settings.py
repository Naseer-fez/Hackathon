"""Application settings and configuration loader."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
import yaml
from pydantic import BaseModel, Field

load_dotenv()


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


class StorageSettings(BaseModel):
    data_dir: str = "d:/CODE/Hackathon/backend/data"
    standards_file: str = "d:/CODE/Hackathon/backend/data/standards_database.json"
    qco_file: str = "d:/CODE/Hackathon/backend/data/qco_registry.json"
    upload_dir: str = "d:/CODE/Hackathon/backend/data/uploads"


class AiEngineSettings(BaseModel):
    embedding_model_name: str = "d:/CODE/Hackathon/llm/all-MiniLM-L6-v2"
    multilingual_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    similarity_threshold: float = 0.35
    top_k_recommendations: int = 5
    hybrid_alpha: float = 0.65
    enable_gpu: bool = True
    reranker_model: str = "BAAI/bge-reranker-small"
    reranker_candidate_pool: int = 25
    domain_expansions_file: str = "d:/CODE/Hackathon/backend/config/domain_expansions.yaml"


class LlmSettings(BaseModel):
    provider: str = "openrouter"
    model_name: str = "nvidia/nemotron-3.5-lightning:free"
    model_path: str = "d:/CODE/Hackathon/llm/gemma-2-2b-it-Q4_K_M.gguf"
    n_ctx: int = 4096
    n_threads: int = 4
    n_gpu_layers: int = 99
    chat_format: str = "gemma"
    api_key_env_var: str = "GEMINI_API_KEY"
    openrouter_api_key_env_var: str = "OPENROUTER_API_KEY"
    temperature: float = 0.2
    max_tokens: int = 2048
    enable_grammar: bool = False
    grammar_file: str = ""
    max_queue_size: int = 5


class CacheSettings(BaseModel):
    sqlite_db_path: str = "d:/CODE/Hackathon/backend/data/semantic_cache.db"
    similarity_threshold: float = 0.95


class VoiceSettings(BaseModel):
    stt_model_path: str = "d:/CODE/Hackathon/llm/faster-whisper-tiny"
    tts_eng_model_path: str = "d:/CODE/Hackathon/llm/mms-tts-eng"
    tts_hin_model_path: str = "d:/CODE/Hackathon/llm/mms-tts-hin"


class BisScraperSettings(BaseModel):
    base_url: str = "https://www.services.bis.gov.in"
    qco_portal_url: str = "https://www.bis.gov.in/product-certification"
    request_timeout_sec: int = 15
    user_agent: str = "Mozilla/5.0"


class LoggingSettings(BaseModel):
    log_dir: str = "d:/CODE/Hackathon/backend/logs"
    log_file: str = "d:/CODE/Hackathon/backend/logs/backend.log"
    level: str = "INFO"
    rotation_max_bytes: int = 10_485_760
    backup_count: int = 5


class AppSettings(BaseModel):
    server: ServerSettings = Field(default_factory=ServerSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    ai_engine: AiEngineSettings = Field(default_factory=AiEngineSettings)
    llm: LlmSettings = Field(default_factory=LlmSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    bis_scraper: BisScraperSettings = Field(default_factory=BisScraperSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)


def load_settings(config_path: str | Path | None = None) -> AppSettings:
    cfg_path = config_path or os.getenv("APP_CONFIG_PATH", "d:/CODE/Hackathon/backend/config/config.yaml")
    raw_data: dict[str, Any] = {}
    if Path(cfg_path).exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as fh:
                parsed = yaml.safe_load(fh)
                if isinstance(parsed, dict):
                    raw_data = parsed
        except (yaml.YAMLError, OSError, ValueError):
            raw_data = {}
    return AppSettings.model_validate(raw_data)


app_settings: AppSettings = load_settings()
