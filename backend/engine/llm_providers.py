"""Concrete LLM providers for Google Gemini, OpenAI, OpenRouter, and Fallback synthesis."""
from __future__ import annotations

import os
import json
from typing import Any, AsyncGenerator
import httpx
from backend.config.settings import app_settings
from backend.engine.llm_interface import BaseLlmProvider


class UnavailableLlmProvider(BaseLlmProvider):
    """Truthful provider indicating that no AI/LLM model is currently active."""

    async def generate_text(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> str:
        return "No LLM model is currently available. Please configure Cloud API credentials (OPENROUTER_API_KEY/GEMINI_API_KEY) or start a local AI runtime."

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> AsyncGenerator[str, None]:
        msg = await self.generate_text(prompt, system_prompt)
        for i in range(0, len(msg), 5):
            yield msg[i:i+5]


DeterministicFallbackProvider = UnavailableLlmProvider


class GeminiLlmProvider(BaseLlmProvider):
    """Google Gemini API provider using asynchronous REST endpoints."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or os.getenv(app_settings.llm.api_key_env_var, "")
        self._model = model or app_settings.llm.model_name
        self._fallback = DeterministicFallbackProvider()

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
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
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (httpx.HTTPError, KeyError, IndexError, OSError):
            pass
        return await self._fallback.generate_text(prompt, system_prompt)

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        if not self._api_key:
            async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk
            return
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:streamGenerateContent?key={self._api_key}&alt=sse"
        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt or ''}\n\nUser Query: {prompt}"}]}],
            "generationConfig": {"temperature": app_settings.llm.temperature, "maxOutputTokens": app_settings.llm.max_tokens},
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                async with client.stream("POST", url, json=payload) as res:
                    if res.status_code != 200:
                        async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk
                        return
                    async for line in res.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str:
                                try:
                                    data = json.loads(data_str)
                                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                                    yield text
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    pass
        except Exception:
            async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk


class OpenAiLlmProvider(BaseLlmProvider):
    """OpenAI / Ollama compatible chat completions provider."""

    def __init__(self, base_url: str = "https://api.openai.com/v1", api_key: str | None = None) -> None:
        self._base_url = base_url
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._fallback = DeterministicFallbackProvider()

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        if not self._api_key and "openai" in self._base_url:
            return await self._fallback.generate_text(prompt, system_prompt)
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        msgs = [{"role": "system", "content": system_prompt or "You are an expert BIS procurement advisor."}, {"role": "user", "content": prompt}]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(f"{self._base_url}/chat/completions", headers=headers, json={"model": app_settings.llm.model_name, "messages": msgs})
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, OSError):
            pass
        return await self._fallback.generate_text(prompt, system_prompt)

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        if not self._api_key and "openai" in self._base_url:
            async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk
            return
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        msgs = [{"role": "system", "content": system_prompt or "You are an expert BIS procurement advisor."}, {"role": "user", "content": prompt}]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                async with client.stream("POST", f"{self._base_url}/chat/completions", headers=headers, json={"model": app_settings.llm.model_name, "messages": msgs, "stream": True}) as res:
                    if res.status_code != 200:
                        async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk
                        return
                    async for line in res.aiter_lines():
                        if line.startswith("data: ") and line.strip() != "data: [DONE]":
                            data_str = line[6:].strip()
                            if data_str:
                                try:
                                    data = json.loads(data_str)
                                    delta = data["choices"][0].get("delta", {}).get("content", "")
                                    if delta: yield delta
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    pass
        except Exception:
            async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk


class OpenRouterLlmProvider(BaseLlmProvider):
    """OpenRouter Cloud LLM provider using OpenAI-compatible API with model routing."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str = "https://openrouter.ai/api/v1") -> None:
        self._base_url = base_url
        self._api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self._model = model or app_settings.llm.model_name
        self._fallback = DeterministicFallbackProvider()

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        if not self._api_key:
            return await self._fallback.generate_text(prompt, system_prompt)
        headers = {"Authorization": f"Bearer {self._api_key}", "HTTP-Referer": "https://bis.gov.in", "X-Title": "BIS-SpecAI"}
        msgs = [{"role": "system", "content": system_prompt or "You are an expert BIS procurement advisor."}, {"role": "user", "content": prompt}]
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(f"{self._base_url}/chat/completions", headers=headers, json={"model": self._model, "messages": msgs, "temperature": app_settings.llm.temperature})
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, OSError):
            pass
        return await self._fallback.generate_text(prompt, system_prompt)

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        if not self._api_key:
            async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk
            return
        headers = {"Authorization": f"Bearer {self._api_key}", "HTTP-Referer": "https://bis.gov.in", "X-Title": "BIS-SpecAI"}
        msgs = [{"role": "system", "content": system_prompt or "You are an expert BIS procurement advisor."}, {"role": "user", "content": prompt}]
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                async with client.stream("POST", f"{self._base_url}/chat/completions", headers=headers, json={"model": self._model, "messages": msgs, "temperature": app_settings.llm.temperature, "stream": True}) as res:
                    if res.status_code != 200:
                        async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk
                        return
                    async for line in res.aiter_lines():
                        if line.startswith("data: ") and line.strip() != "data: [DONE]":
                            data_str = line[6:].strip()
                            if data_str:
                                try:
                                    data = json.loads(data_str)
                                    delta = data["choices"][0].get("delta", {}).get("content", "")
                                    if delta: yield delta
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    pass
        except Exception:
            async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk


class RemoteMacLlmProvider(BaseLlmProvider):
    """Remote Mac LLM Provider for distributed reasoning."""

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint or app_settings.distributed_reasoning.mac_endpoint
        self._fallback = DeterministicFallbackProvider()

    async def generate_text(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> str:
        payload = {"prompt": prompt, "system_prompt": system_prompt or ""}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(self._endpoint, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    # Expecting {"response": "..."} or similar, falling back to raw text if it's not JSON dict
                    if isinstance(data, dict) and "response" in data:
                        return data["response"]
                    elif isinstance(data, dict) and "content" in data:
                        return data["content"]
                    return res.text
        except (httpx.HTTPError, KeyError, IndexError, OSError):
            pass
        return await self._fallback.generate_text(prompt, system_prompt)

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> AsyncGenerator[str, None]:
        payload = {"prompt": prompt, "system_prompt": system_prompt or "", "stream": True}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", self._endpoint, json=payload) as res:
                    if res.status_code != 200:
                        async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk
                        return
                    async for line in res.aiter_lines():
                        if line:
                            yield line + "\n"
        except Exception:
            async for chunk in self._fallback.generate_text_stream(prompt, system_prompt): yield chunk


from backend.engine.local_gguf_provider import LocalGgufLlmProvider

__all__ = ["UnavailableLlmProvider", "DeterministicFallbackProvider", "GeminiLlmProvider", "OpenAiLlmProvider", "OpenRouterLlmProvider", "LocalGgufLlmProvider", "RemoteMacLlmProvider"]

