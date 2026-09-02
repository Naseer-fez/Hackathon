"""Chunking, embedding, and reranking pipeline for document text chunks on GPU."""
from __future__ import annotations
from typing import Any
from backend.engine.embedding_service import get_embedding_service
from backend.engine.reranker_service import RerankerService
from backend.logger.app_logger import get_logger

logger = get_logger("engine.document_chunk_reranker")


def chunk_document_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split clean document text into overlapping chunks."""
    if not text or not text.strip():
        return []
    clean = text.strip()
    chunks: list[str] = []
    start = 0
    text_len = len(clean)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start += max(1, chunk_size - overlap)
    return chunks


class DocumentChunkReranker:
    """Embeds and reranks document chunks locally using GPU acceleration."""

    def __init__(self) -> None:
        self._embedder = get_embedding_service()
        self._reranker = RerankerService()

    def retrieve_and_rerank_chunks(
        self, query: str, full_text: str, top_k: int = 5, candidate_pool: int = 20
    ) -> list[dict[str, Any]]:
        """Chunk full text, score via dense embeddings, and rescore with cross-encoder."""
        chunks = chunk_document_text(full_text)
        if not chunks:
            return []

        q_vec = self._embedder.get_embedding(query)
        scored_chunks: list[tuple[float, str]] = []
        for c in chunks:
            c_vec = self._embedder.get_embedding(c)
            sim = self._embedder.compute_similarity(q_vec, c_vec)
            scored_chunks.append((sim, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        candidates = [c for _, c in scored_chunks[:candidate_pool]]

        # Use cross encoder if available
        model = getattr(self._reranker, "_cross_encoder", None)
        if model is None:
            self._reranker._load_model()
            model = getattr(self._reranker, "_cross_encoder", None)

        if model is not None:
            try:
                pairs = [[query, c] for c in candidates]
                scores = model.predict(pairs)
                reranked = sorted(zip(scores, candidates), key=lambda x: float(x[0]), reverse=True)
                return [{"text": c, "score": float(s), "page_number": 1} for s, c in reranked[:top_k]]
            except (RuntimeError, ValueError, TypeError) as exc:
                logger.warning(f"Cross-encoder chunk scoring failed ({type(exc).__name__}): {exc}")

        return [{"text": c, "score": float(s), "page_number": 1} for s, c in scored_chunks[:top_k]]
