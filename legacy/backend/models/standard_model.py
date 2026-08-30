"""Data models for Indian Standards and Quality Control Orders."""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class StandardStatus(str, Enum):
    """Status of an Indian Standard."""
    ACTIVE = "Active"
    SUPERSEDED = "Superseded"
    WITHDRAWN = "Withdrawn"


class CertificationScheme(str, Enum):
    """Certification schemes under Indian Law."""
    ISI_MARK = "ISI Mark (Scheme I)"
    CRS = "Compulsory Registration Scheme (CRS)"
    BEE_STAR = "BEE Star Rating"
    HALLMARKING = "Hallmarking"
    NONE = "Voluntary"


class MandatoryQCO(BaseModel):
    """Details of mandatory Quality Control Order."""
    is_mandatory: bool = False
    scheme: CertificationScheme = CertificationScheme.NONE
    order_number: str = ""
    issuing_ministry: str = ""
    effective_date: str = ""
    clause_requirement: str = ""


class IndianStandard(BaseModel):
    """Official Indian Standard specification."""
    is_code: str
    title: str
    division: str
    status: StandardStatus = StandardStatus.ACTIVE
    superseded_by: str | None = None
    year: int
    reaffirmation_year: int | None = None
    amendments: list[str] = Field(default_factory=list)
    scope: str
    key_parameters: list[str] = Field(default_factory=list)
    test_methods: list[str] = Field(default_factory=list)
    normative_references: list[str] = Field(default_factory=list)
    safety_standards: list[str] = Field(default_factory=list)
    installation_standards: list[str] = Field(default_factory=list)
    mandatory_qco: MandatoryQCO = Field(default_factory=MandatoryQCO)
    category_keywords: list[str] = Field(default_factory=list)
    gem_categories: list[str] = Field(default_factory=list)
