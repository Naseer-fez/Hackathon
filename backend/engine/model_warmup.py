"""Model warm-up and VRAM caching orchestration routine."""
from __future__ import annotations

import time
from backend.engine.embedding_service import get_embedding_service
from backend.engine.gpu_diagnostics import log_startup_vram_status
from backend.engine.llm_service import get_llm_provider
from backend.logger.app_logger import get_logger
from backend.vectordb.embedding_function import SentenceTransformerEmbeddingFunction

logger = get_logger("engine.model_warmup")


def warmup_backend_ai_models() -> float:
    """Pre-load model weights and warm up inference compute graphs into VRAM/RAM."""
    t0 = time.perf_counter()
    log_startup_vram_status("pre_warmup")

    # 1. Warm up dense embedding models
    get_embedding_service().preload()
    get_embedding_service().warmup()
    chroma_fn = SentenceTransformerEmbeddingFunction()
    chroma_fn.preload()
    chroma_fn.warmup()

    # 2. Warm up LLM provider (Local GGUF or configured provider)
    llm_prov = get_llm_provider()
    if hasattr(llm_prov, "preload"):
        llm_prov.preload()
    if hasattr(llm_prov, "warmup"):
        llm_prov.warmup()

    log_startup_vram_status("post_warmup")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    logger.info(f"Model warm-up routine completed in {elapsed_ms:.2f}ms")
    return elapsed_ms
