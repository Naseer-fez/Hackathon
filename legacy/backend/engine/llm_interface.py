"""Abstract interface definition for pluggable LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLlmProvider(ABC):
    """Abstract base class for all LLM providers (Gemini, OpenAI, Ollama, Fallback)."""

    @abstractmethod
    async def generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        """Generate textual completion for given prompt and system instructions."""
        raise NotImplementedError("Subclasses must implement generate_text")
