"""Runtime tests for statutory QCO compliance and normative graph resolution."""
from __future__ import annotations
import pytest
from backend.engine.certification_advisor import CertificationAdvisor
from backend.engine.normative_resolver import NormativeResolver
from backend.engine.tender_clause_generator import TenderClauseGenerator
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.standard_model import CertificationScheme, IndianStandard


@pytest.fixture(scope="module")
def loader() -> StandardsLoader:
    return StandardsLoader()


@pytest.fixture(scope="module")
def resolver() -> NormativeResolver:
    return NormativeResolver()


@pytest.fixture(scope="module")
def advisor() -> CertificationAdvisor:
    return CertificationAdvisor()


@pytest.fixture(scope="module")
def clause_gen() -> TenderClauseGenerator:
    return TenderClauseGenerator()


def test_runtime_qco_enforcement_isi_and_crs(
    loader: StandardsLoader, advisor: CertificationAdvisor
) -> None:
    """Test statutory QCO rules enforcement on actual standards database."""
    tmt = loader.get_by_code("IS 1786")
    assert tmt is not None
    assert tmt.mandatory_qco.is_mandatory is True
    assert tmt.mandatory_qco.scheme == CertificationScheme.ISI_MARK
    alert = advisor.get_certification_alert(tmt)
    assert "ISI Mark" in alert or "Scheme I" in alert

    solar = loader.get_by_code("IS 14286")
    assert solar is not None
    assert solar.mandatory_qco.is_mandatory is True
    assert solar.mandatory_qco.scheme == CertificationScheme.CRS
    solar_alert = advisor.get_certification_alert(solar)
    assert "CRS" in solar_alert or "R-number" in solar_alert or "Compulsory" in solar_alert


def test_runtime_normative_graph_and_clause_generation(
    loader: StandardsLoader, resolver: NormativeResolver, clause_gen: TenderClauseGenerator
) -> None:
    """Test normative graph resolution and GeM specification clause creation."""
    std = loader.get_by_code("IS 1786")
    assert std is not None
    allied = resolver.resolve_allied(std)
    assert len(allied) > 0
    assert any("1599" in a.is_code or "1608" in a.is_code or "228" in a.is_code for a in allied)

    clause = clause_gen.generate_clause(std)
    assert "IS 1786" in clause
    assert "BIS" in clause
    assert len(clause) > 50
