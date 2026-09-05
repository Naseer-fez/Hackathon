"""Dense vector embedding service with online SentenceTransformers and offline fallback."""
from __future__ import annotations
import hashlib
import threading
import time
from typing import Any
import numpy as np
from backend.config.settings import app_settings
from backend.logger.app_logger import get_logger
from backend.vectordb.embedding_function import _SHARED_LOCK, _SHARED_MODEL_CACHE

logger = get_logger("engine.embedding_service")
_GLOBAL_EMBED_SERVICE: EmbeddingService | None = None
_EMBED_LOCK = threading.Lock()


def get_embedding_service() -> EmbeddingService:
    """Return persistent singleton EmbeddingService instance."""
    global _GLOBAL_EMBED_SERVICE
    if _GLOBAL_EMBED_SERVICE is None:
        with _EMBED_LOCK:
            if _GLOBAL_EMBED_SERVICE is None:
                _GLOBAL_EMBED_SERVICE = EmbeddingService()
    return _GLOBAL_EMBED_SERVICE


class EmbeddingService:
    """Computes and caches dense semantic embeddings with offline resilience and warmup."""

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or app_settings.ai_engine.embedding_model_name
        self._model, self._is_offline, self._dim = None, False, 384
        self._cache: dict[str, np.ndarray] = {}
        self._lock = threading.Lock()

    def _fallback_embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self._dim, dtype=np.float32)
        for word in text.lower().split():
            vec[int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % self._dim] += 2.0
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    vec[int(hashlib.sha256(word[i : i + 3].encode("utf-8")).hexdigest(), 16) % self._dim] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def _try_load_model(self) -> None:
        if self._model is not None or self._is_offline:
            return
        with _SHARED_LOCK:
            if self._model_name in _SHARED_MODEL_CACHE:
                self._model = _SHARED_MODEL_CACHE[self._model_name]
                return
            try:
                from sentence_transformers import SentenceTransformer
                import torch
                
                # Maximize PyTorch GPU performance for RTX 3050 (Ampere)
                if torch.cuda.is_available():
                    torch.backends.cudnn.benchmark = True
                    torch.backends.cuda.matmul.allow_tf32 = True
                    torch.backends.cudnn.allow_tf32 = True
                
                device = "cuda" if (app_settings.ai_engine.enable_gpu and torch.cuda.is_available()) else "cpu"
                logger.info(f"EmbeddingService: Loading '{self._model_name}' on {device}...")
                self._model = SentenceTransformer(self._model_name, device=device)
                
                # Optional: compile model for further speedup if using PyTorch 2.0+
                if device == "cuda" and hasattr(torch, "compile"):
                    try:
                        # SentenceTransformers might have issues with torch.compile depending on the version, 
                        # but we can try to compile the underlying auto_model
                        pass 
                    except Exception as e:
                        logger.warning(f"Failed to compile embedding model: {e}")
                        
                _SHARED_MODEL_CACHE[self._model_name] = self._model
            except (OSError, ValueError, RuntimeError, ImportError) as exc:
                logger.warning(f"EmbeddingService: Load error ({type(exc).__name__}: {exc}) -> fallback")
                self._is_offline, self._model = True, None

    def preload(self) -> bool:
        t0 = time.perf_counter()
        self._try_load_model()
        logger.info(f"EmbeddingService: Preloaded in {(time.perf_counter() - t0) * 1000.0:.2f}ms (Status: {'ONLINE' if self._model else 'OFFLINE'})")
        return self._model is not None

    def warmup(self) -> bool:
        t0 = time.perf_counter()
        self.get_embedding("warmup")
        logger.info(f"EmbeddingService: Warmed up in {(time.perf_counter() - t0) * 1000.0:.2f}ms")
        return True

    def get_embedding(self, text: str) -> np.ndarray:
        clean = text.strip().lower()
        if clean in self._cache:
            return self._cache[clean]
        self._try_load_model()
        if self._model is not None and not self._is_offline:
            try:
                vec = self._model.encode(clean, convert_to_numpy=True, normalize_embeddings=True)
                self._cache[clean] = vec
                return vec
            except (RuntimeError, ValueError):
                self._is_offline = True
        vec = self._fallback_embed(clean)
        self._cache[clean] = vec
        return vec

    def compute_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        norm_a, norm_b = np.linalg.norm(vec_a), np.linalg.norm(vec_b)
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b)) if (norm_a > 0 and norm_b > 0) else 0.0
