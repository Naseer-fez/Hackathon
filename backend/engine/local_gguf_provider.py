"""Local GGUF LLM provider using llama-cpp-python with persistent VRAM caching."""
from __future__ import annotations
import asyncio
from pathlib import Path
import threading
import time
from typing import Any
from backend.config.settings import app_settings
from backend.engine.gguf_loader import instantiate_llama
from backend.engine.llm_interface import BaseLlmProvider
from backend.logger.app_logger import get_logger

logger = get_logger("engine.local_gguf_provider")


class LocalGgufLlmProvider(BaseLlmProvider):
    """Local GGUF provider with CUDA GPU acceleration, warm-up, and zero-unload caching."""

    def __init__(
        self,
        model_path: str | None = None,
        n_ctx: int | None = None,
        n_threads: int | None = None,
        n_gpu_layers: int | None = None,
        chat_format: str | None = None,
    ) -> None:
        self._model_path = model_path or app_settings.llm.model_path
        self._n_ctx = n_ctx or app_settings.llm.n_ctx
        self._n_threads = n_threads or app_settings.llm.n_threads
        self._n_gpu_layers = n_gpu_layers if n_gpu_layers is not None else app_settings.llm.n_gpu_layers
        self._chat_format = chat_format or app_settings.llm.chat_format
        self._model, self._lock = None, threading.Lock()

    def _init_llama_instance(self, ctx: int, gpu_layers: int | None = None, *args: Any, **kwargs: Any) -> Any:
        layers = self._n_gpu_layers if gpu_layers is None else gpu_layers
        return instantiate_llama(self._model_path, ctx, self._n_threads, layers, self._chat_format)

    def _load_model(self) -> Any:
        if not Path(self._model_path).exists():
            logger.info(f"Local GGUF: Model binary not found at '{self._model_path}'")
            return None
        configs = [(self._n_ctx, self._n_gpu_layers), (1024, self._n_gpu_layers), (512, self._n_gpu_layers), (512, 0)]
        for ctx_cand, gpu_cand in configs:
            try:
                try:
                    return self._init_llama_instance(ctx_cand, gpu_cand)
                except TypeError:
                    return self._init_llama_instance(ctx_cand)
            except (ValueError, RuntimeError, OSError) as exc:
                logger.warning(f"Local GGUF: Load failed (ctx={ctx_cand}, gpu={gpu_cand}): {exc}")
        return None

    def preload(self) -> bool:
        with self._lock:
            if self._model is None:
                t0 = time.perf_counter()
                self._model = self._load_model()
                logger.info(f"Local GGUF: Preloaded in {(time.perf_counter() - t0) * 1000.0:.2f}ms (Status: {'SUCCESS' if self._model else 'OFFLINE'})")
            return self._model is not None

    def warmup(self) -> bool:
        with self._lock:
            if self._model is None:
                self.preload()
            if self._model is None:
                logger.info("Local GGUF: Warmup skipped (Model offline)")
                return False
            try:
                t0 = time.perf_counter()
                self._model.create_chat_completion(messages=[{"role": "user", "content": "Warmup"}], max_tokens=1, temperature=0.0)
                logger.info(f"Local GGUF: Warmed up in {(time.perf_counter() - t0) * 1000.0:.2f}ms (CUDA initialized)")
                return True
            except (ValueError, RuntimeError, TypeError, KeyError, IndexError, OSError) as exc:
                logger.warning(f"Local GGUF: Warmup error ({type(exc).__name__}: {exc})")
                return False

    def is_loaded(self) -> bool:
        return self._model is not None

    def _sync_generate(self, prompt: str, system_prompt: str | None) -> str | None:
        with self._lock:
            if self._model is None:
                self._model = self._load_model()
            if self._model is None:
                return None
            msgs = [{"role": "system", "content": system_prompt or "Expert BIS advisor."}, {"role": "user", "content": prompt}]
            try:
                resp = self._model.create_chat_completion(messages=msgs, temperature=app_settings.llm.temperature, max_tokens=app_settings.llm.max_tokens)
                choices = resp.get("choices", [])
                return str(choices[0]["message"].get("content", "")) if choices and "message" in choices[0] else None
            except (ValueError, RuntimeError, TypeError, KeyError, IndexError, OSError) as exc:
                logger.warning(f"[FALLBACK] GGUF inference error ({type(exc).__name__}: {exc})")
                return None

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            out = await asyncio.to_thread(self._sync_generate, prompt, system_prompt)
            if out and out.strip():
                return out.strip()
        except (RuntimeError, ValueError, OSError) as exc:
            logger.warning(f"Local GGUF: Async generation error ({type(exc).__name__}: {exc})")
        return "No LLM model is currently available (Local GGUF model not active)."
