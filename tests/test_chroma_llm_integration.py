"""Integration test for Vector DB (ChromaDB), LLM, and Backend API integration."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.llm_service import LlmService
from backend.main import app
from backend.models.standard_model import IndianStandard


@pytest.fixture
def test_client() -> TestClient:
    """Fixture providing FastAPI test client."""
    return TestClient(app)


def test_hybrid_retriever_chromadb_search() -> None:
    """Test HybridRetriever querying ChromaDB vector store and returning hydrated IndianStandard objects."""
    retriever = HybridRetriever()
    results = retriever.search(query="solar photovoltaic modules crystalline silicon", top_k=3)

    assert len(results) > 0
    std, score, reasons = results[0]
    assert isinstance(std, IndianStandard)
    assert std.is_code != ""
    assert isinstance(score, float)
    assert score > 0.0
    assert len(reasons) > 0


class MockTestProvider:
    """Mock LLM provider for rapid deterministic integration testing."""
    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        return f"AI Evaluation: Standard conforms to BIS specifications for prompt: {prompt[:80]}"


@pytest.mark.asyncio
async def test_llm_service_with_chroma_standard() -> None:
    """Test LLM service generating technical explanation for ChromaDB-hydrated standard."""
    retriever = HybridRetriever()
    matches = retriever.search(query="TMT steel rebars Fe 500D", top_k=1)
    assert len(matches) > 0
    std, _, _ = matches[0]

    llm_service = LlmService(provider=MockTestProvider())  # type: ignore
    explanation = await llm_service.explain_recommendation(
        query="High strength steel rebar Fe 500D for RCC construction",
        standard=std,
        qco_alert="Mandatory ISI Mark Certification",
    )

    assert isinstance(explanation, str)
    assert len(explanation) > 20
    assert "AI Evaluation" in explanation or std.is_code in explanation


@pytest.mark.asyncio
async def test_llm_service_procurement_qa() -> None:
    """Test conversational procurement Q&A with dynamic ChromaDB standard context."""
    retriever = HybridRetriever()
    matches = retriever.search(query="distribution transformer 11kV energy efficiency", top_k=3)
    standards = [m[0] for m in matches]

    llm_service = LlmService(provider=MockTestProvider())  # type: ignore
    answer = await llm_service.answer_procurement_query(
        question="What are the energy efficiency and testing requirements for distribution transformers?",
        context_standards=standards,
    )

    assert isinstance(answer, str)
    assert len(answer) > 20
    assert "AI Evaluation" in answer



def test_explain_standard_api_endpoint(test_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test POST /api/v1/explain-standard with ChromaDB IS code."""
    from backend.api.llm_router import llm_service
    monkeypatch.setattr(llm_service, "_provider", MockTestProvider())
    payload = {
        "query": "Crystalline Silicon Terrestrial Photovoltaic PV Modules",
        "is_code": "IS 14286",
    }
    res = test_client.post("/api/v1/explain-standard", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_code"] == "IS 14286"
    assert len(data["explanation"]) > 20


def test_ask_assistant_api_endpoint(test_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test POST /api/v1/ask-assistant conversational endpoint backed by ChromaDB."""
    from backend.api.llm_router import llm_service
    monkeypatch.setattr(llm_service, "_provider", MockTestProvider())
    payload = {
        "question": "Which standard applies to fire extinguishers ABC type?",
    }
    res = test_client.post("/api/v1/ask-assistant", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "question" in data
    assert len(data["answer"]) > 20



