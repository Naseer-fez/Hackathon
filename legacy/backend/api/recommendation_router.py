"""Router for AI standard recommendations and search queries."""
from __future__ import annotations

import time
from fastapi import APIRouter
from backend.engine.certification_advisor import CertificationAdvisor
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.multilingual_processor import MultilingualProcessor
from backend.engine.normative_resolver import NormativeResolver
from backend.engine.tender_clause_generator import TenderClauseGenerator
from backend.models.recommendation_model import (
    RecommendationRequest,
    RecommendationResponse,
    StandardRecommendation,
)

router = APIRouter(prefix="/api/v1", tags=["recommendations"])

multilingual_proc = MultilingualProcessor()
retriever = HybridRetriever()
resolver = NormativeResolver()
cert_advisor = CertificationAdvisor()
clause_gen = TenderClauseGenerator()


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(req: RecommendationRequest) -> RecommendationResponse:
    """Recommend most relevant Indian Standards and allied standards."""
    start_time = time.perf_counter()

    expanded_query, detected_lang = multilingual_proc.translate_and_expand(
        req.query
    )
    raw_matches = retriever.search(
        query=expanded_query, division=req.division, top_k=req.top_k
    )

    recommendations: list[StandardRecommendation] = []
    for std, score, reasons in raw_matches:
        allied = resolver.resolve_allied(std) if req.include_allied else []
        dep_warning = resolver.check_deprecation(std)
        cert_alert = cert_advisor.get_certification_alert(std)
        clause = clause_gen.generate_clause(std)

        recommendations.append(
            StandardRecommendation(
                standard=std,
                relevance_score=round(score, 4),
                match_reasons=reasons,
                allied_standards=allied,
                certification_alert=cert_alert,
                deprecation_warning=dep_warning,
                sample_tender_clause=clause,
            )
        )

    elapsed = (time.perf_counter() - start_time) * 1000.0

    return RecommendationResponse(
        query=req.query,
        detected_language=detected_lang,
        translated_query=expanded_query,
        total_matches=len(recommendations),
        recommendations=recommendations,
        latency_ms=round(elapsed, 2),
    )
