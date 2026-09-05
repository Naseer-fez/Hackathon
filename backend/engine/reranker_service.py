"""Cross-encoder reranker service for second-stage candidate scoring."""
from __future__ import annotations

from typing import Any
import torch

from backend.config.settings import app_settings
from backend.logger.app_logger import get_logger
from backend.models.standard_model import IndianStandard

logger = get_logger("engine.reranker_service")

# Type alias for standard search result tuples
_CandidateTuple = tuple[IndianStandard, float, list[str]]


class RerankerService:
    """Cross-encoder reranker that rescores first-stage retrieval candidates on CUDA."""

    _cross_encoder: Any = None
    _load_failed: bool = False

    def __init__(self) -> None:
        self._model_name: str = app_settings.ai_engine.reranker_model
        self._cross_encoder: Any = None
        self._load_failed: bool = False

    def _load_model(self) -> None:
        """Lazy-load the cross-encoder model onto CUDA if available, else CPU."""
        if self._load_failed or RerankerService._load_failed:
            return
        if self._cross_encoder is not None:
            return
        if RerankerService._cross_encoder is not None:
            self._cross_encoder = RerankerService._cross_encoder
            return
        try:
            from sentence_transformers import CrossEncoder

            device = "cuda:0" if (app_settings.ai_engine.enable_gpu and torch.cuda.is_available()) else "cpu"
            logger.info(f"Loading cross-encoder model '{self._model_name}' on {device}...")
            kwargs = {"torch_dtype": torch.float16} if "cuda" in device else {}
            model = CrossEncoder(self._model_name, device=device, model_kwargs=kwargs)
            self._cross_encoder = model
            RerankerService._cross_encoder = model
            logger.info(f"Cross-encoder model '{self._model_name}' loaded successfully on {device}.")
        except (ImportError, RuntimeError, OSError, ValueError, AssertionError) as exc:
            self._load_failed = True
            RerankerService._load_failed = True
            logger.warning(
                f"Cross-encoder model failed to load ({type(exc).__name__}: {exc}). "
                "Falling back to hybrid-only ranking."
            )

    def preload(self) -> bool:
        """Preload cross-encoder model weights into GPU VRAM."""
        self._load_model()
        return (self._cross_encoder or RerankerService._cross_encoder) is not None

    def warmup(self) -> bool:
        """Warm up cross-encoder inference compute graph on GPU."""
        if not self.preload():
            return False
        model = self._cross_encoder or RerankerService._cross_encoder
        if model is not None:
            try:
                model.predict([["warmup query", "warmup passage"]])
                logger.info("Reranker model warmed up successfully.")
                return True
            except (RuntimeError, ValueError, TypeError) as exc:
                logger.warning(f"Reranker warm-up failed ({type(exc).__name__}: {exc})")
        return False

    def rerank(self, query: str, candidates: list[_CandidateTuple], top_k: int) -> list[_CandidateTuple]:
        """Rerank candidates using cross-encoder scores."""
        if not candidates:
            return []
        model = self._cross_encoder or RerankerService._cross_encoder
        if model is None and not (self._load_failed or RerankerService._load_failed):
            self._load_model()
            model = self._cross_encoder or RerankerService._cross_encoder
        if model is None:
            logger.warning("Cross-encoder unavailable; returning hybrid-ranked results.")
            return candidates[:top_k]

        pairs = [[query, f"{std.is_code} {std.title} {std.scope}"] for std, _, _ in candidates]
        try:
            scores = model.predict(pairs)
        except (RuntimeError, ValueError, TypeError) as exc:
            logger.warning(f"Cross-encoder prediction failed ({type(exc).__name__}: {exc})")
            return candidates[:top_k]

        scored: list[tuple[float, _CandidateTuple]] = []
        for idx, (std, _hscore, reasons) in enumerate(candidates):
            ce_score = float(scores[idx])
            scored.append((ce_score, (std, ce_score, reasons + [f"Cross-Encoder reranked (score: {ce_score:.3f})"])))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]
