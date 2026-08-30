"""Locked data contracts for LLM input standardization and output synthesis."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from backend.models.standard_model import IndianStandard


class LlmInputContract(BaseModel):
    """Standardized input contract feeding into the LLM Router/Orchestrator."""
    query: str
    extracted_text: str = ""
    detected_language: str = "en"
    candidate_standards: list[IndianStandard] = Field(default_factory=list)
    document_chunks: list[dict[str, Any]] = Field(default_factory=list)
    image_context: dict[str, Any] = Field(default_factory=dict)
    qco_alert: str = ""
    system_instruction: str = ""


class LlmStandardizedResponse(BaseModel):
    """Locked standardized response contract returned by Cloud LLM or Local Fallback."""
    query: str
    primary_is_code: str
    primary_title: str
    technical_justification: str
    qco_compliance_verdict: str
    mandatory_test_methods: list[str] = Field(default_factory=list)
    allied_standards_summary: list[str] = Field(default_factory=list)
    cited_clauses: list[str] = Field(default_factory=list)
    confidence_score: float = 0.95
    source_tier: str = "primary"

