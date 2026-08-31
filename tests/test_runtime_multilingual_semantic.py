"""Runtime test for multilingual Indic semantic query processing."""
from __future__ import annotations
import pytest
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.multilingual_processor import MultilingualProcessor
from backend.models.standard_model import IndianStandard


@pytest.fixture(scope="module")
def processor() -> MultilingualProcessor:
    """Fixture providing MultilingualProcessor."""
    return MultilingualProcessor()


@pytest.fixture(scope="module")
def retriever() -> HybridRetriever:
    """Fixture providing HybridRetriever."""
    return HybridRetriever()


@pytest.mark.parametrize(
    ("indic_query", "expected_lang", "expected_code"),
    [
        ("सौर पैनल और फोटोवोल्टिक मॉड्यूल 500 वाट", "hi", "IS 14286"),
        ("टीएमटी सरिया Fe 500D", "hi", "IS 1786"),
        ("மின் விநியோக மின்மாற்றி 11kV", "ta", "IS 1180"),
        ("অগ্নি নির্বাপক সিলিন্ডার এবিসি টাইপ", "bn", "IS 15683"),
    ],
)
def test_runtime_indic_query_resolution(
    processor: MultilingualProcessor,
    retriever: HybridRetriever,
    indic_query: str,
    expected_lang: str,
    expected_code: str,
) -> None:
    """Test Indic queries in Hindi, Tamil, and Bengali map to correct Indian Standards."""
    expanded_query, detected_lang = processor.translate_and_expand(indic_query)
    assert detected_lang == expected_lang
    assert len(expanded_query) > 0

    results = retriever.search(query=expanded_query, top_k=3)
    assert len(results) > 0
    top_standard, score, _ = results[0]
    assert isinstance(top_standard, IndianStandard)
    assert expected_code in top_standard.is_code
    assert score > 0.40
