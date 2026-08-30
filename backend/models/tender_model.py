"""Data models for tender document parsing and compliance auditing."""
from __future__ import annotations

from pydantic import BaseModel, Field
from backend.models.recommendation_model import StandardRecommendation


class ExtractedLineItem(BaseModel):
    """Extracted procurement line item from tender document."""
    item_id: int
    product_title: str
    spec_summary: str
    cited_standards: list[str] = Field(default_factory=list)
    outdated_citations: list[str] = Field(default_factory=list)
    recommended_standards: list[StandardRecommendation] = Field(
        default_factory=list
    )


class ComplianceIssue(BaseModel):
    """Identified compliance or standard ambiguity issue."""
    severity: str
    category: str
    issue_text: str
    corrective_action: str


class TenderAnalysisReport(BaseModel):
    """Comprehensive compliance audit report for a tender."""
    document_name: str
    extracted_items_count: int
    items: list[ExtractedLineItem] = Field(default_factory=list)
    compliance_issues: list[ComplianceIssue] = Field(default_factory=list)
    mandatory_qco_coverage: float = 100.0
    complete_spec_clause_text: str = ""
