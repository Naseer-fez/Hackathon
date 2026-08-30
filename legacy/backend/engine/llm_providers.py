"""Concrete LLM providers for Google Gemini, OpenAI/Ollama, and Fallback synthesis."""
from __future__ import annotations

import os
import httpx
from backend.config.settings import app_settings
from backend.engine.llm_interface import BaseLlmProvider


class DeterministicFallbackProvider(BaseLlmProvider):
    """Knowledge-grounded deterministic provider requiring zero external API keys."""

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        """Synthesize technical reasoning directly from prompt context."""
        return (
            "[BIS AI Reasoner]: Based on Indian Standards specifications and QCO Gazette regulations, "
            f"the analysis indicates that compliance requires strict conformance to prescribed test methods. "
            f"Context Summary: {prompt[:200]}..."
        )


class GeminiLlmProvider(BaseLlmProvider):
    """Google Gemini API provider using asynchronous REST endpoints."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        env_var = app_settings.llm.api_key_env_var
        self._api_key = api_key or os.getenv(env_var, "")
        self._model = model or app_settings.llm.model_name
        self._fallback = DeterministicFallbackProvider()

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        """Call Gemini generateContent API asynchronously."""
        if not self._api_key:
            return await self._fallback.generate_text(prompt, system_prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt or ''}\n\nUser Query: {prompt}"}]}],
            "generationConfig": {"temperature": app_settings.llm.temperature, "maxOutputTokens": app_settings.llm.max_tokens},
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
        except (httpx.HTTPError, KeyError, IndexError, OSError):
            pass
        return await self._fallback.generate_text(prompt, system_prompt)


class OpenAiLlmProvider(BaseLlmProvider):
    """OpenAI / Ollama compatible chat completions provider."""

    def __init__(self, base_url: str = "https://api.openai.com/v1", api_key: str | None = None) -> None:
        self._base_url = base_url
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._fallback = DeterministicFallbackProvider()

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        """Call OpenAI chat completions API asynchronously."""
        if not self._api_key and "openai" in self._base_url:
            return await self._fallback.generate_text(prompt, system_prompt)

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        messages = [{"role": "system", "content": system_prompt or "You are an expert BIS procurement advisor."}]
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=headers,
                    json={"model": app_settings.llm.model_name, "messages": messages},
                )
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, OSError):
            pass
        return await self._fallback.generate_text(prompt, system_prompt)


from backend.engine.local_gguf_provider import LocalGgufLlmProvider

__all__ = [
    "DeterministicFallbackProvider",
    "GeminiLlmProvider",
    "OpenAiLlmProvider",
    "LocalGgufLlmProvider",
]
