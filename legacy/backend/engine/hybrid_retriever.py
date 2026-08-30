"""Hybrid semantic and lexical retriever for Indian Standards."""
from __future__ import annotations

import re
import numpy as np
from rapidfuzz import fuzz
from backend.config.settings import app_settings
from backend.engine.embedding_service import EmbeddingService
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.standard_model import IndianStandard


class HybridRetriever:
    """Combines dense vector search, lexical token matching, and code exact match."""

    def __init__(
        self,
        loader: StandardsLoader | None = None,
        embed_svc: EmbeddingService | None = None,
    ) -> None:
        self._loader = loader or StandardsLoader()
        self._embed_svc = embed_svc or EmbeddingService()
        self._standards = self._loader.get_all_standards()
        self._doc_embeddings: dict[str, np.ndarray] = {}
        self._index_standards()

    def _index_standards(self) -> None:
        """Precompute embeddings for standard profiles."""
        for s in self._standards:
            doc_text = f"{s.is_code} {s.title} {s.scope} {' '.join(s.key_parameters)} {' '.join(s.category_keywords)}"
            self._doc_embeddings[s.is_code] = self._embed_svc.get_embedding(doc_text)

    def _calculate_lexical_score(self, query: str, s: IndianStandard) -> float:
        """Compute fuzzy token match score."""
        target = f"{s.is_code} {s.title} {' '.join(s.category_keywords)}".lower()
        score = fuzz.token_set_ratio(query.lower(), target) / 100.0
        return float(score)

    def search(
        self, query: str, division: str | None = None, top_k: int = 5
    ) -> list[tuple[IndianStandard, float, list[str]]]:
        """Perform hybrid retrieval and return top matching standards."""
        if not self._standards:
            return []

        q_vec = self._embed_svc.get_embedding(query)
        alpha = app_settings.ai_engine.hybrid_alpha
        results: list[tuple[IndianStandard, float, list[str]]] = []

        for s in self._standards:
            if division and s.division.upper() != division.upper():
                continue

            dense_score = self._embed_svc.compute_similarity(
                q_vec, self._doc_embeddings.get(s.is_code, q_vec)
            )
            lexical_score = self._calculate_lexical_score(query, s)
            reasons: list[str] = []

            # Direct IS code detection bonus
            code_num = re.sub(r"[^\d]", "", s.is_code)
            if code_num and code_num in query:
                lexical_score = max(lexical_score, 0.95)
                reasons.append(f"Direct match on standard code {s.is_code}")

            hybrid_score = (alpha * dense_score) + ((1.0 - alpha) * lexical_score)

            if dense_score > 0.4:
                reasons.append(f"Semantic scope alignment ({dense_score:.2f})")
            if lexical_score > 0.5:
                reasons.append(f"Keyword/Category relevance ({lexical_score:.2f})")

            results.append((s, hybrid_score, reasons))

        results.sort(key=lambda item: item[1], reverse=True)
        return results[:top_k]
