"""Unified LLM service layer with provider factory, singleton caching, and domain reasoning."""
from __future__ import annotations
import threading
from typing import Any, AsyncGenerator
from backend.config.settings import app_settings
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_providers import (
    DeterministicFallbackProvider, GeminiLlmProvider, LocalGgufLlmProvider, OpenAiLlmProvider, OpenRouterLlmProvider
)
from backend.engine.prompts import (
    MASTER_SYSTEM_PROMPT, format_chunk_excerpts, format_evaluation_prompt,
    format_tender_clause_prompt, format_testing_matrix_prompt
)
from backend.logger.app_logger import get_logger
from backend.models.standard_model import IndianStandard

logger = get_logger("engine.llm_service")
_CACHE: dict[str, BaseLlmProvider] = {}
_LOCK = threading.RLock()
_SERVICE: LlmService | None = None
_format_chunk_context = format_chunk_excerpts


def get_llm_provider(provider_type: str | None = None) -> BaseLlmProvider:
    """Factory returning persistent singleton LLM provider based on config or argument."""
    sel = (provider_type or app_settings.llm.provider).lower()
    with _LOCK:
        if sel not in _CACHE:
            if sel in ("local_gguf", "gguf", "local"):
                _CACHE[sel] = LocalGgufLlmProvider()
            elif sel in ("openrouter", "open_router"):
                _CACHE[sel] = OpenRouterLlmProvider()
            elif sel == "gemini":
                _CACHE[sel] = GeminiLlmProvider()
            elif sel == "openai":
                _CACHE[sel] = OpenAiLlmProvider()
            elif sel == "ollama":
                _CACHE[sel] = OpenAiLlmProvider(base_url="http://localhost:11434/v1")
            else:
                _CACHE[sel] = DeterministicFallbackProvider()
        return _CACHE[sel]


def get_llm_service() -> LlmService:
    """Return persistent singleton LlmService instance."""
    global _SERVICE
    if _SERVICE is None:
        with _LOCK:
            if _SERVICE is None:
                _SERVICE = LlmService()
    return _SERVICE


class LlmService:
    """High-level LLM orchestration service for procurement intelligence."""

    def __init__(self, provider: BaseLlmProvider | None = None) -> None:
        self._provider = provider if provider is not None else get_llm_provider()

    async def explain_recommendation(self, query: str, standard: IndianStandard, qco_alert: str, document_chunks: list[Any] | None = None, **kwargs: Any) -> str:
        user_p = format_evaluation_prompt(query=query, standard=standard, qco_alert=qco_alert, document_chunks=document_chunks, **kwargs)
        try:
            res = await self._provider.generate_text(user_p, MASTER_SYSTEM_PROMPT)
            if res and res.strip():
                return res.strip()
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning(f"LlmService: Explanation error ({type(exc).__name__}: {exc})")
        return "No LLM model is currently available to generate technical justification for this standard."

    async def generate_testing_matrix(self, query: str, standard: IndianStandard, qco_alert: str, document_chunks: list[Any] | None = None, **kwargs: Any) -> str:
        user_p = format_testing_matrix_prompt(query=query, standard=standard, qco_alert=qco_alert, document_chunks=document_chunks, **kwargs)
        try:
            res = await self._provider.generate_text(user_p, MASTER_SYSTEM_PROMPT)
            if res and res.strip():
                return res.strip()
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning(f"LlmService: Testing matrix error ({type(exc).__name__}: {exc})")
        return "No LLM model is currently available to generate testing matrix for this standard."

    async def generate_tender_clauses(self, query: str, standard: IndianStandard, qco_alert: str, document_chunks: list[Any] | None = None, **kwargs: Any) -> str:
        user_p = format_tender_clause_prompt(query=query, standard=standard, qco_alert=qco_alert, document_chunks=document_chunks, **kwargs)
        try:
            res = await self._provider.generate_text(user_p, MASTER_SYSTEM_PROMPT)
            if res and res.strip():
                return res.strip()
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning(f"LlmService: Tender clause error ({type(exc).__name__}: {exc})")
        return "No LLM model is currently available to generate tender clauses for this standard."

    async def explain_recommendation_stream(self, query: str, standard: IndianStandard, qco_alert: str, document_chunks: list[Any] | None = None, **kwargs: Any) -> AsyncGenerator[str, None]:
        user_p = format_evaluation_prompt(query=query, standard=standard, qco_alert=qco_alert, document_chunks=document_chunks, **kwargs)
        try:
            async for chunk in self._provider.generate_text_stream(user_p, MASTER_SYSTEM_PROMPT):
                yield chunk
        except (ValueError, RuntimeError, OSError, Exception) as exc:
            logger.warning(f"LlmService: Stream error ({type(exc).__name__}: {exc})")
            yield "\n[Stream Interrupted]"

    async def answer_procurement_query(self, question: str, context_standards: list[IndianStandard], document_chunks: list[Any] | None = None) -> str:
        c_str = "\n".join(f"- {s.is_code}: {s.title}" for s in context_standards[:5])
        user_p = f"Procurement Query: {question}\n\nAvailable Standards:\n{c_str}\n\nDocument Excerpts:\n{format_chunk_excerpts(document_chunks)}"
        try:
            res = await self._provider.generate_text(user_p, MASTER_SYSTEM_PROMPT)
            if res and res.strip():
                return res.strip()
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning(f"LlmService: Query error ({type(exc).__name__}: {exc})")
        return "No LLM model is currently available to answer this query. Please check model status."

    async def answer_procurement_query_stream(self, question: str, context_standards: list[IndianStandard], document_chunks: list[Any] | None = None) -> AsyncGenerator[str, None]:
        c_str = "\n".join(f"- {s.is_code}: {s.title}" for s in context_standards[:5])
        user_p = f"Procurement Query: {question}\n\nAvailable Standards:\n{c_str}\n\nDocument Excerpts:\n{format_chunk_excerpts(document_chunks)}"
        try:
            async for chunk in self._provider.generate_text_stream(user_p, MASTER_SYSTEM_PROMPT):
                yield chunk
        except (ValueError, RuntimeError, OSError, Exception) as exc:
            logger.warning(f"LlmService: Stream query error ({type(exc).__name__}: {exc})")
            yield "\n[Stream Interrupted]"
