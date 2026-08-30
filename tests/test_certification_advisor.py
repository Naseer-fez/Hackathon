"""Unit tests for certification advisor and QCO compliance."""
from __future__ import annotations

from backend.engine.certification_advisor import CertificationAdvisor
from backend.ingestion.qco_registry import QcoRegistry
from backend.ingestion.standards_loader import StandardsLoader


def test_certification_alert_mandatory_and_voluntary() -> None:
    """Test mandatory ISI/CRS alerts and voluntary standards."""
    loader = StandardsLoader()
    qco_reg = QcoRegistry()
    advisor = CertificationAdvisor(qco_reg=qco_reg)

    std_tmt = loader.get_by_code("IS 1786")
    assert std_tmt is not None
    alert_tmt = advisor.get_certification_alert(std_tmt)
    assert "MANDATORY" in alert_tmt
    assert "ISI MARK" in alert_tmt

    std_pv = loader.get_by_code("IS 14286")
    assert std_pv is not None
    alert_pv = advisor.get_certification_alert(std_pv)
    assert "MANDATORY" in alert_pv
