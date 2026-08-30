import logging
from typing import List, Dict, Any, Optional
from .config import TOP_K
from .embeddings import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class DocumentSearcher:
    """Provides high-level semantic search capabilities over the ChromaDB vector store."""
    
    def __init__(self, vector_store: Optional[VectorStore] = None, embedding_service: Optional[EmbeddingService] = None):
        self.vector_store = vector_store or VectorStore()
        self.embedding_service = embedding_service or EmbeddingService()

    def search(self, query_text: str, top_k: int = TOP_K, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Executes semantic search for a given query text.
        
        Args:
            query_text: The user natural language query.
            top_k: Number of top relevant chunks to return.
            category_filter: Optional folder_category to filter search results.
            
        Returns:
            List of result dictionaries sorted by relevance score.
        """
        if not query_text or not query_text.strip():
            logger.warning("Empty query provided to search.")
            return []
            
        query_text = query_text.strip()
        results = self.vector_store.query(
            query_text=query_text, 
            embedding_service=self.embedding_service, 
            top_k=top_k,
            category_filter=category_filter
        )
        
        formatted = []
        if not results or not results.get('documents') or not results['documents'][0]:
            return formatted

        docs = results['documents'][0]
        metas = results['metadatas'][0]
        distances = results['distances'][0]
        ids = results['ids'][0]

        for rank, (chunk_id, doc, meta, dist) in enumerate(zip(ids, docs, metas, distances), start=1):
            # Chroma returns L2 distance / cosine distance depending on config.
            # For cosine distance, similarity can be represented as (1 - distance) or normalized.
            # We provide raw distance and a computed similarity score.
            similarity_score = max(0.0, 1.0 - (dist / 2.0)) if dist <= 2.0 else max(0.0, 1.0 / (1.0 + dist))
            
            formatted.append({
                "rank": rank,
                "chunk_id": chunk_id,
                "score": round(similarity_score, 4),
                "distance": round(dist, 4),
                "file_name": meta.get("file_name", "Unknown"),
                "page_number": meta.get("page_number", 0),
                "total_pages": meta.get("total_pages", 0),
                "folder_category": meta.get("folder_category", "Unknown"),
                "doc_id": meta.get("doc_id", "Unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "text": doc
            })
            
        return formatted
