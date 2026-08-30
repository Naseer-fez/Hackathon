"""Unified LLM service layer with provider factory, singleton caching, and domain reasoning."""
from __future__ import annotations
import threading
from typing import Any
from backend.config.settings import app_settings
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_providers import DeterministicFallbackProvider, GeminiLlmProvider, LocalGgufLlmProvider, OpenAiLlmProvider
from backend.logger.app_logger import get_logger
from backend.models.standard_model import IndianStandard

logger = get_logger("engine.llm_service")
_PROVIDER_CACHE: dict[str, BaseLlmProvider] = {}
_CACHE_LOCK = threading.RLock()
_SERVICE_SINGLETON: LlmService | None = None


def get_llm_provider(provider_type: str | None = None) -> BaseLlmProvider:
    """Factory returning persistent singleton LLM provider based on config or argument."""
    selected = (provider_type or app_settings.llm.provider).lower()
    with _CACHE_LOCK:
        if selected not in _PROVIDER_CACHE:
            if selected in ("local_gguf", "gguf", "local"):
                _PROVIDER_CACHE[selected] = LocalGgufLlmProvider()
            elif selected == "gemini":
                _PROVIDER_CACHE[selected] = GeminiLlmProvider()
            elif selected == "openai":
                _PROVIDER_CACHE[selected] = OpenAiLlmProvider()
            elif selected == "ollama":
                _PROVIDER_CACHE[selected] = OpenAiLlmProvider(base_url="http://localhost:11434/v1")
            else:
                _PROVIDER_CACHE[selected] = DeterministicFallbackProvider()
        return _PROVIDER_CACHE[selected]


def get_llm_service() -> LlmService:
    """Return persistent singleton LlmService instance."""
    global _SERVICE_SINGLETON
    if _SERVICE_SINGLETON is None:
        with _CACHE_LOCK:
            if _SERVICE_SINGLETON is None:
                _SERVICE_SINGLETON = LlmService()
    return _SERVICE_SINGLETON


def _format_chunk_context(chunks: list[Any] | None) -> str:
    if not chunks:
        return ""
    lines = ["\nRelevant Technical Document Excerpts (PDF Chunks):"]
    for c in chunks[:3]:
        fn = getattr(c, "file_name", None) or (c.get("file_name") if isinstance(c, dict) else "Doc")
        pg = getattr(c, "page_number", None) or (c.get("page_number") if isinstance(c, dict) else 1)
        snip = (getattr(c, "snippet", None) or (c.get("snippet") if isinstance(c, dict) else ""))[:200].strip()
        lines.append(f"- [Source: {fn}, Page {pg}]: {snip}")
    return "\n".join(lines)


class LlmService:
    """High-level LLM orchestration service for procurement intelligence."""

    def __init__(self, provider: BaseLlmProvider | None = None) -> None:
        self._provider = provider if provider is not None else get_llm_provider()

    async def explain_recommendation(self, query: str, standard: IndianStandard, qco_alert: str, document_chunks: list[Any] | None = None) -> str:
        logger.info(f"LlmService: Explaining {standard.is_code} using {self._provider.__class__.__name__}")
        chunk_ctx = _format_chunk_context(document_chunks)
        sys_p = "You are a Senior BIS Procurement Technical Advisor. Cite mandatory test methods, QCOs, and PDF sources."
        user_p = (
            f"Buyer: {query}\nStandard: {standard.is_code}:{standard.year} - {standard.title}\n"
            f"Scope: {standard.scope}\nKey Parameters: {', '.join(standard.key_parameters)}\n"
            f"Test Methods: {', '.join(standard.test_methods)}\nCertification: {qco_alert}\n"
            f"{chunk_ctx}\nProvide a structured procurement committee justification."
        )
        try:
            res = await self._provider.generate_text(user_p, sys_p)
            if res and res.strip():
                return res.strip()
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning(f"LlmService: Explanation error ({type(exc).__name__}: {exc})")
        return "No LLM model is currently available to generate technical justification for this standard."

    async def answer_procurement_query(self, question: str, context_standards: list[IndianStandard], document_chunks: list[Any] | None = None) -> str:
        logger.info(f"LlmService: Answering query '{question}' with {len(context_standards)} standards")
        context_str = "\n".join(f"- {s.is_code}: {s.title}" for s in context_standards[:5])
        sys_p = "You are an AI assistant specialized in Indian Standards and GeM e-procurement."
        user_p = f"Question: {question}\n\nAvailable Standards:\n{context_str}\n{_format_chunk_context(document_chunks)}"
        try:
            res = await self._provider.generate_text(user_p, sys_p)
            if res and res.strip():
                return res.strip()
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning(f"LlmService: Query answer error ({type(exc).__name__}: {exc})")
        return "No LLM model is currently available to answer this query. Please check model status."
