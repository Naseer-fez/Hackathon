"""Local GGUF LLM provider using llama-cpp-python with persistent VRAM caching."""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
import threading
import time
from typing import Any, AsyncGenerator
from backend.config.settings import app_settings
from backend.engine.gguf_loader import instantiate_llama
from backend.engine.llm_interface import BaseLlmProvider
from backend.logger.app_logger import get_logger

logger = get_logger("engine.local_gguf_provider")
_STREAM_END = object()


class BackpressureError(Exception):
    """Raised when the LLM inference queue is full."""


def _safe_get_next(iterator: Any) -> Any:
    """Fetch next item safely without raising StopIteration into an asyncio.Future."""
    return next(iterator, _STREAM_END)


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
        self._model = None
        self._lock = threading.Lock()  # startup-only (preload/warmup)
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(1)
        self._queue_count: int = 0
        self._max_queue: int = app_settings.llm.max_queue_size
        self._grammar: Any = None
        self._grammar_loaded: bool = False

    def _load_grammar(self) -> Any:
        """Load GBNF grammar from configured path. Returns None on failure (unconstrained)."""
        if self._grammar_loaded:
            return self._grammar
        self._grammar_loaded = True
        if not app_settings.llm.enable_grammar:
            logger.info("Local GGUF: Grammar disabled via config — using unconstrained generation")
            return None
        grammar_path = app_settings.llm.grammar_file
        if not grammar_path:
            logger.info("Local GGUF: No grammar file configured — using unconstrained generation")
            return None
        if not Path(grammar_path).exists():
            logger.warning(f"Local GGUF: Grammar file not found at '{grammar_path}' — falling back to unconstrained generation")
            return None
        try:
            from llama_cpp import LlamaGrammar
            self._grammar = LlamaGrammar.from_file(grammar_path)
            logger.info(f"Local GGUF: Loaded GBNF grammar from '{grammar_path}'")
            return self._grammar
        except (ValueError, RuntimeError, OSError, ImportError) as exc:
            logger.warning(f"Local GGUF: Failed to load grammar ({type(exc).__name__}: {exc}) — falling back to unconstrained generation")
            return None

    def _init_llama_instance(self, ctx: int, gpu_layers: int | None = None) -> Any:
        layers = self._n_gpu_layers if gpu_layers is None else gpu_layers
        return instantiate_llama(self._model_path, ctx, self._n_threads, layers, self._chat_format)

    def _load_model(self) -> Any:
        if not Path(self._model_path).exists():
            logger.info(f"Local GGUF: Model binary not found at '{self._model_path}'")
            return None
        configs = [(self._n_ctx, self._n_gpu_layers), (4096, self._n_gpu_layers), (4096, 0)]
        for ctx_cand, gpu_cand in configs:
            try:
                return self._init_llama_instance(ctx_cand, gpu_cand)
            except (ValueError, RuntimeError, TypeError, OSError) as exc:
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
                return False
            try:
                self._model.create_chat_completion(messages=[{"role": "user", "content": "Warmup"}], max_tokens=1, temperature=0.0)
                return True
            except (ValueError, RuntimeError, TypeError, KeyError, IndexError, OSError) as exc:
                logger.warning(f"Local GGUF: Warmup error ({type(exc).__name__}: {exc})")
                return False

    def is_loaded(self) -> bool:
        return self._model is not None

    def _sync_generate(self, prompt: str, system_prompt: str | None) -> str | None:
        if self._model is None:
            self._model = self._load_model()
        if self._model is None:
            return None
        grammar = self._load_grammar()
        msgs = [{"role": "system", "content": system_prompt or "Expert BIS advisor."}, {"role": "user", "content": prompt}]
        try:
            resp = self._model.create_chat_completion(
                messages=msgs,
                temperature=app_settings.llm.temperature,
                max_tokens=app_settings.llm.max_tokens,
                grammar=grammar,
            )
            choices = resp.get("choices", [])
            return str(choices[0]["message"].get("content", "")) if choices and "message" in choices[0] else None
        except (ValueError, RuntimeError, TypeError, KeyError, IndexError, OSError) as exc:
            if grammar is not None:
                logger.warning(f"[FALLBACK] GGUF grammar inference error ({type(exc).__name__}: {exc}) — retrying without grammar")
                try:
                    resp = self._model.create_chat_completion(
                        messages=msgs,
                        temperature=app_settings.llm.temperature,
                        max_tokens=app_settings.llm.max_tokens,
                    )
                    choices = resp.get("choices", [])
                    return str(choices[0]["message"].get("content", "")) if choices and "message" in choices[0] else None
                except (ValueError, RuntimeError, TypeError, KeyError, IndexError, OSError) as exc2:
                    logger.warning(f"[FALLBACK] GGUF unconstrained inference also failed ({type(exc2).__name__}: {exc2})")
                    return None
            logger.warning(f"[FALLBACK] GGUF inference error ({type(exc).__name__}: {exc})")
            return None

    def _sync_generate_stream(self, prompt: str, system_prompt: str | None) -> Any:
        if self._model is None:
            self._model = self._load_model()
        if self._model is None:
            yield "No LLM model is currently available (Local GGUF model not active)."
            return
        grammar = self._load_grammar()
        msgs = [{"role": "system", "content": system_prompt or "Expert BIS advisor."}, {"role": "user", "content": prompt}]
        try:
            resp = self._model.create_chat_completion(
                messages=msgs,
                temperature=app_settings.llm.temperature,
                max_tokens=app_settings.llm.max_tokens,
                stream=True,
                grammar=grammar,
            )
            for chunk in resp:
                choices = chunk.get("choices", [])
                if choices and "delta" in choices[0]:
                    c = choices[0]["delta"].get("content", "")
                    if c:
                        yield c
        except (ValueError, RuntimeError, TypeError, KeyError, IndexError, OSError) as exc:
            if grammar is not None:
                logger.warning(f"[FALLBACK] GGUF grammar streaming error ({type(exc).__name__}: {exc}) — retrying without grammar")
                try:
                    resp = self._model.create_chat_completion(
                        messages=msgs,
                        temperature=app_settings.llm.temperature,
                        max_tokens=app_settings.llm.max_tokens,
                        stream=True,
                    )
                    for chunk in resp:
                        choices = chunk.get("choices", [])
                        if choices and "delta" in choices[0]:
                            c = choices[0]["delta"].get("content", "")
                            if c:
                                yield c
                    return
                except (ValueError, RuntimeError, TypeError, KeyError, IndexError, OSError) as exc2:
                    logger.warning(f"[FALLBACK] GGUF unconstrained streaming also failed ({type(exc2).__name__}: {exc2})")
            logger.warning(f"[FALLBACK] GGUF streaming error ({type(exc).__name__}: {exc})")
            yield f"\n[Error: {type(exc).__name__}]"

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        if self._queue_count >= self._max_queue:
            raise BackpressureError(f"LLM inference queue is full ({self._max_queue} pending)")
        self._queue_count += 1
        logger.info(f"Queue: request enqueued (position={self._queue_count})")
        try:
            async with self._semaphore:
                out = await asyncio.to_thread(self._sync_generate, prompt, system_prompt)
                if out and out.strip():
                    return out.strip()
        except BackpressureError:
            raise
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning(f"Local GGUF: Async generation error ({type(exc).__name__}: {exc})")
        finally:
            self._queue_count -= 1
        return "No LLM model is currently available (Local GGUF model not active)."

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        if self._queue_count >= self._max_queue:
            raise BackpressureError(f"LLM inference queue is full ({self._max_queue} pending)")
        self._queue_count += 1
        position = self._queue_count
        logger.info(f"Queue: stream request enqueued (position={position})")
        try:
            if position > 1:
                yield json.dumps({"status": "queued", "position": position})
            async with self._semaphore:
                gen = await asyncio.to_thread(self._sync_generate_stream, prompt, system_prompt)
                while True:
                    chunk = await asyncio.to_thread(_safe_get_next, gen)
                    if chunk is _STREAM_END:
                        break
                    yield chunk
        except BackpressureError:
            raise
        except (ValueError, RuntimeError, OSError, Exception) as exc:
            logger.warning(f"Local GGUF: Async stream error ({type(exc).__name__}: {exc})")
            yield "\n[Stream Interrupted]"
        finally:
            self._queue_count -= 1
