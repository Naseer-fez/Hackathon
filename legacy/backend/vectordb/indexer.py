"""Persistent Vector DB indexer for Indian Standards knowledge base."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
import chromadb
from chromadb.api.models.Collection import Collection
from backend.vectordb.config import VectorDbSettings, vector_db_settings
from backend.vectordb.embedding_function import SentenceTransformerEmbeddingFunction
from backend.vectordb.semantic_chunker import SemanticChunker


class VectorDbIndexer:
    """Manages embedding generation and indexing into persistent ChromaDB."""

    def __init__(self, settings: VectorDbSettings | None = None) -> None:
        self.settings = settings or vector_db_settings
        Path(self.settings.db_path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.settings.db_path)
        self._embed_fn = SentenceTransformerEmbeddingFunction(
            model_name=self.settings.embedding_model_name
        )
        self._chunker = SemanticChunker()
        self._ensure_sys_path()

    def _ensure_sys_path(self) -> None:
        """Add source repo to python path for importing source modules."""
        repo_path = str(self.settings.source_repo_path)
        if repo_path not in sys.path:
            sys.path.insert(0, repo_path)

    def get_or_create_collection(self, recreate: bool = False) -> Collection:
        """Get or recreate the ChromaDB collection with cosine similarity."""
        if recreate:
            try:
                self._client.delete_collection(self.settings.collection_name)
            except (ValueError, KeyError, Exception):
                pass
        return self._client.get_or_create_collection(
            name=self.settings.collection_name,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def index_all(self, recreate: bool = False, limit: int | None = None) -> int:
        """Load standards from master catalog, chunk, embed, and persist into ChromaDB."""
        from src.corpus.catalog import MasterStandardsCatalog
        from src.regulatory.qco_registry import QCORegistry

        catalog = MasterStandardsCatalog(auto_load=False)
        catalog.load_from_json(str(self.settings.standards_master_path))
        qco_reg = QCORegistry()

        collection = self.get_or_create_collection(recreate=recreate)
        all_standards = catalog.list_all_standards()
        if limit:
            all_standards = all_standards[:limit]

        ids: list[str] = []
        docs: list[str] = []
        metas: list[dict[str, Any]] = []
        total_indexed = 0
        batch_size = self.settings.batch_size

        for std in all_standards:
            qco = qco_reg.get_qco_for_standard(std.is_number or std.standard_id)
            doc_text, chunk_id, metadata = self._chunker.build_chunk(std, qco)
            ids.append(chunk_id)
            docs.append(doc_text)
            metas.append(metadata)

            if len(ids) >= batch_size:
                collection.upsert(ids=ids, documents=docs, metadatas=metas)
                total_indexed += len(ids)
                ids, docs, metas = [], [], []

        if ids:
            collection.upsert(ids=ids, documents=docs, metadatas=metas)
            total_indexed += len(ids)

        return total_indexed

    def get_collection_count(self) -> int:
        """Return total document count currently indexed in the collection."""
        collection = self.get_or_create_collection(recreate=False)
        return collection.count()
