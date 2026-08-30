"""Unit tests for normative resolver and supersession checks."""
from __future__ import annotations

from backend.engine.normative_resolver import NormativeResolver
from backend.ingestion.standards_loader import StandardsLoader


def test_resolve_allied_and_deprecation() -> None:
    """Test resolving normative references, test methods, and deprecation."""
    loader = StandardsLoader()
    resolver = NormativeResolver(loader=loader)

    std_concrete = loader.get_by_code("IS 456")
    assert std_concrete is not None

    allied = resolver.resolve_allied(std_concrete)
    assert len(allied) > 0
    types = [a.relation_type for a in allied]
    assert "Normative Reference" in types
    assert "Test Method" in types

    std_old = loader.get_by_code("IS 1786:1985")
    if std_old:
        warning = resolver.check_deprecation(std_old)
        assert warning is not None
        assert "SUPERSEDED" in warning
