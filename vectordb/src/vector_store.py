import chromadb
import logging
import gc
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from .config import CHROMA_DIR, COLLECTION_NAME, BATCH_SIZE

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, chroma_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.chroma_dir = str(chroma_dir or CHROMA_DIR)
        self.collection_name = collection_name or COLLECTION_NAME
        
        logger.info(f"Connecting to ChromaDB at {self.chroma_dir}...")
        self.client = chromadb.PersistentClient(path=self.chroma_dir)
        
        # Using cosine distance space for normalized semantic embeddings
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Collection '{self.collection_name}' ready. Currently contains {self.collection.count()} vectors.")

    def validate_chunks_before_store(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validates chunk data prior to embedding/storing.
        Checks for empty text, missing IDs, missing metadata, and duplicates in the current batch.
        """
        seen_ids = set()
        valid_chunks = []
        
        for idx, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id")
            text = chunk.get("text", "")
            
            if not chunk_id:
                logger.error(f"Chunk at index {idx} has missing 'chunk_id'. Skipping.")
                continue
                
            if chunk_id in seen_ids:
                logger.warning(f"Duplicate chunk ID '{chunk_id}' found in batch. Keeping first occurrence.")
                continue
            seen_ids.add(chunk_id)
            
            if not text or not str(text).strip():
                logger.warning(f"Chunk '{chunk_id}' has empty text. Skipping.")
                continue
                
            if len(str(text).strip()) < 5:
                logger.warning(f"Chunk '{chunk_id}' has suspiciously short text ({len(str(text).strip())} chars). Skipping.")
                continue
                
            # Verify required metadata fields
            required_meta = ["doc_id", "file_name", "folder_category", "page_number", "total_pages", "chunk_index"]
            missing_keys = [k for k in required_meta if k not in chunk]
            if missing_keys:
                logger.warning(f"Chunk '{chunk_id}' is missing metadata keys: {missing_keys}. Skipping.")
                continue
                
            valid_chunks.append(chunk)
            
        logger.info(f"Validation complete: {len(valid_chunks)}/{len(chunks)} chunks passed validation.")
        return valid_chunks

    def store_chunks(self, chunks: List[Dict[str, Any]], embedding_service, batch_size: int = BATCH_SIZE):
        """
        Embeds and stores chunks in batches into ChromaDB with safe upsert behavior.
        """
        valid_chunks = self.validate_chunks_before_store(chunks)
        if not valid_chunks:
            logger.warning("No valid chunks to store.")
            return
            
        total_chunks = len(valid_chunks)
        logger.info(f"Writing to Chroma in batches of {batch_size}...")
        
        for i in tqdm(range(0, total_chunks, batch_size), desc="Ingesting batches"):
            batch = valid_chunks[i:i + batch_size]
            
            texts = [chunk['text'] for chunk in batch]
            ids = [chunk['chunk_id'] for chunk in batch]
            
            metadatas = [
                {
                    "doc_id": str(c["doc_id"]),
                    "file_name": str(c["file_name"]),
                    "folder_category": str(c["folder_category"]),
                    "page_number": int(c["page_number"]),
                    "total_pages": int(c["total_pages"]),
                    "chunk_index": int(c["chunk_index"])
                }
                for c in batch
            ]
            
            # Generate embeddings
            embeddings = embedding_service.embed_batch(texts)
            
            # Validate embedding dimensions
            if embeddings and len(embeddings[0]) != embedding_service.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {embedding_service.dimension}, got {len(embeddings[0])}"
                )
                
            # Upsert into Chroma (updates existing IDs or inserts new ones)
            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            # Force garbage collection between batches
            gc.collect()
            
        logger.info(f"Successfully upserted {total_chunks} chunks into Chroma collection '{self.collection_name}'. Total in collection: {self.collection.count()}")

    def query(self, query_text: str, embedding_service, top_k: int = 5, category_filter: Optional[str] = None):
        """Queries the vector store for top_k most similar chunks."""
        query_embedding = embedding_service.embed_batch([query_text])[0]
        
        where_clause = {"folder_category": category_filter} if category_filter else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Returns collection statistics."""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_vectors": count,
            "chroma_dir": self.chroma_dir
        }
