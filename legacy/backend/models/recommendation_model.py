"""Data models for recommendation requests and responses."""
from __future__ import annotations

from pydantic import BaseModel, Field
from backend.models.standard_model import IndianStandard


class RecommendationRequest(BaseModel):
    """User query payload for standard recommendation."""
    query: str
    language: str | None = None
    division: str | None = None
    top_k: int = 5
    include_allied: bool = True


class AlliedStandardItem(BaseModel):
    """Allied or cross-referenced standard node."""
    is_code: str
    title: str
    relation_type: str
    status: str = "Active"
    is_mandatory: bool = False
    details: str = ""


class StandardRecommendation(BaseModel):
    """Detailed recommendation record for an Indian Standard."""
    standard: IndianStandard
    relevance_score: float
    match_reasons: list[str] = Field(default_factory=list)
    allied_standards: list[AlliedStandardItem] = Field(default_factory=list)
    certification_alert: str = ""
    deprecation_warning: str | None = None
    sample_tender_clause: str = ""


class RecommendationResponse(BaseModel):
    """Response payload containing recommendations and metadata."""
    query: str
    detected_language: str
    translated_query: str
    total_matches: int
    recommendations: list[StandardRecommendation] = Field(default_factory=list)
    latency_ms: float = 0.0
