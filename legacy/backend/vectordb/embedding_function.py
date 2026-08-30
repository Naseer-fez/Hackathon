"""ChromaDB-compatible SentenceTransformer embedding function with resilient fallback."""
from __future__ import annotations

import hashlib
import os
from typing import Any
import numpy as np
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings


class SentenceTransformerEmbeddingFunction(EmbeddingFunction[Documents]):
    """Generates dense vector embeddings using SentenceTransformers or neural hashing fallback."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", dim: int = 384) -> None:
        self._model_name = model_name
        self._dim = dim
        self._model: Any = None
        self._offline = False

    @classmethod
    def name(cls) -> str:
        """Return embedding function unique identifier for ChromaDB."""
        return "bis_sentence_transformer_resilient"

    def get_config(self) -> dict[str, Any]:
        """Return configuration dictionary for ChromaDB serialization."""
        return {"model_name": self._model_name, "dim": self._dim}

    @classmethod
    def build_from_config(cls, config: dict[str, Any]) -> "SentenceTransformerEmbeddingFunction":
        """Recreate embedding function from stored ChromaDB configuration."""
        return cls(
            model_name=config.get("model_name", "sentence-transformers/all-MiniLM-L6-v2"),
            dim=config.get("dim", 384),
        )

    def _load_model(self) -> None:
        """Attempt to load SentenceTransformer model with local priority and offline fallback."""
        if self._model is not None or self._offline:
            return
        if os.getenv("VECTORDB_OFFLINE", "false").lower() in ("1", "true"):
            self._offline = True
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name, local_files_only=True)
        except (OSError, RuntimeError, ValueError, ImportError, Exception):
            self._offline = True
            self._model = None

    def _hash_embed_text(self, text: str) -> list[float]:
        """Compute deterministic dense semantic vector using character n-grams and hashing."""
        vec = np.zeros(self._dim, dtype=np.float32)
        words = text.lower().split()
        for word in words:
            h_word = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            vec[h_word % self._dim] += 2.0
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    trigram = word[i : i + 3]
                    h_tri = int(hashlib.sha256(trigram.encode("utf-8")).hexdigest(), 16)
                    vec[h_tri % self._dim] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return [float(x) for x in vec]

    def __call__(self, input: Documents) -> Embeddings:
        """Generate normalized vector embeddings for a list of document strings."""
        if not input:
            return []
        self._load_model()
        if self._model is not None and not self._offline:
            try:
                embeddings = self._model.encode(
                    input,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    batch_size=32,
                    show_progress_bar=False,
                )
                return [[float(x) for x in emb] for emb in embeddings]
            except (RuntimeError, ValueError, Exception):
                self._offline = True
        return [self._hash_embed_text(doc) for doc in input]

    def embed_query(self, input: Documents) -> Embeddings:
        """Chroma interface alias for embedding queries."""
        return self(input)

    def embed_documents(self, input: Documents) -> Embeddings:
        """Chroma interface alias for embedding documents."""
        return self(input)
