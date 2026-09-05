"""Unit tests for distributed AI architecture (Fast Answer & Heavy Reasoning)."""
from __future__ import annotations
from typing import AsyncGenerator
import pytest
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_orchestrator import LlmOrchestrator
from backend.models.llm_contracts import PipelineAnswerResponse


class MockFastLocalProvider(BaseLlmProvider):
    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Fast 2B response: IS 269 applies for Ordinary Portland Cement."

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        yield "Fast 2B response"


class MockMacProvider(BaseLlmProvider):
    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Heavy Mac reasoning: Comprehensive QCO compliance verified under Scheme I."

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        yield "Heavy Mac reasoning"


class MockFailingMacProvider(BaseLlmProvider):
    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        raise TimeoutError("Mac reasoning endpoint timeout")

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        raise TimeoutError("Mac stream timeout")
        yield ""


@pytest.mark.asyncio
async def test_fast_answer_pipeline() -> None:
    """Test fast answer pipeline bypasses Mac and uses local model."""
    orchestrator = LlmOrchestrator(
        cloud_provider=MockMacProvider(),
        local_provider=MockFastLocalProvider(),
    )
    res = await orchestrator.execute_fast_answer(
        query="What is the standard for OPC 53 cement?",
        pdf_text="OPC 53 cement specifications as per IS 269."
    )
    assert isinstance(res, PipelineAnswerResponse)
    assert "Fast 2B response" in res.answer
    assert res.query == "What is the standard for OPC 53 cement?"


@pytest.mark.asyncio
async def test_heavy_reasoning_pipeline() -> None:
    """Test heavy reasoning pipeline with context synthesis and Mac offloading."""
    orchestrator = LlmOrchestrator(
        cloud_provider=MockMacProvider(),
        local_provider=MockFastLocalProvider(),
    )
    # Enable distributed flag on instance for test
    orchestrator._distributed = True
    res = await orchestrator.execute_heavy_reasoning(
        query="Verify structural steel Fe 500D requirements",
        pdf_text="Supply 500 MT Fe 500D rebars conforming to IS 1786.",
        chat_history=[{"role": "user", "content": "Tell me about IS 1786"}, {"role": "assistant", "content": "IS 1786 covers high strength deformed steel bars."}],
        refresh_context=True,
    )
    assert isinstance(res, PipelineAnswerResponse)
    assert "Heavy Mac reasoning" in res.answer
    assert res.source_tier == "remote_mac"


@pytest.mark.asyncio
async def test_heavy_reasoning_fallback_when_mac_fails() -> None:
    """Test heavy reasoning falls back gracefully to local model when Mac fails."""
    orchestrator = LlmOrchestrator(
        cloud_provider=MockFailingMacProvider(),
        local_provider=MockFastLocalProvider(),
    )
    orchestrator._distributed = True
    res = await orchestrator.execute_heavy_reasoning(
        query="Verify structural steel Fe 500D requirements",
        pdf_text="Supply 500 MT Fe 500D rebars conforming to IS 1786.",
    )
    assert isinstance(res, PipelineAnswerResponse)
    assert "Fast 2B response" in res.answer
    assert res.source_tier == "local_2b_fallback"
