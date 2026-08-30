"""Router for LLM reasoning, explanation, and interactive Q&A."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.engine.certification_advisor import CertificationAdvisor
from backend.engine.llm_service import LlmService
from backend.ingestion.standards_loader import StandardsLoader

router = APIRouter(prefix="/api/v1", tags=["llm_assistant"])

loader = StandardsLoader()
advisor = CertificationAdvisor()
llm_service = LlmService()


class ExplainStandardRequest(BaseModel):
    """Payload for LLM technical justification."""
    query: str
    is_code: str


class AssistantQuestionRequest(BaseModel):
    """Payload for conversational assistant Q&A."""
    question: str


class LlmExplanationResponse(BaseModel):
    """Structured LLM technical explanation response."""
    is_code: str
    explanation: str


class AssistantAnswerResponse(BaseModel):
    """Assistant conversational answer response."""
    question: str
    answer: str


@router.post("/explain-standard", response_model=LlmExplanationResponse)
async def explain_standard(req: ExplainStandardRequest) -> LlmExplanationResponse:
    """Generate LLM-driven technical justification for a recommended standard."""
    std = loader.get_by_code(req.is_code)
    if not std:
        raise HTTPException(status_code=404, detail=f"Standard '{req.is_code}' not found")

    alert = advisor.get_certification_alert(std)
    explanation = await llm_service.explain_recommendation(
        query=req.query, standard=std, qco_alert=alert
    )
    return LlmExplanationResponse(is_code=std.is_code, explanation=explanation)


@router.post("/ask-assistant", response_model=AssistantAnswerResponse)
async def ask_assistant(req: AssistantQuestionRequest) -> AssistantAnswerResponse:
    """Ask conversational questions about Indian Standards and QCO requirements."""
    standards = loader.get_all_standards()
    answer = await llm_service.answer_procurement_query(
        question=req.question, context_standards=standards
    )
    return AssistantAnswerResponse(question=req.question, answer=answer)
