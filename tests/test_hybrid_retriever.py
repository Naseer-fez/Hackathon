"""Unit tests for hybrid retriever and its new sub-components."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.query_expander import QueryExpander
from backend.engine.reranker_service import RerankerService
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.standard_model import IndianStandard


# ---------------------------------------------------------
# Query Expander Tests
# ---------------------------------------------------------

def test_query_expansion_adds_bis_terms() -> None:
    """Test query expansion adds formal BIS terms."""
    expander = QueryExpander()
    original = "solar panel"
    expanded = expander.expand(original)
    
    assert original in expanded
    assert "photovoltaic" in expanded.lower()
    assert "crystalline" in expanded.lower()

def test_query_expansion_preserves_original() -> None:
    """Test expansion keeps original query at start."""
    expander = QueryExpander()
    expanded = expander.expand("TMT bar")
    
    assert expanded.startswith("TMT bar")
    assert "1786" in expanded

def test_query_expansion_no_match_returns_original() -> None:
    """Test unmatched query returns original text."""
    expander = QueryExpander()
    original = "quantum teleportation device"
    expanded = expander.expand(original)
    
    assert expanded == original


# ---------------------------------------------------------
# Reranker Service Tests
# ---------------------------------------------------------

def test_reranker_reorders_by_cross_encoder_score() -> None:
    """Test cross-encoder reranks candidates properly."""
    reranker = RerankerService()
    
    # Mock cross-encoder predict to return inverted scores for existing candidates
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.1, 0.9, 0.5]  # Standard 2 should win
    reranker._cross_encoder = mock_model
    
    # Setup dummy standards
    std1 = IndianStandard(is_code="IS 1", title="A", division="A", year=2020, scope="")
    std2 = IndianStandard(is_code="IS 2", title="B", division="A", year=2020, scope="")
    std3 = IndianStandard(is_code="IS 3", title="C", division="A", year=2020, scope="")
    
    candidates = [
        (std1, 0.9, ["hybrid match"]),
        (std2, 0.8, ["hybrid match"]),
        (std3, 0.7, ["hybrid match"]),
    ]
    
    reranked = reranker.rerank("test query", candidates, top_k=2)
    
    # Assert top 2 returned, and IS 2 is first due to ce score of 0.9
    assert len(reranked) == 2
    assert reranked[0][0].is_code == "IS 2"
    assert reranked[1][0].is_code == "IS 3"
    
    # Assert reason appended
    assert any("Cross-Encoder reranked" in r for r in reranked[0][2])

@patch.object(RerankerService, "_load_model")
def test_reranker_graceful_fallback_on_load_failure(mock_load: MagicMock) -> None:
    """Test reranker falls back to original order if model fails to load."""
    reranker = RerankerService()
    reranker._cross_encoder = None
    
    std1 = IndianStandard(is_code="IS 1", title="A", division="A", year=2020, scope="")
    std2 = IndianStandard(is_code="IS 2", title="B", division="A", year=2020, scope="")
    
    candidates = [
        (std1, 0.9, ["hybrid match"]),
        (std2, 0.8, ["hybrid match"]),
    ]
    
    reranked = reranker.rerank("test query", candidates, top_k=2)
    
    # Assert fallback to original order
    assert reranked[0][0].is_code == "IS 1"
    assert reranked[1][0].is_code == "IS 2"


# ---------------------------------------------------------
# Hybrid Retriever Integration Tests
# ---------------------------------------------------------

def test_hybrid_search_semantic_and_code() -> None:
    """Test hybrid search with semantic description and exact IS code."""
    loader = StandardsLoader()
    retriever = HybridRetriever(loader=loader)

    # Semantic test
    results = retriever.search(query="solar rooftop pv module", top_k=3)
    assert len(results) > 0
    top_std, score, reasons = results[0]
    assert "14286" in top_std.is_code or "Solar" in top_std.title
    assert score > 0.2

    # Exact code match test
    code_results = retriever.search(query="Requirement as per IS 1786", top_k=2)
    assert len(code_results) > 0
    assert "1786" in code_results[0][0].is_code

def test_search_returns_results_for_trade_terms() -> None:
    """Test search retrieves correct standard for expanded trade terms."""
    loader = StandardsLoader()
    retriever = HybridRetriever(loader=loader)
    
    # TMT bar should map to IS 1786 via query expansion
    results = retriever.search(query="TMT bar", top_k=5)
    codes = [std.is_code for std, _score, _reasons in results]
    assert any("1786" in code for code in codes)
