"""Unit and integration tests for abstracted LLM service and endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_providers import (
    DeterministicFallbackProvider,
    GeminiLlmProvider,
    LocalGgufLlmProvider,
    OpenAiLlmProvider,
)
from backend.engine.llm_service import LlmService, get_llm_provider
from backend.ingestion.standards_loader import StandardsLoader
from backend.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_llm_providers_and_fallback() -> None:
    """Test all pluggable LLM providers."""
    fallback = DeterministicFallbackProvider()
    res = await fallback.generate_text("Prompt query", "System instruction")
    assert "BIS AI Reasoner" in res

    gemini = GeminiLlmProvider(api_key="")
    res_gemini = await gemini.generate_text("Gemini query")
    assert isinstance(res_gemini, str)

    openai = OpenAiLlmProvider(api_key="")
    res_openai = await openai.generate_text("OpenAI query")
    assert isinstance(res_openai, str)

    local_gguf = LocalGgufLlmProvider(model_path="non_existent.gguf")
    res_gguf = await local_gguf.generate_text("Local GGUF query")
    assert isinstance(res_gguf, str)


@pytest.mark.asyncio
async def test_llm_service_domain_methods() -> None:
    """Test LLM service domain explanation and Q&A."""
    service = LlmService()
    loader = StandardsLoader()
    std = loader.get_by_code("IS 1786")
    assert std is not None

    explanation = await service.explain_recommendation(
        query="High strength rebar", standard=std, qco_alert="Mandatory ISI"
    )
    assert len(explanation) > 0

    answer = await service.answer_procurement_query(
        question="What is the standard for TMT rebars?",
        context_standards=[std],
    )
    assert len(answer) > 0


def test_llm_api_endpoints() -> None:
    """Test REST API routes for LLM explanation and assistant."""
    explain_res = client.post(
        "/api/v1/explain-standard",
        json={"query": "TMT steel rebar Fe 500D", "is_code": "IS 1786"},
    )
    assert explain_res.status_code == 200
    assert "explanation" in explain_res.json()

    ask_res = client.post(
        "/api/v1/ask-assistant",
        json={"question": "Which standard applies to distribution transformers?"},
    )
    assert ask_res.status_code == 200
    assert "answer" in ask_res.json()
