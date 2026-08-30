"""LLM Abstraction Orchestrator with Cloud-Primary execution and silent Local Fallback."""
from __future__ import annotations
import asyncio
from typing import Any
from backend.config.settings import app_settings
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_providers import DeterministicFallbackProvider, GeminiLlmProvider, LocalGgufLlmProvider, OpenAiLlmProvider
from backend.logger.app_logger import get_logger
from backend.models.llm_contracts import LlmInputContract, LlmStandardizedResponse

logger = get_logger("engine.llm_orchestrator")


class LlmOrchestrator:
    """Cloud-Primary LLM Router with instant failover to Local LLM / deterministic tier."""

    def __init__(
        self,
        cloud: BaseLlmProvider | None = None,
        local: BaseLlmProvider | None = None,
        timeout_sec: float = 6.0,
        cloud_provider: BaseLlmProvider | None = None,
        local_provider: BaseLlmProvider | None = None,
    ) -> None:
        c_prov = cloud or cloud_provider
        l_prov = local or local_provider
        self._cloud = c_prov or (GeminiLlmProvider() if app_settings.llm.provider == "gemini" else OpenAiLlmProvider())
        self._local = l_prov or LocalGgufLlmProvider()
        self._fallback = DeterministicFallbackProvider()
        self._timeout_sec = timeout_sec

    def _build_prompt(self, c: LlmInputContract) -> tuple[str, str]:
        sys_p = c.system_instruction or "You are a Senior BIS Procurement Technical Advisor."
        top_s = c.candidate_standards[0] if c.candidate_standards else None
        code = f"{top_s.is_code}:{top_s.year} - {top_s.title}" if top_s else "General Indian Standards"
        chunk_lines = [f"- [Source: {k.get('file_name', 'Doc')}, Page {k.get('page_number', 1)}]: {k.get('snippet', '')[:180]}" for k in c.document_chunks[:3]]
        chunk_txt = ("\nDocument Excerpts:\n" + "\n".join(chunk_lines)) if chunk_lines else ""
        user_p = (
            f"User Query: {c.query}\nSpecification: {c.extracted_text[:300]}\n"
            f"Candidate Standard: {code}\nScope: {top_s.scope if top_s else ''}\n"
            f"QCO Requirements: {c.qco_alert}{chunk_txt}\nGenerate technical justification and cite clauses."
        )
        return sys_p, user_p

    def _synthesize(self, c: LlmInputContract, raw: str, tier: str) -> LlmStandardizedResponse:
        top_s = c.candidate_standards[0] if c.candidate_standards else None
        code, title = (top_s.is_code, top_s.title) if top_s else ("IS General", "Indian Standard")
        tests = top_s.test_methods if top_s else ["Standard Conformance"]
        allied = [f"{r} (Normative Reference)" for r in top_s.normative_references] if top_s else []
        citations = [f"{k.get('file_name', 'Doc')} (Page {k.get('page_number', 1)})" for k in c.document_chunks[:3]]
        verdict = c.qco_alert or ("Mandatory ISI Mark (Scheme I)" if top_s and top_s.mandatory_qco.is_mandatory else "Voluntary Conformance")
        return LlmStandardizedResponse(
            query=c.query, primary_is_code=code, primary_title=title,
            technical_justification=raw.strip() or f"Standard {code} matches requirements for {c.query}.",
            qco_compliance_verdict=verdict, mandatory_test_methods=tests, allied_standards_summary=allied,
            cited_clauses=citations, confidence_score=0.96 if tier == "cloud" else (0.92 if tier == "local_fallback" else 0.88),
            source_tier=tier,
        )

    async def execute(self, contract: LlmInputContract) -> LlmStandardizedResponse:
        """Execute Cloud-First inference with automatic failover to Local GGUF and Deterministic tier."""
        sys_prompt, user_prompt = self._build_prompt(contract)
        try:
            logger.info(f"LLM Orchestrator: Invoking Primary Cloud LLM ({self._cloud.__class__.__name__})...")
            raw = await asyncio.wait_for(self._cloud.generate_text(user_prompt, sys_prompt), timeout=self._timeout_sec)
            if raw and len(raw.strip()) > 20:
                return self._synthesize(contract, raw, tier="cloud")
        except (asyncio.TimeoutError, OSError, ValueError, Exception) as exc:
            logger.warning(f"[FALLBACK] Cloud LLM unavailable ({type(exc).__name__}) -> Local GGUF Tier")

        try:
            logger.info(f"LLM Orchestrator: Invoking Local GGUF Provider ({self._local.__class__.__name__})...")
            local_raw = await self._local.generate_text(user_prompt, sys_prompt)
            if local_raw and len(local_raw.strip()) > 20:
                return self._synthesize(contract, local_raw, tier="local_fallback")
        except (RuntimeError, OSError, ValueError, Exception) as exc:
            logger.warning(f"[FALLBACK] Local GGUF unavailable ({type(exc).__name__}) -> Deterministic")

        top_s = contract.candidate_standards[0] if contract.candidate_standards else None
        return LlmStandardizedResponse(
            query=contract.query, primary_is_code=top_s.is_code if top_s else "IS General",
            primary_title=top_s.title if top_s else "Indian Standard",
            technical_justification="No LLM model is currently available (Cloud API not configured and Local AI runtime offline).",
            qco_compliance_verdict="Unavailable: No active LLM model to perform AI justification.",
            mandatory_test_methods=top_s.test_methods if top_s else [],
            allied_standards_summary=[f"{r} (Normative Reference)" for r in top_s.normative_references] if top_s else [],
            cited_clauses=[f"{k.get('file_name', 'Doc')} (Page {k.get('page_number', 1)})" for k in contract.document_chunks[:3]],
            confidence_score=0.0, source_tier="unavailable",
        )



