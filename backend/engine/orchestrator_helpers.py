"""Prompt formatting and response synthesis helpers for LLM Orchestrator."""
from __future__ import annotations
from typing import Any
from backend.engine.prompts import MASTER_SYSTEM_PROMPT, format_evaluation_prompt
from backend.models.llm_contracts import LlmInputContract, LlmStandardizedResponse


def build_orchestrator_prompt(c: LlmInputContract) -> tuple[str, str]:
    """Build system and user prompt for contract evaluation."""
    sys_p = c.system_instruction or MASTER_SYSTEM_PROMPT
    top_s = c.candidate_standards[0] if c.candidate_standards else None
    user_p = format_evaluation_prompt(
        query=c.query, standard=top_s, qco_alert=c.qco_alert,
        document_chunks=c.document_chunks, image_context=c.image_context,
        detected_language=c.detected_language,
    )
    return sys_p, user_p


def synthesize_contract_response(c: LlmInputContract, raw: str, tier: str) -> LlmStandardizedResponse:
    """Synthesize raw LLM text into standardized response contract."""
    top_s = c.candidate_standards[0] if c.candidate_standards else None
    code, title = (top_s.is_code, top_s.title) if top_s else ("IS General", "Indian Standard")
    tests = top_s.test_methods if top_s else ["Standard Conformance"]
    allied = [f"{r} (Normative Reference)" for r in top_s.normative_references] if top_s else []
    citations = [f"{k.get('file_name', 'Doc')} (Page {k.get('page_number', 1)})" for k in c.document_chunks[:3]]
    verdict = c.qco_alert or (
        "Mandatory ISI Mark (Scheme I)" if top_s and top_s.mandatory_qco.is_mandatory else "Voluntary Conformance"
    )
    confidence = 0.96 if tier in ["cloud", "remote_mac"] else (0.92 if tier in ["local_fallback", "local_2b"] else 0.88)
    return LlmStandardizedResponse(
        query=c.query, primary_is_code=code, primary_title=title,
        technical_justification=raw.strip() or f"Standard {code} matches requirements for {c.query}.",
        qco_compliance_verdict=verdict, mandatory_test_methods=tests, allied_standards_summary=allied,
        cited_clauses=citations, confidence_score=confidence, source_tier=tier,
    )


def count_history_tokens(history: list[dict[str, str]]) -> int:
    """Estimate token count for a chat history list."""
    total_chars = sum(len(m.get("content", "")) + len(m.get("role", "")) for m in history)
    return max(1, total_chars // 4)
