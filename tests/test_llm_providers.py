"""Unit tests for LocalGgufLlmProvider, factory registration, and resilience."""
from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_providers import LocalGgufLlmProvider
from backend.engine.llm_service import LlmService, get_llm_provider
from backend.models.standard_model import IndianStandard, StandardStatus


@pytest.mark.asyncio
async def test_local_gguf_provider_fallback_offline() -> None:
    """Test LocalGgufLlmProvider reports offline status when file does not exist."""
    provider = LocalGgufLlmProvider(model_path="d:/non_existent/path/model.gguf", n_ctx=2048, n_threads=2)
    result = await provider.generate_text("Explain IS 1786 rebar requirements")
    assert isinstance(result, str) and "No LLM model is currently available" in result


@pytest.mark.asyncio
async def test_local_gguf_provider_mock_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test LocalGgufLlmProvider generating text via llama_cpp completion."""
    provider = LocalGgufLlmProvider()
    mock_model = MagicMock()
    mock_model.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "Mocked GGUF response for BIS Standard"}}]
    }
    monkeypatch.setattr(provider, "_model", mock_model)
    result = await provider.generate_text("Generate clause", system_prompt="BIS Spec")
    assert result == "Mocked GGUF response for BIS Standard"
    mock_model.create_chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_local_gguf_provider_exception_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test LocalGgufLlmProvider returns faithful message when model inference raises runtime error."""
    provider = LocalGgufLlmProvider()
    mock_model = MagicMock()
    mock_model.create_chat_completion.side_effect = RuntimeError("CUDA OOM")
    monkeypatch.setattr(provider, "_model", mock_model)
    result = await provider.generate_text("Query prompt")
    assert isinstance(result, str) and "No LLM model is currently available" in result


def test_get_llm_provider_local_aliases() -> None:
    """Test factory resolution for local_gguf aliases."""
    for alias in ["local_gguf", "gguf", "local", "LOCAL_GGUF"]:
        assert isinstance(get_llm_provider(alias), LocalGgufLlmProvider)


def test_local_gguf_provider_context_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test graceful multi-tier fallback when higher context size fails."""
    provider = LocalGgufLlmProvider(model_path="d:/dummy/path.gguf", n_ctx=2048)
    monkeypatch.setattr("pathlib.Path.exists", lambda _: True)
    attempts: list[int] = []

    def mock_init(self: LocalGgufLlmProvider, ctx: int) -> MagicMock:
        attempts.append(ctx)
        if ctx == 2048:
            raise ValueError("OOM at 2048")
        return MagicMock()

    monkeypatch.setattr(LocalGgufLlmProvider, "_init_llama_instance", mock_init)
    assert provider._load_model() is not None
    assert attempts == [2048, 1024]


@pytest.mark.asyncio
async def test_llm_service_with_local_gguf(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test LlmService functioning end-to-end with LocalGgufLlmProvider."""
    provider = LocalGgufLlmProvider()
    mock_model = MagicMock()
    mock_model.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "IS 456 governs reinforced concrete structural design."}}]
    }
    monkeypatch.setattr(provider, "_model", mock_model)
    service = LlmService(provider=provider)
    std = IndianStandard(
        is_code="IS 456",
        title="Plain and Reinforced Concrete - Code of Practice",
        division="Civil Engineering",
        year=2000,
        scope="Plain and reinforced concrete",
        key_parameters=["Compressive strength"],
        test_methods=["IS 516"],
        status=StandardStatus.ACTIVE,
    )
    exp = await service.explain_recommendation("M25 Concrete", std, "Voluntary")
    assert isinstance(exp, str) and "IS 456" in exp

