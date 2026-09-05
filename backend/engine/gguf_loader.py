"""Low-level GGUF runtime loader with multi-tier CUDA fallback."""
from __future__ import annotations

import gc
from pathlib import Path
from typing import Any
from backend.logger.app_logger import get_logger

logger = get_logger("engine.gguf_loader")


def instantiate_llama(
    model_path: str, context_size: int, threads: int, gpu_layers: int, chat_format: str
) -> Any:
    """Instantiate Llama runtime with specified context size and GPU offload layers."""
    import llama_cpp
    from llama_cpp import Llama

    gc.collect()
    logger.info(f"Local GGUF: Loading '{model_path}' (ctx={context_size}, gpu={gpu_layers})...")
    
    extra_kwargs: dict[str, Any] = {}
    if context_size >= 16384:
        q8 = getattr(llama_cpp, "GGML_TYPE_Q8_0", 8)
        extra_kwargs["type_k"] = q8
        extra_kwargs["type_v"] = q8
        logger.info(f"Local GGUF: Enabled 8-bit quantized KV cache (Q8_0) for {context_size} context.")

    return Llama(
        model_path=model_path,
        n_ctx=context_size,
        n_threads=threads,
        n_gpu_layers=-1 if gpu_layers > 0 else 0, # Maximize GPU usage
        offload_kqv=(gpu_layers > 0),
        flash_attn=(gpu_layers > 0),  # Maximize performance on Ampere/RTX 3050
        chat_format=chat_format,
        verbose=False,
        **extra_kwargs,
    )


def load_gguf_model(
    model_path: str, n_ctx: int, n_threads: int, n_gpu_layers: int, chat_format: str
) -> Any:
    """Load local GGUF model with multi-tier fallback (GPU -> reduced layers -> CPU)."""
    if not Path(model_path).exists():
        logger.info(f"Local GGUF: Model binary not found at '{model_path}'")
        return None
    configs = [(n_ctx, n_gpu_layers), (1024, n_gpu_layers), (512, n_gpu_layers), (512, 0)]
    for ctx_cand, gpu_cand in configs:
        try:
            return instantiate_llama(model_path, ctx_cand, n_threads, gpu_cand, chat_format)
        except (ValueError, RuntimeError, TypeError, OSError, ImportError, ModuleNotFoundError) as exc:
            gc.collect()
            logger.warning(f"Local GGUF: Load failed (ctx={ctx_cand}, gpu={gpu_cand}): {exc}")
    return None

