"""Hybrid semantic and lexical dual-index retriever for Indian Standards backed by ChromaDB."""
from __future__ import annotations
import re
from typing import Any
from rapidfuzz import fuzz
from backend.config.settings import app_settings
from backend.engine.chroma_hydrator import hydrate_standard_from_chroma
from backend.engine.embedding_service import EmbeddingService
from backend.ingestion.standards_loader import StandardsLoader
from backend.logger.app_logger import get_logger
from backend.models.recommendation_model import DocumentChunkEvidence
from backend.models.standard_model import IndianStandard
from backend.vectordb.search_service import VectorDbSearchService
from backend.engine.query_expander import QueryExpander
from backend.engine.reranker_service import RerankerService

logger = get_logger("engine.hybrid_retriever")


class HybridRetriever:
    """Combines ChromaDB dense retrieval with in-memory lexical matching and document chunk evidence."""

    def __init__(self, loader: StandardsLoader | None = None, embed_svc: EmbeddingService | None = None) -> None:
        self._loader = loader or StandardsLoader()
        self._embed_svc = embed_svc or EmbeddingService()
        self._vectordb = VectorDbSearchService()
        self._standards = self._loader.get_all_standards()
        self._expander = QueryExpander()
        self._reranker = RerankerService()

    def _calculate_lexical_score(self, query: str, s: IndianStandard) -> float:
        target = f"{s.is_code} {s.title} {' '.join(s.category_keywords)}".lower()
        return float(fuzz.token_set_ratio(query.lower(), target) / 100.0)

    def search(self, query: str, division: str | None = None, top_k: int = 5) -> list[tuple[IndianStandard, float, list[str]]]:
        """Perform Stage 1: Macro Standard Discovery."""
        if not query.strip():
            return []
            
        # Task 1.1: Query Expansion
        expanded_query = self._expander.expand(query)
        
        results_map: dict[str, tuple[IndianStandard, float, list[str]]] = {}
        alpha = app_settings.ai_engine.hybrid_alpha
        logger.info(f"HybridRetriever: Macro search for '{expanded_query}' (Division: {division or 'All'})")
        
        pool_size = getattr(app_settings.ai_engine, "reranker_candidate_pool", 25)

        try:
            hits = self._vectordb.search(query=expanded_query, division=division, top_k=pool_size)
            for hit in hits:
                std = hydrate_standard_from_chroma(hit, self._loader)
                lex_score = self._calculate_lexical_score(expanded_query, std)
                dense_score = float(hit.get("similarity_score", 0.0))
                hybrid_score = (alpha * dense_score) + ((1.0 - alpha) * lex_score)
                reasons = [f"ChromaDB Vector match ({dense_score:.2f})"]
                if lex_score > 0.4:
                    reasons.append(f"Keyword alignment ({lex_score:.2f})")
                results_map[std.is_code] = (std, hybrid_score, reasons)
        except (KeyError, ValueError, Exception) as exc:
            logger.warning(f"[FALLBACK] ChromaDB search error ({type(exc).__name__}) -> using in-memory catalog")

        for s in self._standards:
            if division and s.division.upper() != division.upper():
                continue
            lex_score = self._calculate_lexical_score(expanded_query, s)
            reasons = []
            code_num = re.sub(r"[^\d]", "", s.is_code)
            if code_num and code_num in query:  # use original query for exact code match check
                lex_score, reasons = max(lex_score, 0.95), [f"Direct match on standard code {s.is_code}"]
            if s.is_code in results_map:
                std, ex_sc, ex_r = results_map[s.is_code]
                results_map[s.is_code] = (s, max(ex_sc, lex_score), list(set(ex_r + reasons)))
            elif lex_score > 0.45:
                results_map[s.is_code] = (s, lex_score, [f"Curated catalog match ({lex_score:.2f})"])

        ranked = sorted(results_map.values(), key=lambda item: item[1], reverse=True)
        
        # Task 1.2: Cross-Encoder Reranking
        candidates = ranked[:pool_size]
        final_ranked = self._reranker.rerank(query, candidates, top_k)
        
        return final_ranked

    def search_document_evidence(self, query: str, top_k: int = 5) -> list[DocumentChunkEvidence]:
        """Perform Stage 2: Micro Evidence & Deep Clause Retrieval from PDF chunks."""
        expanded_query = self._expander.expand(query)
        raw_chunks = self._vectordb.search_document_chunks(query=expanded_query, top_k=top_k)
        evidences: list[DocumentChunkEvidence] = []
        for c in raw_chunks:
            evidences.append(DocumentChunkEvidence(
                chunk_id=c.get("chunk_id", ""), doc_id=c.get("doc_id", ""),
                file_name=c.get("file_name", ""), page_number=c.get("page_number", 1),
                total_pages=c.get("total_pages", 1), folder_category=c.get("folder_category", "Standard"),
                snippet=c.get("snippet", ""), relevance_score=c.get("similarity_score", 0.0),
            ))
        return evidences

    def search_with_evidence(
        self, query: str, division: str | None = None, top_k: int = 5, top_k_chunks: int = 5
    ) -> tuple[list[tuple[IndianStandard, float, list[str]]], list[DocumentChunkEvidence]]:
        """Perform unified Dual-Index Retrieval unifying macro standards and micro PDF clause excerpts."""
        standards = self.search(query=query, division=division, top_k=top_k)
        evidences = self.search_document_evidence(query=query, top_k=top_k_chunks)
        codes = [s[0].is_code for s in standards]
        for ev in evidences:
            for c in codes:
                code_digits = re.sub(r"[^\d]", "", c)
                if code_digits and (c.lower() in ev.file_name.lower() or code_digits in ev.file_name.lower() or c.lower() in ev.snippet.lower()):
                    ev.matched_standard = c
                    break
        return standards, evidences
