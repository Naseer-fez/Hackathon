"""Router for GeM / CPPP e-procurement webhook integration."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.normative_resolver import NormativeResolver
from backend.engine.tender_clause_generator import TenderClauseGenerator

router = APIRouter(prefix="/api/v1", tags=["gem_integration"])

retriever = HybridRetriever()
resolver = NormativeResolver()
clause_gen = TenderClauseGenerator()


class GemBidValidationRequest(BaseModel):
    """Payload sent by GeM portal during bid creation."""
    bid_id: str
    category_name: str
    product_title: str
    buyer_specifications: str


class GemBidValidationResponse(BaseModel):
    """Validation response returned to GeM portal."""
    bid_id: str
    status: str
    compliance_score: float
    primary_standard: str
    is_qco_mandatory: bool
    qco_order: str
    recommended_clause: str
    allied_standards: list[str]


@router.post("/gem-webhook", response_model=GemBidValidationResponse)
async def validate_gem_bid(req: GemBidValidationRequest) -> GemBidValidationResponse:
    """Validate a GeM bid specification against BIS and QCO regulations."""
    search_query = f"{req.category_name} {req.product_title} {req.buyer_specifications}"
    matches = retriever.search(query=search_query, top_k=1)

    if not matches:
        return GemBidValidationResponse(
            bid_id=req.bid_id,
            status="WARNING",
            compliance_score=0.5,
            primary_standard="Standard Not Found",
            is_qco_mandatory=False,
            qco_order="None",
            recommended_clause="Manual review by procurement committee advised.",
            allied_standards=[],
        )

    std, score, _ = matches[0]
    allied = resolver.resolve_allied(std)
    allied_codes = [a.is_code for a in allied]
    clause = clause_gen.generate_clause(std)

    status = "COMPLIANT" if std.mandatory_qco.is_mandatory else "VERIFIED"

    return GemBidValidationResponse(
        bid_id=req.bid_id,
        status=status,
        compliance_score=round(score, 2),
        primary_standard=f"{std.is_code}:{std.year}",
        is_qco_mandatory=std.mandatory_qco.is_mandatory,
        qco_order=std.mandatory_qco.order_number,
        recommended_clause=clause,
        allied_standards=allied_codes,
    )
