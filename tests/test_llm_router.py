"""Tests for LLM router SSE streaming endpoints."""
from __future__ import annotations

from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.llm_router import router


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_client() -> TestClient:
    """Create a FastAPI TestClient with only the llm_router mounted."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


async def _mock_explain_stream(**kwargs: Any) -> AsyncGenerator[str, None]:
    """Simulate streaming explanation chunks."""
    for chunk in ["The primary ", "Indian Standard ", "is IS 1786:2008", ", Clause 6.2."]:
        yield chunk


async def _mock_ask_stream(**kwargs: Any) -> AsyncGenerator[str, None]:
    """Simulate streaming assistant answer chunks."""
    for chunk in ["TMT steel bars ", "must comply with ", "IS 1786:2008."]:
        yield chunk


async def _mock_explain_stream_error(**kwargs: Any) -> AsyncGenerator[str, None]:
    """Simulate a stream that raises mid-way."""
    yield "Partial content "
    raise RuntimeError("LLM failure")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client() -> TestClient:
    """Provide a patched TestClient with all dependencies mocked."""
    mock_std = MagicMock()
    mock_std.is_code = "IS 1786"
    mock_std.title = "TMT Steel Bars"

    mock_evidence = MagicMock()
    mock_evidence.chunk_text = "excerpt"
    mock_evidence.page_number = 1
    mock_evidence.source_file = "test.pdf"

    with (
        patch("backend.api.llm_router.loader") as mock_loader,
        patch("backend.api.llm_router.retriever") as mock_retriever,
        patch("backend.api.llm_router.advisor") as mock_advisor,
        patch("backend.api.llm_router.llm_service") as mock_llm_service,
    ):
        mock_loader.get_by_code.return_value = mock_std
        mock_loader.get_all_standards.return_value = [mock_std]
        mock_advisor.get_certification_alert.return_value = "QCO mandatory"
        mock_retriever.search.return_value = [(mock_std, 0.95)]
        mock_retriever.search_document_evidence.return_value = [mock_evidence]
        mock_retriever.search_with_evidence.return_value = (
            [(mock_std, 0.95)],
            [mock_evidence],
        )
        mock_llm_service.explain_recommendation_stream = _mock_explain_stream
        mock_llm_service.answer_procurement_query_stream = _mock_ask_stream

        yield _make_test_client()


@pytest.fixture()
def client_with_error() -> TestClient:
    """Provide a patched TestClient where the stream raises an error."""
    mock_std = MagicMock()
    mock_std.is_code = "IS 1786"
    mock_std.title = "TMT Steel Bars"

    with (
        patch("backend.api.llm_router.loader") as mock_loader,
        patch("backend.api.llm_router.retriever") as mock_retriever,
        patch("backend.api.llm_router.advisor") as mock_advisor,
        patch("backend.api.llm_router.llm_service") as mock_llm_service,
    ):
        mock_loader.get_by_code.return_value = mock_std
        mock_advisor.get_certification_alert.return_value = ""
        mock_retriever.search_document_evidence.return_value = []
        mock_llm_service.explain_recommendation_stream = _mock_explain_stream_error

        yield _make_test_client()


# ---------------------------------------------------------------------------
# SSE Content-Type tests
# ---------------------------------------------------------------------------

class TestSSEContentType:
    """Verify streaming endpoints return text/event-stream."""

    def test_explain_stream_content_type(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/explain-standard-stream",
            json={"query": "requirements", "is_code": "IS 1786"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_ask_stream_content_type(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/ask-assistant-stream",
            json={"question": "What BIS standards apply to TMT steel bars?"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]


# ---------------------------------------------------------------------------
# SSE format tests
# ---------------------------------------------------------------------------

class TestSSEFormat:
    """Verify SSE data: prefix and [DONE] terminator."""

    def test_explain_stream_sse_format(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/explain-standard-stream",
            json={"query": "requirements", "is_code": "IS 1786"},
        )
        body = resp.text
        lines = [line for line in body.split("\n") if line.strip()]
        # Every non-empty line must start with "data: "
        for line in lines:
            assert line.startswith("data: "), f"Line does not start with 'data: ': {line!r}"
        # Last non-empty line must be the [DONE] terminator
        assert lines[-1] == "data: [DONE]"

    def test_ask_stream_sse_format(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/ask-assistant-stream",
            json={"question": "What BIS standards apply to TMT steel bars?"},
        )
        body = resp.text
        lines = [line for line in body.split("\n") if line.strip()]
        for line in lines:
            assert line.startswith("data: "), f"Line does not start with 'data: ': {line!r}"
        assert lines[-1] == "data: [DONE]"
        # Verify actual content is present
        combined = " ".join(lines)
        assert "IS 1786:2008" in combined

    def test_stream_contains_natural_prose_and_is_codes(self, client: TestClient) -> None:
        """Verify the stream contains both natural English prose and IS code citations."""
        resp = client.post(
            "/api/v1/explain-standard-stream",
            json={"query": "requirements", "is_code": "IS 1786"},
        )
        body = resp.text
        # Natural prose
        assert "Indian Standard" in body
        # IS code citation
        assert "IS 1786:2008" in body


# ---------------------------------------------------------------------------
# SSE error format test
# ---------------------------------------------------------------------------

class TestSSEErrorFormat:
    """Verify error events are properly formatted as SSE."""

    def test_stream_error_format(self, client_with_error: TestClient) -> None:
        resp = client_with_error.post(
            "/api/v1/explain-standard-stream",
            json={"query": "requirements", "is_code": "IS 1786"},
        )
        body = resp.text
        lines = [line for line in body.split("\n") if line.strip()]
        # Should contain error event and DONE terminator
        assert any("data: [ERROR: RuntimeError]" in line for line in lines)
        assert lines[-1] == "data: [DONE]"
