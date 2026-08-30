"""Unit tests for tender clause generator."""
from __future__ import annotations

from backend.engine.tender_clause_generator import TenderClauseGenerator
from backend.ingestion.standards_loader import StandardsLoader


def test_generate_clause() -> None:
    """Test generating tender specification clause with citations and testing."""
    loader = StandardsLoader()
    gen = TenderClauseGenerator()

    std = loader.get_by_code("IS 1786")
    assert std is not None

    clause = gen.generate_clause(std)
    assert "IS 1786" in clause
    assert "TECHNICAL COMPLIANCE" in clause
    assert "TESTING & QUALITY ASSURANCE" in clause
    assert "STATUTORY MANDATE" in clause
