"""Multithreaded BM25 lexical retrieval engine."""
from __future__ import annotations

import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed

from rank_bm25 import BM25Okapi
from backend.models.standard_model import IndianStandard
from backend.logger.app_logger import get_logger

logger = get_logger("engine.bm25_engine")


def _tokenize(text: str) -> list[str]:
    """Helper function to tokenize text for BM25."""
    return text.lower().split()


class BM25Engine:
    """CPU-bound multithreaded BM25 indexer and searcher."""

    def __init__(self) -> None:
        self.bm25: BM25Okapi | None = None
        self.standards: list[IndianStandard] = []

    def build_index(self, standards: list[IndianStandard]) -> None:
        """Build the BM25 index using multiple threads for tokenization."""
        self.standards = standards
        if not standards:
            logger.warning("No standards provided for BM25 indexing.")
            return

        texts = [f"{s.is_code} {s.title} {' '.join(s.category_keywords)}" for s in standards]
        tokenized_corpus: list[list[str]] = [[] for _ in range(len(texts))]

        max_workers = min(multiprocessing.cpu_count() * 2, len(texts) or 1)
        logger.info(f"Building BM25 index for {len(texts)} documents with {max_workers} threads...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(_tokenize, text): idx
                for idx, text in enumerate(texts)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    tokenized_corpus[idx] = future.result()
                except Exception as exc:
                    logger.error(f"Failed to tokenize document {idx}: {exc}")

        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info("BM25 index built successfully.")

    def search(self, query: str, top_k: int = 5, division: str | None = None) -> list[tuple[IndianStandard, float]]:
        """Search the BM25 index and return ranked standards with scores."""
        if not self.bm25 or not query.strip():
            return []

        tokenized_query = _tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        def _process_result(idx: int, score: float) -> tuple[IndianStandard, float] | None:
            if score <= 0:
                return None
            std = self.standards[idx]
            if division and std.division.upper() != division.upper():
                return None
            return (std, float(score))

        results: list[tuple[IndianStandard, float]] = []
        max_workers = max(1, multiprocessing.cpu_count() - 1)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_process_result, i, score) for i, score in enumerate(scores)]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    results.append(res)

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
