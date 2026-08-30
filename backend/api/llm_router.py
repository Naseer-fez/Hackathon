"""Router for LLM reasoning, explanation, and interactive Q&A with grounded PDF evidence."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.engine.certification_advisor import CertificationAdvisor
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.llm_service import get_llm_service
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.recommendation_model import DocumentChunkEvidence

router = APIRouter(prefix="/api/v1", tags=["llm_assistant"])
loader = StandardsLoader()
advisor = CertificationAdvisor()
retriever = HybridRetriever()
llm_service = get_llm_service()


class ExplainStandardRequest(BaseModel):
    query: str
    is_code: str


class AssistantQuestionRequest(BaseModel):
    question: str


class LlmExplanationResponse(BaseModel):
    is_code: str
    explanation: str
    document_evidences: list[DocumentChunkEvidence] = Field(default_factory=list)


class AssistantAnswerResponse(BaseModel):
    question: str
    answer: str
    document_evidences: list[DocumentChunkEvidence] = Field(default_factory=list)


@router.post("/explain-standard", response_model=LlmExplanationResponse)
async def explain_standard(req: ExplainStandardRequest) -> LlmExplanationResponse:
    """Generate LLM technical justification grounded in macro standard specs and micro PDF chunks."""
    std = loader.get_by_code(req.is_code)
    if not std:
        matches = retriever.search(query=req.is_code, top_k=1)
        if matches:
            std = matches[0][0]
    if not std:
        raise HTTPException(status_code=404, detail=f"Standard '{req.is_code}' not found")

    alert = advisor.get_certification_alert(std)
    evidences = retriever.search_document_evidence(query=f"{req.is_code} {req.query}", top_k=3)
    explanation = await llm_service.explain_recommendation(
        query=req.query, standard=std, qco_alert=alert, document_chunks=evidences
    )
    return LlmExplanationResponse(is_code=std.is_code, explanation=explanation, document_evidences=evidences)


@router.post("/ask-assistant", response_model=AssistantAnswerResponse)
async def ask_assistant(req: AssistantQuestionRequest) -> AssistantAnswerResponse:
    """Ask conversational questions grounded in Indian Standards and exact PDF page excerpts."""
    matches, evidences = retriever.search_with_evidence(query=req.question, top_k=5, top_k_chunks=3)
    standards = [m[0] for m in matches] if matches else loader.get_all_standards()[:5]
    answer = await llm_service.answer_procurement_query(
        question=req.question, context_standards=standards, document_chunks=evidences
    )
    return AssistantAnswerResponse(question=req.question, answer=answer, document_evidences=evidences)


