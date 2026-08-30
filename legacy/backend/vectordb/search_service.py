"""Hybrid semantic retrieval and metadata filtering service for Indian Standards."""
from __future__ import annotations

from typing import Any
from backend.vectordb.config import VectorDbSettings, vector_db_settings
from backend.vectordb.indexer import VectorDbIndexer


class VectorDbSearchService:
    """Provides semantic search and metadata-filtered queries over ChromaDB."""

    def __init__(self, settings: VectorDbSettings | None = None) -> None:
        self.settings = settings or vector_db_settings
        self._indexer = VectorDbIndexer(self.settings)

    def _build_filter(self, status: str | None, mandatory: bool | None, division: str | None) -> dict[str, Any] | None:
        """Construct valid ChromaDB filter clause combining multiple criteria."""
        clauses: list[dict[str, Any]] = []
        if status:
            clauses.append({"status": status})
        if mandatory is not None:
            clauses.append({"mandatory": mandatory})
        if division:
            clauses.append({"division_council": division.strip().upper()})
        return clauses[0] if len(clauses) == 1 else ({"$and": clauses} if clauses else None)

    def search(
        self,
        query_text: str,
        status_filter: str | None = "Active",
        mandatory_only: bool | None = None,
        division_council: str | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Perform semantic query with hybrid metadata filtering."""
        if not query_text.strip():
            return []

        collection = self._indexer.get_or_create_collection(recreate=False)
        where_filter = self._build_filter(status_filter, mandatory_only, division_council)
        n_results = min(top_k, max(collection.count(), 1))
        results = collection.query(query_texts=[query_text], n_results=n_results, where=where_filter)

        if not results or not results["ids"] or not results["ids"][0]:
            return []

        ids, dists = results["ids"][0], results.get("distances", [[0.0] * len(results["ids"][0])])[0]
        metas = results.get("metadatas", [[{}] * len(ids)])[0]
        docs = results.get("documents", [[""] * len(ids)])[0]

        return [
            {
                "chunk_id": doc_id,
                "standard_id": (metas[i] or {}).get("standard_id", ""),
                "is_number": (metas[i] or {}).get("is_number", ""),
                "year": (metas[i] or {}).get("year", 2015),
                "status": (metas[i] or {}).get("status", "Active"),
                "mandatory": (metas[i] or {}).get("mandatory", False),
                "qco_order_title": (metas[i] or {}).get("qco_order_title", ""),
                "bis_scheme": (metas[i] or {}).get("bis_scheme", ""),
                "division_council": (metas[i] or {}).get("division_council", ""),
                "product_category": (metas[i] or {}).get("product_category", ""),
                "similarity_score": round(max(0.0, 1.0 - float(dists[i])), 4),
                "distance": round(float(dists[i]), 4),
                "snippet": docs[i][:300] if docs[i] else "",
                "metadata": metas[i] or {},
            }
            for i, doc_id in enumerate(ids)
        ]


def search_standards(
    query_text: str,
    status_filter: str | None = "Active",
    mandatory_only: bool | None = None,
    division_council: str | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Global helper function for semantic retrieval over Indian Standards."""
    service = VectorDbSearchService()
    return service.search(query_text, status_filter, mandatory_only, division_council, top_k)
