"""Runtime test for LLM Dual-Index context grounding, streaming, and contracts."""
from __future__ import annotations
from typing import AsyncGenerator
import pytest
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_orchestrator import LlmOrchestrator
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.llm_contracts import LlmInputContract, LlmStandardizedResponse


class GroundedVerificationProvider(BaseLlmProvider):
    """Provider validating that actual document excerpts and standards are injected."""

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        assert "IS 1786" in prompt or "Steel" in prompt
        return "Grounded Justification: IS 1786:2008 conforms to structural RCC requirements with Fe 500D."

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        yield "Grounded Justification: IS 1786:2008 conforms to structural RCC requirements."


@pytest.mark.asyncio
async def test_runtime_llm_orchestrator_grounding_and_contracts() -> None:
    """Test LlmOrchestrator producing structured contracts grounded in real standard metadata."""
    loader = StandardsLoader()
    std = loader.get_by_code("IS 1786")
    assert std is not None

    contract = LlmInputContract(
        query="Fe 500D TMT Rebar for Highway Bridge Construction",
        extracted_text="High tensile rebar Fe 500D for prestressed and reinforced concrete",
        candidate_standards=[std],
        document_chunks=[{
            "file_name": "IS_1786_2008.pdf",
            "page_number": 6,
            "snippet": "0.2 percent proof stress minimum 500.0 N/mm2; elongation minimum 16.0 percent.",
        }],
        qco_alert="Mandatory ISI Mark Certification (Ministry of Steel)",
    )

    orchestrator = LlmOrchestrator(cloud=GroundedVerificationProvider(), local=GroundedVerificationProvider())
    response = await orchestrator.execute(contract)

    assert isinstance(response, LlmStandardizedResponse)
    assert response.primary_is_code == "IS 1786"
    assert response.source_tier == "cloud"
    assert "IS 1786" in response.technical_justification
    assert len(response.mandatory_test_methods) > 0
    assert len(response.cited_clauses) > 0
    assert "IS_1786_2008.pdf" in response.cited_clauses[0]
    assert response.confidence_score > 0.90
