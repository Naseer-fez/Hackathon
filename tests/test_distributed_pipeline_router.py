"""Unit tests for distributed AI architecture router endpoints."""
from __future__ import annotations
import json
from fastapi.testclient import TestClient
import pytest
from backend.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing FastAPI test client."""
    return TestClient(app)


def test_fast_answer_endpoint(client: TestClient) -> None:
    """Test /fast-answer endpoint with form-data."""
    data = {
        "query": "What is the standard for Ordinary Portland Cement 53 Grade?",
        "pdf_text": "Sample text for cement specification IS 269.",
    }
    res = client.post("/api/v1/fast-answer", data=data)
    assert res.status_code == 200
    res_data = res.json()
    assert "query" in res_data
    assert "answer" in res_data
    assert "source_tier" in res_data


def test_heavy_reasoning_endpoint(client: TestClient) -> None:
    """Test /heavy-reasoning endpoint with form-data and chat history."""
    chat_hist = json.dumps([
        {"role": "user", "content": "Tell me about structural steel."},
        {"role": "assistant", "content": "IS 800 specifies code of practice for steel construction."}
    ])
    data = {
        "query": "What are the yield strength criteria for Fe 410?",
        "pdf_text": "Steel structures shall comply with IS 800 and IS 2062 Grade E250/E410.",
        "chat_history": chat_hist,
        "refresh_context": "false",
    }
    res = client.post("/api/v1/heavy-reasoning", data=data)
    assert res.status_code == 200
    res_data = res.json()
    assert "query" in res_data
    assert "answer" in res_data


def test_summarize_context_endpoint(client: TestClient) -> None:
    """Test /summarize-context endpoint."""
    payload = {
        "chat_history": [
            {"role": "user", "content": "Query 1: IS 1786 rebars"},
            {"role": "assistant", "content": "Answer 1: Yield strength 500 MPa"},
        ]
    }
    res = client.post("/api/v1/summarize-context", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert "summarized_context" in res_data
