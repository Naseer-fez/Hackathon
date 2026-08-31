"""Unit tests for OpenRouter Cloud LLM Provider and factory routing."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_providers import OpenRouterLlmProvider
from backend.engine.llm_service import LlmService, get_llm_provider


@pytest.mark.asyncio
async def test_openrouter_provider_fallback_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    provider = OpenRouterLlmProvider(api_key="")
    res = await provider.generate_text("Prompt without key")
    assert isinstance(res, str) and "No LLM model is currently available" in res


@pytest.mark.asyncio
async def test_openrouter_provider_successful_generation() -> None:
    provider = OpenRouterLlmProvider(api_key="sk-or-v1-mock-key", model="anthropic/claude-3.5-sonnet")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": "OpenRouter generated BIS technical justification."}}]}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await provider.generate_text("Explain IS 2062", system_prompt="BIS Procurement Advisor")
        assert res == "OpenRouter generated BIS technical justification."
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_openrouter_provider_http_error_handling() -> None:
    import httpx
    provider = OpenRouterLlmProvider(api_key="sk-or-v1-mock-key")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection failed")
        res = await provider.generate_text("Query with error")
        assert isinstance(res, str) and "No LLM model is currently available" in res


def test_get_llm_provider_openrouter_factory() -> None:
    for alias in ["openrouter", "open_router", "OPENROUTER"]:
        provider = get_llm_provider(alias)
        assert isinstance(provider, OpenRouterLlmProvider)
