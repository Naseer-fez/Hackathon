"""Router for LLM reasoning, explanation, and interactive Q&A with grounded PDF evidence."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from backend.engine.certification_advisor import CertificationAdvisor
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.llm_service import get_llm_service
from backend.engine.local_gguf_provider import BackpressureError
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


class ChatMessage(BaseModel):
    role: str
    content: str


class AssistantQuestionRequest(BaseModel):
    question: str
    pdf_text: str | None = None
    chat_history: list[ChatMessage] | None = None


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
    try:
        explanation = await llm_service.explain_recommendation(
            query=req.query, standard=std, qco_alert=alert, document_chunks=evidences
        )
    except BackpressureError:
        raise HTTPException(status_code=429, detail="Server busy. Please retry.")
    return LlmExplanationResponse(is_code=std.is_code, explanation=explanation, document_evidences=evidences)


@router.post("/explain-standard-stream")
async def explain_standard_stream(req: ExplainStandardRequest) -> StreamingResponse:
    """Stream LLM technical justification via SSE."""
    std = loader.get_by_code(req.is_code)
    if not std:
        matches = retriever.search(query=req.is_code, top_k=1)
        if matches: std = matches[0][0]
    if not std: raise HTTPException(status_code=404, detail="Standard not found")

    alert = advisor.get_certification_alert(std)
    evidences = retriever.search_document_evidence(query=f"{req.is_code} {req.query}", top_k=3)

    async def stream_generator():
        try:
            async for chunk in llm_service.explain_recommendation_stream(
                query=req.query, standard=std, qco_alert=alert, document_chunks=evidences
            ):
                yield f"data: {chunk}\n\n"
        except BackpressureError:
            yield f"data: [ERROR: Server busy. Please retry.]\n\n"
        except (ValueError, RuntimeError, OSError, Exception) as exc:
            yield f"data: [ERROR: {type(exc).__name__}]\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/ask-assistant", response_model=AssistantAnswerResponse)
async def ask_assistant(req: AssistantQuestionRequest) -> AssistantAnswerResponse:
    """Ask conversational questions grounded in Indian Standards and exact PDF page excerpts."""
    matches, evidences = retriever.search_with_evidence(query=req.question, top_k=5, top_k_chunks=3)
    standards = [m[0] for m in matches] if matches else loader.get_all_standards()[:5]
    try:
        answer = await llm_service.answer_procurement_query(
            question=req.question, context_standards=standards, document_chunks=evidences, pdf_text=req.pdf_text, chat_history=req.chat_history
        )
    except BackpressureError:
        raise HTTPException(status_code=429, detail="Server busy. Please retry.")
    return AssistantAnswerResponse(question=req.question, answer=answer, document_evidences=evidences)


@router.post("/ask-assistant-stream")
async def ask_assistant_stream(req: AssistantQuestionRequest) -> StreamingResponse:
    """Stream conversational answer grounded in IS."""
    matches, evidences = retriever.search_with_evidence(query=req.question, top_k=5, top_k_chunks=3)
    standards = [m[0] for m in matches] if matches else loader.get_all_standards()[:5]

    async def stream_generator():
        try:
            async for chunk in llm_service.answer_procurement_query_stream(
                question=req.question, context_standards=standards, document_chunks=evidences, pdf_text=req.pdf_text, chat_history=req.chat_history
            ):
                yield f"data: {chunk}\n\n"
        except BackpressureError:
            yield f"data: [ERROR: Server busy. Please retry.]\n\n"
        except (ValueError, RuntimeError, OSError, Exception) as exc:
            yield f"data: [ERROR: {type(exc).__name__}]\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

