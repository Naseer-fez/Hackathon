"""Unit and integration tests for BIS Vector Database pipeline."""
from __future__ import annotations

import tempfile
import pytest
from backend.vectordb.config import VectorDbSettings
from backend.vectordb.embedding_function import SentenceTransformerEmbeddingFunction
from backend.vectordb.indexer import VectorDbIndexer
from backend.vectordb.search_service import VectorDbSearchService
from backend.vectordb.semantic_chunker import SemanticChunker
from backend.vectordb.taxonomy_enricher import TaxonomyEnricher


def test_vector_db_settings() -> None:
    """Test vector db settings initialization and paths."""
    settings = VectorDbSettings()
    assert "vectordb" in settings.db_path
    assert settings.collection_name == "bis_standards_catalog"
    assert settings.standards_master_path.name == "standards_master.json"


def test_embedding_function() -> None:
    """Test embedding function generates normalized float vectors."""
    embed_fn = SentenceTransformerEmbeddingFunction()
    docs = ["IS 269 Ordinary Portland Cement", "IS 1786 TMT Steel Bars"]
    embeddings = embed_fn(docs)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert isinstance(float(embeddings[0][0]), float)


def test_taxonomy_enricher() -> None:
    """Test abbreviation detection and Indic dictionary enrichment."""
    enricher = TaxonomyEnricher()
    abbrs = enricher.get_abbreviations_for_text("Requires XLPE insulation and FRLS sheath")
    assert any("XLPE" in a for a in abbrs)
    trade_terms = enricher.get_trade_terms_for_standard("IS 1786:2008")
    assert any("TMT" in t for t in trade_terms)
    indic = enricher.get_indic_terms_for_standard("IS 1786:2008")
    assert "Hindi" in indic["scripts"] or "Hindi" in indic["transliterations"]


def test_semantic_chunker() -> None:
    """Test semantic chunking with taxonomy injection and metadata creation."""
    chunker = SemanticChunker()
    sample_std = {
        "standard_id": "IS 269:2015",
        "is_number": "IS 269",
        "year": 2015,
        "title": "Ordinary Portland Cement",
        "scope": "Covers manufacture and chemical requirements of 33, 43, 53 grade cement.",
        "status": "Active",
        "division_council": "CED - Civil Engineering Division Council",
        "technical_committee": "CED 2",
        "sector": "Civil Engineering",
        "product_category": "Cement",
        "certification_mandatory": True,
        "materials_covered": ["Clinker", "Gypsum"],
    }
    doc_text, chunk_id, meta = chunker.build_chunk(sample_std)
    assert "IS 269:2015" in doc_text
    assert meta["mandatory"] is True
    assert meta["year"] == 2015
    assert meta["status"] == "Active"


def test_indexer_and_search() -> None:
    """Test indexing and hybrid search on a temporary ChromaDB instance."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        settings = VectorDbSettings(db_path=tmp_dir, collection_name="test_standards")
        indexer = VectorDbIndexer(settings=settings)
        indexed_count = indexer.index_all(recreate=True, limit=5)
        assert indexed_count == 5
        assert indexer.get_collection_count() == 5

        service = VectorDbSearchService(settings=settings)
        results = service.search(query_text="cement concrete specification", top_k=2)
        assert len(results) > 0
        assert "similarity_score" in results[0]
        assert "standard_id" in results[0]
