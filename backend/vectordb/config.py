"""Configuration settings for the Indian Standards Vector Database."""
from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel, Field


class VectorDbSettings(BaseModel):
    """Configuration parameters for ChromaDB and embedding models."""

    # Store 1: Catalog Metadata Store
    catalog_db_path: str = Field(
        default_factory=lambda: os.getenv("VECTORDB_PATH", "D:/CODE/Hackathon/vectordb")
    )
    catalog_collection_name: str = Field(
        default_factory=lambda: os.getenv("VECTORDB_COLLECTION", "bis_standards_catalog")
    )

    # Store 2: Granular PDF Document Chunks Store
    document_db_path: str = Field(
        default_factory=lambda: os.getenv("DOCUMENT_VECTORDB_PATH", "D:/CODE/Hackathon/vectordb/data/chroma")
    )
    document_collection_name: str = Field(
        default_factory=lambda: os.getenv("DOCUMENT_VECTORDB_COLLECTION", "document_chunks")
    )
    source_repo_path: str = Field(
        default_factory=lambda: os.getenv(
            "SOURCE_REPO_PATH",
            "D:/Extras/ES/Scrapiing/teamwork_is_knowledge_base",
        )
    )
    embedding_model_name: str = Field(
        default_factory=lambda: os.getenv(
            "VECTORDB_EMBEDDING_MODEL",
            "d:/CODE/Hackathon/llm/all-MiniLM-L6-v2",
        )
    )
    batch_size: int = Field(
        default_factory=lambda: int(os.getenv("VECTORDB_BATCH_SIZE", "64"))
    )
    similarity_threshold: float = Field(
        default_factory=lambda: float(
            os.getenv("VECTORDB_SIMILARITY_THRESHOLD", "0.35")
        )
    )

    @property
    def db_path(self) -> str:
        """Backward compatible alias for catalog DB path."""
        return self.catalog_db_path

    @property
    def collection_name(self) -> str:
        """Backward compatible alias for catalog collection name."""
        return self.catalog_collection_name

    @property
    def standards_master_path(self) -> Path:
        """Path to master catalog JSON file."""
        return (
            Path(self.source_repo_path)
            / "data"
            / "processed"
            / "standards_master.json"
        )

    @property
    def qco_registry_path(self) -> Path:
        """Path to statutory QCO registry JSON file."""
        return (
            Path(self.source_repo_path)
            / "data"
            / "processed"
            / "qco_registry.json"
        )

    @property
    def knowledge_graph_path(self) -> Path:
        """Path to knowledge graph GraphML file."""
        return (
            Path(self.source_repo_path)
            / "data"
            / "graph"
            / "knowledge_graph.graphml"
        )


def load_vector_db_settings() -> VectorDbSettings:
    """Load settings instance with environment variable overrides."""
    return VectorDbSettings()


vector_db_settings: VectorDbSettings = load_vector_db_settings()
