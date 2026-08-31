"""Cross-encoder reranker service for second-stage candidate scoring."""
from __future__ import annotations

from typing import Any

from backend.config.settings import app_settings
from backend.logger.app_logger import get_logger
from backend.models.standard_model import IndianStandard

logger = get_logger("engine.reranker_service")

# Type alias for standard search result tuples
_CandidateTuple = tuple[IndianStandard, float, list[str]]


class RerankerService:
    """Cross-encoder reranker that rescores first-stage retrieval candidates on CUDA."""

    def __init__(self) -> None:
        self._cross_encoder: Any = None
        self._model_name: str = app_settings.ai_engine.reranker_model
        self._load_failed: bool = False

    def _load_model(self) -> None:
        """Lazy-load the cross-encoder model onto CUDA (cuda:0)."""
        if self._load_failed:
            return
        try:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading cross-encoder model '{self._model_name}' on cuda:0...")
            self._cross_encoder = CrossEncoder(self._model_name, device="cuda:0")
            logger.info(f"Cross-encoder model '{self._model_name}' loaded successfully on CUDA.")
        except (ImportError, RuntimeError, OSError, ValueError) as exc:
            self._load_failed = True
            logger.warning(
                f"Cross-encoder model failed to load ({type(exc).__name__}: {exc}). "
                "Falling back to hybrid-only ranking."
            )

    def rerank(
        self,
        query: str,
        candidates: list[_CandidateTuple],
        top_k: int,
    ) -> list[_CandidateTuple]:
        """Rerank candidates using cross-encoder scores.

        If the model is unavailable, gracefully returns the first top_k candidates
        from the original ranking.
        """
        if not candidates:
            return []

        if self._cross_encoder is None and not self._load_failed:
            self._load_model()

        if self._cross_encoder is None:
            logger.warning("Cross-encoder unavailable; returning hybrid-ranked results.")
            return candidates[:top_k]

        pairs: list[list[str]] = []
        for std, _score, _reasons in candidates:
            candidate_text = f"{std.is_code} {std.title} {std.scope}"
            pairs.append([query, candidate_text])

        try:
            scores = self._cross_encoder.predict(pairs)
        except (RuntimeError, ValueError, TypeError) as exc:
            logger.warning(f"Cross-encoder prediction failed ({type(exc).__name__}): {exc}")
            return candidates[:top_k]

        scored: list[tuple[float, _CandidateTuple]] = []
        for idx, (std, hybrid_score, reasons) in enumerate(candidates):
            ce_score = float(scores[idx])
            updated_reasons = reasons + [f"Cross-Encoder reranked (score: {ce_score:.3f})"]
            scored.append((ce_score, (std, ce_score, updated_reasons)))

        scored.sort(key=lambda item: item[0], reverse=True)
        reranked = [entry for _ce, entry in scored[:top_k]]
        logger.info(f"Cross-encoder reranked {len(candidates)} candidates -> top {top_k}")
        return reranked
