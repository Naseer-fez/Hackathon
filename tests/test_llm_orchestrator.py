"""Tests for LLM Orchestrator, Cloud-Primary execution, and silent local fallback."""
from __future__ import annotations

import pytest
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_orchestrator import LlmOrchestrator
from backend.models.llm_contracts import LlmInputContract, LlmStandardizedResponse
from backend.models.standard_model import CertificationScheme, IndianStandard, MandatoryQCO, StandardStatus


class MockCloudSuccessProvider(BaseLlmProvider):
    """Simulates successful Cloud LLM response."""
    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Cloud LLM Analysis: The recommended standard is IS 14286. Mandatory CRS applies."


class MockCloudFailingProvider(BaseLlmProvider):
    """Simulates Cloud LLM failure (rate limit, timeout, 500 error)."""
    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        raise ConnectionError("Cloud API unreachable or timed out")


class MockLocalProvider(BaseLlmProvider):
    """Simulates Local GGUF LLM inference."""
    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Local GGUF Analysis: IS 14286 applies for terrestrial PV solar modules."


@pytest.fixture
def sample_contract() -> LlmInputContract:
    """Fixture providing sample standardized LLM input contract."""
    std = IndianStandard(
        is_code="IS 14286",
        title="Crystalline Silicon Terrestrial Photovoltaic (PV) Modules",
        division="LITD",
        status=StandardStatus.ACTIVE,
        year=2010,
        amendments=["Amendment 1 (2019)"],
        scope="Design qualification and type approval for terrestrial PV modules.",
        key_parameters=["Maximum Power (Pmax)", "Open Circuit Voltage (Voc)"],
        test_methods=["Thermal Cycling Test", "Damp Heat Test"],
        normative_references=["IS 61215", "IS 61730"],
        safety_standards=["IS/IEC 61730-1"],
        installation_standards=["IS 14489"],
        mandatory_qco=MandatoryQCO(
            is_mandatory=True,
            scheme=CertificationScheme.CRS,
            order_number="MeitY Solar Photovoltaics QCO 2017",
            issuing_ministry="Ministry of New and Renewable Energy (MNRE)",
            effective_date="2018-04-16",
            clause_requirement="Bidders must possess valid BIS CRS R-number registration.",
        ),
        category_keywords=["solar panel", "pv module"],
        gem_categories=["Solar Photovoltaic Modules"],
    )
    return LlmInputContract(
        query="Solar PV Module 500W",
        extracted_text="Photovoltaic module crystalline silicon 500Wp",
        candidate_standards=[std],
        qco_alert="Mandatory CRS Registration Required",
    )


@pytest.mark.asyncio
async def test_llm_orchestrator_cloud_primary(sample_contract: LlmInputContract) -> None:
    """Test primary cloud provider generates standardized output."""
    orchestrator = LlmOrchestrator(
        cloud_provider=MockCloudSuccessProvider(),
        local_provider=MockLocalProvider(),
    )
    response = await orchestrator.execute(sample_contract)

    assert isinstance(response, LlmStandardizedResponse)
    assert response.primary_is_code == "IS 14286"
    assert response.source_tier == "cloud"
    assert "Cloud LLM Analysis" in response.technical_justification
    assert "IS 61215 (Normative Reference)" in response.allied_standards_summary


@pytest.mark.asyncio
async def test_llm_orchestrator_silent_local_fallback(sample_contract: LlmInputContract) -> None:
    """Test silent failover to local fallback when cloud encounters failure."""
    orchestrator = LlmOrchestrator(
        cloud_provider=MockCloudFailingProvider(),
        local_provider=MockLocalProvider(),
    )
    response = await orchestrator.execute(sample_contract)

    assert isinstance(response, LlmStandardizedResponse)
    assert response.primary_is_code == "IS 14286"
    assert response.source_tier == "local_fallback"
    assert "Local GGUF Analysis" in response.technical_justification
    assert len(response.mandatory_test_methods) > 0


@pytest.mark.asyncio
async def test_llm_orchestrator_unavailable_reporting(sample_contract: LlmInputContract) -> None:
    """Test faithful unavailable reporting when both cloud and local providers fail."""
    orchestrator = LlmOrchestrator(
        cloud_provider=MockCloudFailingProvider(),
        local_provider=MockCloudFailingProvider(),
    )
    response = await orchestrator.execute(sample_contract)

    assert isinstance(response, LlmStandardizedResponse)
    assert response.primary_is_code == "IS 14286"
    assert response.source_tier == "unavailable"
    assert response.confidence_score == 0.0
    assert "No LLM model is currently available" in response.technical_justification

