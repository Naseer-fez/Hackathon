"""Dense vector embedding service with online SentenceTransformers and offline fallback."""
from __future__ import annotations

import hashlib
from typing import Any
import numpy as np
from backend.config.settings import app_settings


class EmbeddingService:
    """Computes and caches dense semantic embeddings with offline resilience."""

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = (
            model_name or app_settings.ai_engine.embedding_model_name
        )
        self._model: Any = None
        self._is_offline = False
        self._dim = 384
        self._cache: dict[str, np.ndarray] = {}

    def _fallback_embed(self, text: str) -> np.ndarray:
        """Compute deterministic dense semantic vector using character n-grams and hashing."""
        vec = np.zeros(self._dim, dtype=np.float32)
        words = text.lower().split()
        for word in words:
            # Word level hash
            h_word = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            vec[h_word % self._dim] += 2.0
            # Character trigrams for morphological similarity
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    trigram = word[i : i + 3]
                    h_tri = int(hashlib.sha256(trigram.encode("utf-8")).hexdigest(), 16)
                    vec[h_tri % self._dim] += 1.0

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def _try_load_model(self) -> None:
        """Attempt to load SentenceTransformer or flag as offline."""
        if self._model is not None or self._is_offline:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self._model_name, local_files_only=False
            )
        except (OSError, ValueError, RuntimeError, ImportError):
            self._is_offline = True
            self._model = None

    def get_embedding(self, text: str) -> np.ndarray:
        """Generate normalized dense vector embedding for single text string."""
        clean_text = text.strip().lower()
        if clean_text in self._cache:
            return self._cache[clean_text]

        self._try_load_model()

        if self._model is not None and not self._is_offline:
            try:
                vec = self._model.encode(
                    clean_text, convert_to_numpy=True, normalize_embeddings=True
                )
                self._cache[clean_text] = vec
                return vec
            except (RuntimeError, ValueError):
                self._is_offline = True

        vec = self._fallback_embed(clean_text)
        self._cache[clean_text] = vec
        return vec

    def compute_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Compute cosine similarity between two normalized vectors."""
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
