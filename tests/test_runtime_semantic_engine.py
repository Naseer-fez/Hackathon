"""Runtime integration test for BIS-SpecAI semantic retrieval engine on actual data."""
from __future__ import annotations
import pytest
from backend.engine.hybrid_retriever import HybridRetriever
from backend.models.recommendation_model import DocumentChunkEvidence
from backend.models.standard_model import IndianStandard


@pytest.fixture(scope="module")
def retriever() -> HybridRetriever:
    """Fixture providing initialized HybridRetriever backed by actual data stores."""
    return HybridRetriever()


@pytest.mark.parametrize(
    ("query", "expected_code"),
    [
        ("High strength deformed steel bars for concrete reinforcement Fe 500D", "IS 1786"),
        ("Terrestrial Photovoltaic PV modules crystalline silicon solar panels", "IS 14286"),
        ("Outdoor oil type three phase distribution transformer 11kV", "IS 1180"),
        ("Portable fire extinguishers performance and construction", "IS 15683"),
    ],
)
def test_runtime_macro_discovery_actual_data(
    retriever: HybridRetriever, query: str, expected_code: str
) -> None:
    """Verify macro standard discovery returns valid actual IndianStandard records."""
    results = retriever.search(query=query, top_k=3)
    assert len(results) > 0, f"No matches found for real query: {query}"
    top_standard, score, match_reasons = results[0]

    assert isinstance(top_standard, IndianStandard)
    assert expected_code in top_standard.is_code
    assert top_standard.title != ""
    assert top_standard.year >= 1990
    assert score > 0.40
    assert len(match_reasons) > 0
    assert top_standard.scope != ""


def test_runtime_dual_index_evidence_actual_data(retriever: HybridRetriever) -> None:
    """Verify dual-index search yields macro standards and micro PDF document chunks."""
    standards, evidences = retriever.search_with_evidence(
        query="ordinary portland cement 43 grade compressive strength", top_k=2, top_k_chunks=3
    )
    assert len(standards) > 0
    top_std, score, _ = standards[0]
    assert any(code in top_std.is_code for code in ["IS 8112", "IS 269", "IS 12269", "IS 1489"])

    assert isinstance(evidences, list)
    if evidences:
        top_ev = evidences[0]
        assert isinstance(top_ev, DocumentChunkEvidence)
        assert top_ev.file_name != ""
        assert top_ev.page_number >= 1
        assert len(top_ev.snippet) > 10
