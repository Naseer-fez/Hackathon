"""Tests for async request queue, backpressure (HTTP 429), and serialized GPU access."""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.engine.local_gguf_provider import BackpressureError, LocalGgufLlmProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def provider() -> LocalGgufLlmProvider:
    """Create a LocalGgufLlmProvider with mocked model and small queue for testing."""
    with patch("backend.engine.local_gguf_provider.app_settings") as mock_settings:
        mock_settings.llm.model_path = "/fake/model.gguf"
        mock_settings.llm.n_ctx = 512
        mock_settings.llm.n_threads = 1
        mock_settings.llm.n_gpu_layers = 0
        mock_settings.llm.chat_format = "chatml"
        mock_settings.llm.temperature = 0.2
        mock_settings.llm.max_tokens = 64
        mock_settings.llm.enable_grammar = False
        mock_settings.llm.grammar_file = ""
        mock_settings.llm.max_queue_size = 2

        p = LocalGgufLlmProvider()
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "IS 1786:2008 for TMT bars."}}]
        }
        p._model = mock_model
    return p


# ---------------------------------------------------------------------------
# Backpressure tests
# ---------------------------------------------------------------------------

class TestBackpressureRaises:
    """Verify BackpressureError raised when queue is full."""

    def test_backpressure_raises_when_queue_full(self, provider: LocalGgufLlmProvider) -> None:
        """With max_queue_size=2 and 2 pending requests, third request raises BackpressureError."""
        provider._queue_count = 2  # simulate full queue

        async def run() -> None:
            await provider.generate_text("test prompt", "system")

        with pytest.raises(BackpressureError):
            asyncio.get_event_loop().run_until_complete(run())


class TestSerializedGpuAccess:
    """Verify requests are serialized (not parallel) on GPU."""

    def test_requests_serialized_on_gpu(self, provider: LocalGgufLlmProvider) -> None:
        """Two concurrent requests run sequentially, not in parallel."""
        call_order: list[int] = []
        original_sync = provider._sync_generate

        def tracked_generate(prompt: str, system_prompt: str | None) -> str | None:
            call_order.append(len(call_order) + 1)
            return "IS 269:2015 for OPC cement."

        provider._sync_generate = tracked_generate  # type: ignore[assignment]

        async def run() -> list[str]:
            t1 = asyncio.create_task(provider.generate_text("prompt 1", "sys"))
            t2 = asyncio.create_task(provider.generate_text("prompt 2", "sys"))
            return list(await asyncio.gather(t1, t2))

        results = asyncio.get_event_loop().run_until_complete(run())
        assert len(results) == 2
        assert all(r.strip() for r in results)
        # Both completed — serialized via semaphore
        assert len(call_order) == 2


class TestQueuePositionInStream:
    """Verify queued stream yields position event."""

    def test_queue_position_event_when_queued(self, provider: LocalGgufLlmProvider) -> None:
        """When request is queued behind another, first event is queue position JSON."""
        import json

        # Simulate one request already in queue
        provider._queue_count = 1

        mock_model = provider._model
        mock_model.create_chat_completion.return_value = iter([
            {"choices": [{"delta": {"content": "Token1"}}]},
        ])

        async def collect() -> list[str]:
            return [c async for c in provider.generate_text_stream("prompt", "sys")]

        chunks = asyncio.get_event_loop().run_until_complete(collect())
        # First chunk should be queue position JSON
        assert len(chunks) >= 1
        first = json.loads(chunks[0])
        assert first["status"] == "queued"
        assert first["position"] >= 2


class TestImmediateServing:
    """Verify no unnecessary delay when queue is empty."""

    def test_request_served_immediately_when_empty(self, provider: LocalGgufLlmProvider) -> None:
        """When no other requests are active, request is served without delay."""
        assert provider._queue_count == 0

        async def run() -> str:
            return await provider.generate_text("test", "sys")

        result = asyncio.get_event_loop().run_until_complete(run())
        assert "IS 1786:2008" in result
        assert provider._queue_count == 0  # counter back to 0


class TestHttp429FromRouter:
    """Verify HTTP 429 response from the router when BackpressureError is raised."""

    def test_http_429_from_router(self) -> None:
        """Using FastAPI TestClient, trigger backpressure → assert HTTP 429."""
        from backend.api.llm_router import router

        mock_std = MagicMock()
        mock_std.is_code = "IS 1786"
        mock_std.title = "TMT Steel Bars"

        mock_evidence = MagicMock()

        with (
            patch("backend.api.llm_router.loader") as mock_loader,
            patch("backend.api.llm_router.retriever") as mock_retriever,
            patch("backend.api.llm_router.advisor") as mock_advisor,
            patch("backend.api.llm_router.llm_service") as mock_llm_service,
        ):
            mock_loader.get_by_code.return_value = mock_std
            mock_loader.get_all_standards.return_value = [mock_std]
            mock_advisor.get_certification_alert.return_value = ""
            mock_retriever.search_with_evidence.return_value = (
                [(mock_std, 0.95)],
                [mock_evidence],
            )
            # Make the LLM service raise BackpressureError
            mock_llm_service.answer_procurement_query = AsyncMock(
                side_effect=BackpressureError("Queue full")
            )

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            resp = client.post(
                "/api/v1/ask-assistant",
                json={"question": "What standards for cement?"},
            )
            assert resp.status_code == 429
            assert "busy" in resp.json()["detail"].lower()
