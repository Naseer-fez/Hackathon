"""Hybrid semantic retrieval and dual-index search service for Indian Standards."""
from __future__ import annotations
from typing import Any
import chromadb
from backend.vectordb.config import VectorDbSettings, vector_db_settings
from backend.vectordb.indexer import VectorDbIndexer
class VectorDbSearchService:
    """Provides dual-index semantic search over standards catalog and document chunks."""

    def __init__(self, settings: VectorDbSettings | None = None) -> None:
        self.settings = settings or vector_db_settings
        self._indexer = VectorDbIndexer(self.settings)
        self._doc_client: chromadb.PersistentClient | None = None
        self._doc_col: Any = None

    def _get_doc_col(self) -> Any:
        """Get or initialize document chunks collection client."""
        if self._doc_col is None:
            self._doc_client = chromadb.PersistentClient(path=self.settings.document_db_path)
            self._doc_col = self._doc_client.get_collection(self.settings.document_collection_name)
        return self._doc_col

    def _build_filter(self, status: str | None, mandatory: bool | None, div: str | None) -> dict[str, Any] | None:
        clauses = [{"status": status}] if status else []
        if mandatory is not None:
            clauses.append({"mandatory": mandatory})
        if div:
            clauses.append({"division_council": div.strip().upper()})
        return clauses[0] if len(clauses) == 1 else ({"$and": clauses} if clauses else None)

    def search(
        self, query_text: str = "", query: str = "", status: str | None = "Active",
        mandatory: bool | None = None, division: str | None = None, top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Perform semantic query over standards catalog collection."""
        q = (query_text or query).strip()
        if not q:
            return []
        col = self._indexer.get_or_create_collection(recreate=False)
        filt = self._build_filter(status, mandatory, division)
        try:
            res = col.query(query_texts=[q], n_results=min(top_k, max(col.count(), 1)), where=filt)
        except (chromadb.errors.ChromaError, ValueError, Exception):
            res = col.query(query_texts=[q], n_results=min(top_k, max(col.count(), 1)))
        if not res or not res["ids"] or not res["ids"][0]:
            return []
        ids, dists = res["ids"][0], res.get("distances", [[0.0] * len(res["ids"][0])])[0]
        metas, docs = res.get("metadatas", [[{}] * len(ids)])[0], res.get("documents", [[""] * len(ids)])[0]
        return [
            {
                "chunk_id": doc_id, "standard_id": (metas[i] or {}).get("standard_id", ""),
                "is_number": (metas[i] or {}).get("is_number", ""), "year": (metas[i] or {}).get("year", 2015),
                "status": (metas[i] or {}).get("status", "Active"), "mandatory": (metas[i] or {}).get("mandatory", False),
                "qco_order_title": (metas[i] or {}).get("qco_order_title", ""), "bis_scheme": (metas[i] or {}).get("bis_scheme", ""),
                "division_council": (metas[i] or {}).get("division_council", ""), "product_category": (metas[i] or {}).get("product_category", ""),
                "similarity_score": round(max(0.0, 1.0 - float(dists[i])), 4), "distance": round(float(dists[i]), 4),
                "snippet": docs[i][:300] if docs[i] else "", "metadata": metas[i] or {},
            }
            for i, doc_id in enumerate(ids)
        ]

    def search_document_chunks(self, query: str = "", query_text: str = "", top_k: int = 5, category: str | None = None) -> list[dict[str, Any]]:
        """Perform dense vector retrieval over granular PDF document text chunks."""
        q = (query or query_text).strip()
        if not q:
            return []
        try:
            col = self._get_doc_col()
            q_emb = self._indexer._embed_fn([q])
            filt = {"folder_category": category} if category else None
            res = col.query(query_embeddings=q_emb, n_results=min(top_k, max(col.count(), 1)), where=filt)
            if not res or not res["ids"] or not res["ids"][0]:
                return []
            ids, dists = res["ids"][0], res.get("distances", [[0.0] * len(res["ids"][0])])[0]
            metas, docs = res.get("metadatas", [[{}] * len(ids)])[0], res.get("documents", [[""] * len(ids)])[0]
            return [
                {
                    "chunk_id": doc_id, "doc_id": (metas[i] or {}).get("doc_id", ""),
                    "file_name": (metas[i] or {}).get("file_name", ""), "page_number": int((metas[i] or {}).get("page_number", 1)),
                    "total_pages": int((metas[i] or {}).get("total_pages", 1)), "folder_category": (metas[i] or {}).get("folder_category", "Standard"),
                    "similarity_score": round(max(0.0, 1.0 - float(dists[i])), 4), "distance": round(float(dists[i]), 4),
                    "snippet": docs[i] if docs[i] else "", "metadata": metas[i] or {},
                }
                for i, doc_id in enumerate(ids)
            ]
        except (chromadb.errors.ChromaError, KeyError, ValueError, Exception):
            return []

    def search_dual_index(self, query: str, top_k_catalog: int = 5, top_k_documents: int = 5) -> dict[str, Any]:
        """Perform unified dual-index search querying catalog and granular chunks."""
        return {
            "standards": self.search(query=query, top_k=top_k_catalog),
            "document_chunks": self.search_document_chunks(query=query, top_k=top_k_documents),
        }

def search_standards(query_text: str, top_k: int = 10) -> list[dict[str, Any]]:
    """Global helper for semantic retrieval over Indian Standards catalog."""
    return VectorDbSearchService().search(query=query_text, top_k=top_k)
