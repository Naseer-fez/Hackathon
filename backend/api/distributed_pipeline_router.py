"""Router for distributed AI pipelines: Fast Answer (Local 2B) and Heavy Reasoning (Mac Offload)."""
from __future__ import annotations
import json
from typing import Any
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from backend.engine.llm_orchestrator import LlmOrchestrator
from backend.models.llm_contracts import PipelineAnswerResponse
from backend.parsers.pdf_markdown_parser import PdfMarkdownParser

router = APIRouter(prefix="/api/v1", tags=["distributed_reasoning"])
orchestrator = LlmOrchestrator()
pdf_parser = PdfMarkdownParser()


class SummarizeContextRequest(BaseModel):
    chat_history: list[dict[str, str]] = Field(default_factory=list)


class SummarizeContextResponse(BaseModel):
    summarized_context: str


@router.post("/fast-answer", response_model=PipelineAnswerResponse)
async def fast_answer(
    query: str = Form(...),
    pdf_text: str = Form(""),
    pdf_file: UploadFile | None = File(None),
) -> PipelineAnswerResponse:
    """Rapid low-latency answer bypassing Mac reasoning engine using local model."""
    doc_text = pdf_text
    if pdf_file is not None:
        file_bytes = await pdf_file.read()
        extracted = pdf_parser.extract_markdown_from_bytes(file_bytes)
        if extracted:
            doc_text = extracted

    return await orchestrator.execute_fast_answer(query=query, pdf_text=doc_text)


@router.post("/heavy-reasoning", response_model=PipelineAnswerResponse)
async def heavy_reasoning(
    query: str = Form(...),
    pdf_text: str = Form(""),
    chat_history: str = Form("[]"),
    refresh_context: bool = Form(False),
    pdf_file: UploadFile | None = File(None),
) -> PipelineAnswerResponse:
    """Deep-dive reasoning with local context synthesis and remote Mac offloading."""
    parsed_history: list[dict[str, str]] = []
    if chat_history:
        try:
            parsed = json.loads(chat_history)
            if isinstance(parsed, list):
                parsed_history = parsed
        except (json.JSONDecodeError, TypeError):
            parsed_history = []

    doc_text = pdf_text
    if pdf_file is not None:
        file_bytes = await pdf_file.read()
        extracted = pdf_parser.extract_markdown_from_bytes(file_bytes)
        if extracted:
            doc_text = extracted

    return await orchestrator.execute_heavy_reasoning(
        query=query,
        pdf_text=doc_text,
        chat_history=parsed_history,
        refresh_context=refresh_context,
    )


@router.post("/summarize-context", response_model=SummarizeContextResponse)
async def summarize_context(req: SummarizeContextRequest) -> SummarizeContextResponse:
    """Compress conversation history into dense summary using local model."""
    summary = await orchestrator.summarize_chat_history(req.chat_history)
    return SummarizeContextResponse(summarized_context=summary)
