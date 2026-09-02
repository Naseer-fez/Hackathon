"""Unit tests for configuration loader and settings."""
from __future__ import annotations

from backend.config.paths import CONFIG_YAML_PATH
from backend.config.settings import AppSettings, load_settings


def test_load_settings_default() -> None:
    """Test loading configuration with default values."""
    settings = load_settings("non_existent_config.yaml")
    assert isinstance(settings, AppSettings)
    assert settings.server.port == 8000
    assert settings.server.host == "127.0.0.1"


def test_load_settings_from_real_yaml() -> None:
    """Test loading configuration from existing config.yaml."""
    settings = load_settings(CONFIG_YAML_PATH)
    assert settings.server.log_level == "INFO"
    assert settings.ai_engine.top_k_recommendations == 5
    assert settings.llm.provider in ["openrouter", "local_gguf"]
    assert settings.llm.n_ctx == 4096
    assert settings.llm.n_threads == 4
    assert "all-MiniLM-L6-v2" in settings.ai_engine.embedding_model_name
