"""Unit tests for specification extractor."""
from __future__ import annotations

from backend.parsers.spec_extractor import SpecExtractor


def test_spec_extractor_line_items_and_citations() -> None:
    """Test extracting cited IS codes and identifying compliance issues."""
    extractor = SpecExtractor()
    sample_text = (
        "Item 1: Supply of TMT Steel bars according to IS 1786:1985 for building foundation.\n\n"
        "Item 2: Supply of LED street lighting fixtures 120W without specification."
    )

    items = extractor.split_into_items(sample_text)
    assert len(items) == 2
    assert "IS 1786:1985" in items[0].cited_standards
    assert len(items[0].outdated_citations) > 0

    issues = extractor.identify_compliance_issues(items)
    assert len(issues) >= 2
    severities = [i.severity for i in issues]
    assert "HIGH" in severities
    assert "MEDIUM" in severities
