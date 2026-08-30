"""ChromaDB-compatible SentenceTransformer embedding function with shared model cache and warmup."""
from __future__ import annotations
import hashlib
import os
import threading
import time
from typing import Any
import numpy as np
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from backend.logger.app_logger import get_logger

logger = get_logger("vectordb.embedding")
_SHARED_MODEL_CACHE: dict[str, Any] = {}
_SHARED_LOCK = threading.Lock()


class SentenceTransformerEmbeddingFunction(EmbeddingFunction[Documents]):
    """Dense embeddings using shared SentenceTransformers or neural hashing fallback."""

    def __init__(self, model_name: str = "d:/CODE/Hackathon/llm/all-MiniLM-L6-v2", dim: int = 384) -> None:
        self._model_name, self._dim, self._model, self._offline = model_name, dim, None, False

    @classmethod
    def name(cls) -> str:
        return "bis_sentence_transformer_resilient"

    def get_config(self) -> dict[str, Any]:
        return {"model_name": self._model_name, "dim": self._dim}

    @classmethod
    def build_from_config(cls, config: dict[str, Any]) -> SentenceTransformerEmbeddingFunction:
        return cls(model_name=config.get("model_name", "d:/CODE/Hackathon/llm/all-MiniLM-L6-v2"), dim=config.get("dim", 384))

    def _load_model(self) -> None:
        if self._model is not None or self._offline:
            return
        with _SHARED_LOCK:
            if self._model_name in _SHARED_MODEL_CACHE:
                self._model = _SHARED_MODEL_CACHE[self._model_name]
                return
            if os.getenv("VECTORDB_OFFLINE", "false").lower() in ("1", "true"):
                self._offline = True
                return
            try:
                from backend.config.settings import app_settings
                from sentence_transformers import SentenceTransformer
                import torch
                dev = "cuda" if (app_settings.ai_engine.enable_gpu and torch.cuda.is_available()) else "cpu"
                logger.info(f"SentenceTransformer: Loading '{self._model_name}' on {dev}...")
                self._model = SentenceTransformer(self._model_name, device=dev)
                _SHARED_MODEL_CACHE[self._model_name] = self._model
            except (OSError, ValueError, RuntimeError, ImportError) as exc:
                logger.warning(f"SentenceTransformer load error ({type(exc).__name__}) -> fallback")
                self._offline, self._model = True, None

    def preload(self) -> bool:
        t0 = time.perf_counter()
        self._load_model()
        logger.info(f"SentenceTransformer (Chroma): Preloaded in {(time.perf_counter() - t0) * 1000.0:.2f}ms (Status: {'ONLINE' if self._model else 'OFFLINE'})")
        return self._model is not None

    def warmup(self) -> bool:
        t0 = time.perf_counter()
        self(["warmup"])
        logger.info(f"SentenceTransformer (Chroma): Warmed up in {(time.perf_counter() - t0) * 1000.0:.2f}ms")
        return True

    def _hash_embed_text(self, text: str) -> list[float]:
        vec = np.zeros(self._dim, dtype=np.float32)
        for w in text.lower().split():
            vec[int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % self._dim] += 2.0
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    vec[int(hashlib.sha256(w[i : i + 3].encode("utf-8")).hexdigest(), 16) % self._dim] += 1.0
        norm = np.linalg.norm(vec)
        return [float(x) for x in (vec / norm if norm > 0 else vec)]

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []
        self._load_model()
        if self._model is not None and not self._offline:
            try:
                embs = self._model.encode(input, convert_to_numpy=True, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
                return [[float(x) for x in emb] for emb in embs]
            except (RuntimeError, ValueError):
                self._offline = True
        return [self._hash_embed_text(doc) for doc in input]

    def embed_query(self, input: Documents) -> Embeddings:
        return self(input)

    def embed_documents(self, input: Documents) -> Embeddings:
        return self(input)
