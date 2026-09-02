"""Unit tests for document chunk reranker."""
from __future__ import annotations
from backend.engine.document_chunk_reranker import DocumentChunkReranker, chunk_document_text


def test_chunk_document_text_empty() -> None:
    assert chunk_document_text("") == []


def test_chunk_document_text_basic() -> None:
    text = "A" * 1200
    chunks = chunk_document_text(text, chunk_size=500, overlap=50)
    assert len(chunks) >= 3


def test_retrieve_and_rerank_chunks() -> None:
    sample_text = (
        "IS 456 is the code of practice for plain and reinforced concrete. "
        "IS 1786 covers high strength deformed steel bars and wires for concrete reinforcement. "
        "IS 800 covers general construction in steel and structural steel design."
    )
    reranker = DocumentChunkReranker()
    results = reranker.retrieve_and_rerank_chunks("reinforced concrete code", sample_text, top_k=2)
    assert isinstance(results, list)
    if results:
        assert "text" in results[0]
        assert "score" in results[0]
