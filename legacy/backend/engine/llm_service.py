"""Unified LLM service layer with provider factory and domain reasoning."""
from __future__ import annotations

from backend.config.settings import app_settings
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_providers import (
    DeterministicFallbackProvider,
    GeminiLlmProvider,
    LocalGgufLlmProvider,
    OpenAiLlmProvider,
)
from backend.models.standard_model import IndianStandard


def get_llm_provider(provider_type: str | None = None) -> BaseLlmProvider:
    """Factory creating appropriate LLM provider based on config or argument."""
    selected = (provider_type or app_settings.llm.provider).lower()
    if selected in ("local_gguf", "gguf", "local"):
        return LocalGgufLlmProvider()
    if selected == "gemini":
        return GeminiLlmProvider()
    if selected == "openai":
        return OpenAiLlmProvider()
    if selected == "ollama":
        return OpenAiLlmProvider(base_url="http://localhost:11434/v1")
    return DeterministicFallbackProvider()


class LlmService:
    """High-level LLM orchestration service for procurement intelligence."""

    def __init__(self, provider: BaseLlmProvider | None = None) -> None:
        self._provider = provider or get_llm_provider()

    async def explain_recommendation(
        self, query: str, standard: IndianStandard, qco_alert: str
    ) -> str:
        """Generate detailed technical justification for recommended standard."""
        system_prompt = (
            "You are a Senior BIS Procurement Technical Advisor. "
            "Explain why the recommended Indian Standard fits the product requirement, "
            "highlight mandatory testing methods, and cite Quality Control Orders."
        )
        user_prompt = (
            f"Buyer Product Description: {query}\n"
            f"Recommended Standard: {standard.is_code}:{standard.year} - {standard.title}\n"
            f"Scope: {standard.scope}\n"
            f"Key Parameters: {', '.join(standard.key_parameters)}\n"
            f"Test Methods: {', '.join(standard.test_methods)}\n"
            f"Certification Advisory: {qco_alert}\n\n"
            "Please provide a structured, professional justification for the procurement committee."
        )
        return await self._provider.generate_text(user_prompt, system_prompt)

    async def answer_procurement_query(
        self, question: str, context_standards: list[IndianStandard]
    ) -> str:
        """Answer general natural language questions about Indian Standards."""
        context_str = "\n".join(
            f"- {s.is_code}: {s.title} (Status: {s.status.value}, QCO: {s.mandatory_qco.is_mandatory})"
            for s in context_standards[:5]
        )
        system_prompt = "You are an AI assistant specialized in Indian Standards and GeM e-procurement."
        user_prompt = f"Question: {question}\n\nAvailable Standards Context:\n{context_str}"
        return await self._provider.generate_text(user_prompt, system_prompt)
