"""Unit tests for hybrid retriever."""
from __future__ import annotations

from backend.engine.hybrid_retriever import HybridRetriever
from backend.ingestion.standards_loader import StandardsLoader


def test_hybrid_search_semantic_and_code() -> None:
    """Test hybrid search with semantic description and exact IS code."""
    loader = StandardsLoader()
    retriever = HybridRetriever(loader=loader)

    # Semantic test
    results = retriever.search(query="solar rooftop pv module", top_k=3)
    assert len(results) > 0
    top_std, score, reasons = results[0]
    assert "14286" in top_std.is_code or "Solar" in top_std.title
    assert score > 0.3

    # Exact code match test
    code_results = retriever.search(query="Requirement as per IS 1786", top_k=2)
    assert len(code_results) > 0
    assert "1786" in code_results[0][0].is_code
