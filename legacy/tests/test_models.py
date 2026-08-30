"""Unit tests for Pydantic data models."""
from __future__ import annotations

from backend.models.recommendation_model import RecommendationRequest, RecommendationResponse
from backend.models.standard_model import CertificationScheme, IndianStandard, MandatoryQCO, StandardStatus
from backend.models.tender_model import ComplianceIssue, ExtractedLineItem, TenderAnalysisReport


def test_indian_standard_model_validation() -> None:
    """Test validation of IndianStandard model."""
    std = IndianStandard(
        is_code="IS 456",
        title="Plain and Reinforced Concrete",
        division="CED",
        year=2000,
        scope="Structural concrete code",
        mandatory_qco=MandatoryQCO(
            is_mandatory=False, scheme=CertificationScheme.NONE
        ),
    )
    assert std.is_code == "IS 456"
    assert std.status == StandardStatus.ACTIVE


def test_recommendation_models() -> None:
    """Test Recommendation request and response models."""
    req = RecommendationRequest(query="Solar PV", top_k=3)
    assert req.query == "Solar PV"
    assert req.top_k == 3

    res = RecommendationResponse(
        query="Solar PV",
        detected_language="en",
        translated_query="Solar PV",
        total_matches=0,
    )
    assert res.detected_language == "en"
