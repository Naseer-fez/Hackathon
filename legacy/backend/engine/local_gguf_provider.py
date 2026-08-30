"""Local GGUF LLM provider using llama-cpp-python or local runtime with resilient fallback."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from backend.config.settings import app_settings
from backend.engine.llm_interface import BaseLlmProvider
from backend.engine.llm_providers import DeterministicFallbackProvider


class LocalGgufLlmProvider(BaseLlmProvider):
    """Local GGUF inference provider with non-blocking async execution and fallback."""

    def __init__(
        self,
        model_path: str | None = None,
        n_ctx: int | None = None,
        n_threads: int | None = None,
    ) -> None:
        self._model_path = model_path or app_settings.llm.model_path
        self._n_ctx = n_ctx or app_settings.llm.n_ctx
        self._n_threads = n_threads or app_settings.llm.n_threads
        self._model: Any = None
        self._is_offline = False
        self._fallback = DeterministicFallbackProvider()

    def _load_model(self) -> Any:
        """Attempt to load local GGUF model via llama_cpp."""
        if not Path(self._model_path).exists():
            self._is_offline = True
            return None
        try:
            from llama_cpp import Llama

            return Llama(
                model_path=self._model_path,
                n_ctx=self._n_ctx,
                n_threads=self._n_threads,
                verbose=False,
            )
        except (ImportError, OSError, ValueError, RuntimeError):
            self._is_offline = True
            return None

    def _sync_generate(self, prompt: str, system_prompt: str | None) -> str | None:
        """Synchronously execute GGUF chat completion."""
        if self._model is None and not self._is_offline:
            self._model = self._load_model()
        if self._model is None:
            return None

        sys_content = system_prompt or "You are an expert BIS procurement advisor."
        messages = [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": prompt},
        ]
        try:
            response = self._model.create_chat_completion(
                messages=messages,
                temperature=app_settings.llm.temperature,
                max_tokens=app_settings.llm.max_tokens,
            )
            choices = response.get("choices", [])
            if choices and "message" in choices[0]:
                return str(choices[0]["message"].get("content", ""))
        except (KeyError, IndexError, RuntimeError, ValueError, TypeError):
            self._is_offline = True
        return None

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        """Generate text asynchronously without blocking the event loop."""
        try:
            output = await asyncio.to_thread(
                self._sync_generate, prompt, system_prompt
            )
            if output and output.strip():
                return output
        except (RuntimeError, ValueError, OSError, TimeoutError):
            pass
        return await self._fallback.generate_text(prompt, system_prompt)
