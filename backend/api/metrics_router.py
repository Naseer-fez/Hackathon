"""API router for Prometheus metrics and RAG evaluation."""
from fastapi import APIRouter
from fastapi.responses import Response as RawResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from backend.engine.rag_evaluation import RagEvaluator, RagTriadResult

router = APIRouter(tags=["metrics"])

@router.get("/metrics")
async def prometheus_metrics() -> RawResponse:
    """Prometheus metrics endpoint."""
    return RawResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

@router.post("/api/v1/admin/evaluate-rag")
async def trigger_rag_evaluation() -> list[RagTriadResult]:
    """Trigger RAG triad evaluation against golden dataset."""
    evaluator = RagEvaluator()
    results = await evaluator.run_golden_dataset_evaluation()
    return results
