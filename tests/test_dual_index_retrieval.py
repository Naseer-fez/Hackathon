"""Unit and integration tests for Dual-Index Hierarchical Retrieval."""
from __future__ import annotations
import pytest
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.llm_orchestrator import LlmOrchestrator
from backend.engine.llm_providers import UnavailableLlmProvider
from backend.engine.llm_service import LlmService, _format_chunk_context
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.llm_contracts import LlmInputContract
from backend.models.recommendation_model import DocumentChunkEvidence
from backend.vectordb.search_service import VectorDbSearchService


def test_vectordb_search_document_chunks() -> None:
    svc = VectorDbSearchService()
    results = svc.search_document_chunks(query="ordinary portland cement", top_k=2)
    assert isinstance(results, list)
    if results:
        first = results[0]
        assert "file_name" in first
        assert "page_number" in first
        assert "snippet" in first
        assert isinstance(first["page_number"], int)


def test_vectordb_search_dual_index() -> None:
    svc = VectorDbSearchService()
    dual = svc.search_dual_index(query="steel wire tensile strength", top_k_catalog=2, top_k_documents=2)
    assert "standards" in dual
    assert "document_chunks" in dual
    assert isinstance(dual["standards"], list)
    assert isinstance(dual["document_chunks"], list)


def test_hybrid_retriever_search_with_evidence() -> None:
    retriever = HybridRetriever()
    standards, evidences = retriever.search_with_evidence(query="ordinary portland cement", top_k=2, top_k_chunks=2)
    assert len(standards) > 0
    assert isinstance(evidences, list)
    if evidences:
        assert isinstance(evidences[0], DocumentChunkEvidence)
        assert hasattr(evidences[0], "page_number")
        assert hasattr(evidences[0], "file_name")


def test_format_chunk_context_and_lmm_service() -> None:
    chunks = [
        DocumentChunkEvidence(
            chunk_id="c1", doc_id="d1", file_name="IS_269.pdf",
            page_number=4, total_pages=10, folder_category="Standard",
            snippet="Compressive strength 33 Grade shall not be less than 33 MPa.",
            relevance_score=0.92,
        )
    ]
    ctx = _format_chunk_context(chunks)
    assert "IS_269.pdf" in ctx
    assert "Page 4" in ctx
    assert "33 MPa" in ctx


@pytest.mark.asyncio
async def test_lmm_orchestrator_dual_index_grounding() -> None:
    orchestrator = LlmOrchestrator(cloud=UnavailableLlmProvider(), local=UnavailableLlmProvider())
    loader = StandardsLoader()
    std = loader.get_all_standards()[0]
    contract = LlmInputContract(
        query="Cement tensile and compressive testing",
        candidate_standards=[std],
        document_chunks=[{
            "file_name": "IS_269_spec.pdf",
            "page_number": 5,
            "snippet": "Setting time initial minimum 30 minutes",
        }],
    )
    res = await orchestrator.execute(contract)
    assert res.primary_is_code == std.is_code
    assert len(res.cited_clauses) > 0
    assert "IS_269_spec.pdf" in res.cited_clauses[0]
