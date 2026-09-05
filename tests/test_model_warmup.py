"""Unit tests for server startup preloading, model warmup, and singleton guarantees."""
from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from backend.engine.embedding_service import EmbeddingService, get_embedding_service
from backend.engine.llm_service import get_llm_provider, get_llm_service
from backend.engine.local_gguf_provider import LocalGgufLlmProvider
from backend.vectordb.embedding_function import SentenceTransformerEmbeddingFunction


def test_local_gguf_preload_and_warmup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test LocalGgufLlmProvider preload and warmup cycle."""
    provider = LocalGgufLlmProvider(model_path="dummy/path.gguf")
    mock_llama = MagicMock()
    mock_llama.create_chat_completion.return_value = {"choices": [{"message": {"content": "OK"}}]}

    monkeypatch.setattr(provider, "_load_model", lambda: mock_llama)
    assert not provider.is_loaded()

    # Test preload
    loaded = provider.preload()
    assert loaded is True
    assert provider.is_loaded()

    # Test warmup
    warmed = provider.warmup()
    assert warmed is True
    mock_llama.create_chat_completion.assert_called_once()


def test_embedding_service_preload_and_warmup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test EmbeddingService preload and warmup execution."""
    service = EmbeddingService(model_name="dummy-model")
    mock_st = MagicMock()
    mock_st.encode.return_value = [0.1] * 384

    monkeypatch.setattr(service, "_try_load_model", lambda: setattr(service, "_model", mock_st))
    assert service.preload() is True
    assert service.warmup() is True


def test_sentence_transformer_chroma_warmup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test ChromaDB SentenceTransformerEmbeddingFunction preload and warmup."""
    embed_fn = SentenceTransformerEmbeddingFunction(model_name="dummy-model")
    mock_st = MagicMock()
    mock_st.encode.return_value = [[0.1] * 384]

    monkeypatch.setattr(embed_fn, "_load_model", lambda: setattr(embed_fn, "_model", mock_st))
    assert embed_fn.preload() is True
    assert embed_fn.warmup() is True


def test_singleton_guarantees() -> None:
    """Verify get_llm_provider, get_llm_service, and get_embedding_service return singletons."""
    prov1 = get_llm_provider("local_gguf")
    prov2 = get_llm_provider("local_gguf")
    assert prov1 is prov2

    svc1 = get_llm_service()
    svc2 = get_llm_service()
    assert svc1 is svc2

    emb1 = get_embedding_service()
    emb2 = get_embedding_service()
    assert emb1 is emb2


def test_warmup_backend_ai_models_mac_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify warmup_backend_ai_models preloads 2B and reranker while bypassing 7B in Mac mode."""
    from backend.config.settings import app_settings
    from backend.engine.model_warmup import warmup_backend_ai_models

    monkeypatch.setattr(app_settings.distributed_reasoning, "mac_available", True)

    mock_embed = MagicMock()
    mock_chroma = MagicMock()
    mock_reranker = MagicMock()
    mock_2b = MagicMock()

    monkeypatch.setattr("backend.engine.model_warmup.get_embedding_service", lambda: mock_embed)
    monkeypatch.setattr("backend.engine.model_warmup.SentenceTransformerEmbeddingFunction", lambda: mock_chroma)
    monkeypatch.setattr("backend.engine.model_warmup.RerankerService", lambda: mock_reranker)
    monkeypatch.setattr("backend.engine.model_warmup.get_llm_provider", lambda prov: mock_2b if prov == "local" else MagicMock())

    elapsed = warmup_backend_ai_models()
    assert elapsed >= 0.0

    mock_embed.preload.assert_called_once()
    mock_embed.warmup.assert_called_once()
    mock_chroma.preload.assert_called_once()
    mock_chroma.warmup.assert_called_once()
    mock_reranker.preload.assert_called_once()
    mock_reranker.warmup.assert_called_once()
    mock_2b.preload.assert_called_once()
    mock_2b.warmup.assert_called_once()


def test_7b_model_guard_blocks_instantiation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify LocalGgufLlmProvider strictly blocks loading 7B weights when Mac mode is active."""
    from backend.config.settings import app_settings
    monkeypatch.setattr(app_settings.distributed_reasoning, "mac_available", True)

    prov_7b = LocalGgufLlmProvider(model_path="llm/Qwen2.5-7B-Instruct-Q4_K_M.gguf")
    # Even if file existed, _load_model must refuse and return None
    loaded = prov_7b._load_model()
    assert loaded is None

