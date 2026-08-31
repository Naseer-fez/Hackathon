# Phase 4: Observability & Continuous Evaluation

## Project Context

**BIS-SpecAI** is an AI-powered Indian Standards (BIS) recommendation engine for e-Procurement portals (GeM, CPPP, State/PSU Tenders). It uses a local GGUF model via `llama-cpp-python` on an NVIDIA RTX 3050 6GB GPU, with a FastAPI backend and React + TypeScript frontend.

The system is now accurate (Phase 1), generates constrained output with SSE streaming (Phase 2), and handles concurrency with caching (Phase 3). This final phase adds production monitoring and continuous AI quality evaluation.

**Project root:** `d:\CODE\Hackathon`

**Coding rules:** Read `d:\CODE\Hackathon\GEMINI.md` for project-wide coding constraints.

---

## Phase Objective

Provide production-level visibility into system health, GPU resource usage, and continuous RAG accuracy metrics. This phase creates a unified observability layer combining hardware telemetry with AI quality evaluation.

**Features to Build:**
1. Telemetry & Health Monitoring (Prometheus `/metrics` endpoint)
2. Automated RAG Triad Evaluation

**Why Combined:** Both involve extracting metrics from the running system. By building the Prometheus telemetry endpoint first, the RAG Triad evaluation scripts can publish their evaluation scores (Context Relevance, Faithfulness, Answer Relevance) directly to the telemetry endpoint, creating a unified dashboard of system health and AI quality.

---

## Prerequisites

**Phases 1, 2, and 3 must be completed first.** Assumes:
- Cross-Encoder reranking, query expansion, strict citations all operational
- GBNF grammar constraints applied to LLM generation
- SSE streaming working with `text/event-stream` format
- Semantic query cache operational in pipeline
- Async request queue with backpressure in place

---

## Files to Modify / Create

| File | Action | Purpose |
|---|---|---|
| `d:\CODE\Hackathon\backend\main.py` | MODIFY | Integrate Prometheus middleware + `/metrics` endpoint |
| `d:\CODE\Hackathon\backend\engine\rag_evaluation.py` | CREATE | RAG Triad evaluation engine |
| `d:\CODE\Hackathon\tests\test_rag_evaluation.py` | CREATE | Tests for RAG evaluation |
| `d:\CODE\Hackathon\tests\test_metrics.py` | CREATE | Tests for Prometheus metrics endpoint |

---

## Current Code: `main.py`

**Path:** `d:\CODE\Hackathon\backend\main.py` (96 lines)

```python
"""FastAPI application entry point for Indian Standards AI Recommendation Engine."""
from __future__ import annotations

from contextlib import asynccontextmanager
import time
from typing import Any, AsyncGenerator
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from backend.api.gem_webhook_router import router as gem_router
from backend.api.llm_router import router as llm_router
from backend.api.pipeline_router import router as pipeline_router
from backend.api.recommendation_router import router as rec_router
from backend.api.standards_router import router as std_router
from backend.api.tender_router import router as tender_router
from backend.config.settings import app_settings
from backend.data.seed_generator import generate_seed_data
from backend.engine.model_warmup import warmup_backend_ai_models
from backend.logger.app_logger import get_logger, setup_logging

logger = get_logger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context ensuring seed data, VRAM caching, and model warmup."""
    setup_logging()
    logger.info("BIS-SpecAI Backend initializing...")
    generate_seed_data()
    warmup_backend_ai_models()
    logger.info("BIS-SpecAI Backend ready to accept requests")
    yield
    logger.info("BIS-SpecAI Backend shutting down")


app = FastAPI(
    title="BIS Indian Standards AI Recommendation Engine",
    description="AI-powered recommendation engine for Indian Standards (IS), QCO compliance, and tender auditing.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next: Any) -> Response:
    """Log all incoming HTTP requests and response performance metrics."""
    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "127.0.0.1"
    logger.info(f"--> {request.method} {request.url.path} [Client: {client_ip}]")
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(f"<-- {request.method} {request.url.path} [{response.status_code}] ({elapsed_ms:.2f}ms)")
        return response
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(f"<-- {request.method} {request.url.path} [EXCEPTION: {type(exc).__name__} - {exc}] ({elapsed_ms:.2f}ms)")
        raise


app.include_router(rec_router)
app.include_router(tender_router)
app.include_router(std_router)
app.include_router(gem_router)
app.include_router(llm_router)
app.include_router(pipeline_router)


@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "Indian Standards AI Engine", "version": "1.0.0"}


def start_server() -> None:
    """Run uvicorn server with configured parameters."""
    uvicorn.run(
        "backend.main:app",
        host=app_settings.server.host,
        port=app_settings.server.port,
        log_level=app_settings.server.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    start_server()
```

**Key observations:**
- No Prometheus integration exists
- No `/metrics` endpoint
- The `log_requests_middleware` already tracks elapsed time — this can be instrumented with Prometheus histograms
- The `lifespan` context is the right place to initialize Prometheus collectors and GPU monitoring background tasks

---

## Task 4.1: Telemetry & Prometheus Metrics

**File:** `d:\CODE\Hackathon\backend\main.py`

### What to Build

Integrate `prometheus_client` with FastAPI to expose a `/metrics` endpoint tracking system health, GPU utilization, and inference performance.

### How to Build

1. **Add Prometheus instrumentation to `main.py`:**

   ```python
   from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
   from fastapi.responses import Response as RawResponse

   # Define metrics
   REQUEST_COUNT = Counter(
       "bisspecai_http_requests_total",
       "Total HTTP requests",
       ["method", "endpoint", "status_code"]
   )
   REQUEST_LATENCY = Histogram(
       "bisspecai_http_request_duration_seconds",
       "HTTP request latency in seconds",
       ["method", "endpoint"],
       buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
   )
   LLM_GENERATION_TOKENS = Counter(
       "bisspecai_llm_tokens_generated_total",
       "Total tokens generated by LLM"
   )
   LLM_INFERENCE_LATENCY = Histogram(
       "bisspecai_llm_inference_duration_seconds",
       "LLM inference latency in seconds",
       buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
   )
   VECTOR_SEARCH_LATENCY = Histogram(
       "bisspecai_vector_search_duration_seconds",
       "Vector search latency in seconds",
       buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
   )
   GPU_VRAM_USAGE = Gauge(
       "bisspecai_gpu_vram_bytes",
       "GPU VRAM allocation in bytes"
   )
   GPU_TEMPERATURE = Gauge(
       "bisspecai_gpu_temperature_celsius",
       "GPU temperature in Celsius"
   )
   CACHE_HITS = Counter(
       "bisspecai_cache_hits_total",
       "Total semantic cache hits"
   )
   CACHE_MISSES = Counter(
       "bisspecai_cache_misses_total",
       "Total semantic cache misses"
   )
   ```

2. **Instrument the existing `log_requests_middleware`:**

   Add to the middleware (after computing `elapsed_ms`):
   ```python
   REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status_code=str(response.status_code)).inc()
   REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(elapsed_ms / 1000.0)
   ```

3. **Add the `/metrics` endpoint:**

   ```python
   @app.get("/metrics")
   async def prometheus_metrics() -> RawResponse:
       """Prometheus metrics endpoint."""
       return RawResponse(
           content=generate_latest(),
           media_type=CONTENT_TYPE_LATEST,
       )
   ```

4. **Add GPU monitoring background task** in the `lifespan` context:

   ```python
   import asyncio
   import torch

   async def _poll_gpu_metrics() -> None:
       """Background task polling GPU metrics every 30 seconds."""
       while True:
           try:
               if torch.cuda.is_available():
                   GPU_VRAM_USAGE.set(torch.cuda.memory_allocated(0))
                   # For temperature, use pynvml or subprocess nvidia-smi
           except (RuntimeError, OSError) as exc:
               logger.warning(f"GPU metrics poll error: {exc}")
           await asyncio.sleep(30)

   # In lifespan, after warmup:
   gpu_task = asyncio.create_task(_poll_gpu_metrics())
   yield
   gpu_task.cancel()
   ```

5. **Export metric objects** so other modules can instrument themselves:
   - `local_gguf_provider.py` can import and use `LLM_INFERENCE_LATENCY` and `LLM_GENERATION_TOKENS`
   - `hybrid_retriever.py` can import and use `VECTOR_SEARCH_LATENCY`
   - `cache_service.py` can import and use `CACHE_HITS` and `CACHE_MISSES`

   Create a shared metrics module at `d:\CODE\Hackathon\backend\metrics.py` to define all Prometheus objects in one place, then import from there.

### Acceptance Criteria
- [ ] `/metrics` endpoint returns valid Prometheus text format
- [ ] HTTP request count and latency are tracked per endpoint
- [ ] GPU VRAM usage is reported as a Prometheus Gauge
- [ ] GPU temperature is reported (via `pynvml`, `torch`, or `nvidia-smi` subprocess)
- [ ] LLM inference latency is tracked
- [ ] Vector search latency is tracked
- [ ] Cache hit/miss counters are tracked
- [ ] All metric names are prefixed with `bisspecai_`
- [ ] Background GPU polling task starts on boot and stops on shutdown

---

## Task 4.2: Automated RAG Triad Evaluation

**File:** CREATE `d:\CODE\Hackathon\backend\engine\rag_evaluation.py`

### What to Build

An automated evaluation engine that periodically grades the system's output quality using the RAG Triad: Context Relevance, Groundedness/Faithfulness, and Answer Relevance.

### How to Build

1. **Create the `RagEvaluator` class:**

   ```python
   # d:\CODE\Hackathon\backend\engine\rag_evaluation.py

   class RagTriadResult(BaseModel):
       """Result of a single RAG triad evaluation."""
       query: str
       context_relevance_score: float  # 0.0 - 1.0
       groundedness_score: float       # 0.0 - 1.0
       answer_relevance_score: float   # 0.0 - 1.0
       overall_score: float            # average of the three
       evaluation_details: dict[str, str]  # per-metric reasoning
       evaluated_at: str               # ISO timestamp

   class RagEvaluator:
       """Automated RAG Triad evaluation using LLM-as-judge."""

       def __init__(self) -> None:
           self._llm_provider = ...  # Get the LLM provider
           self._retriever = ...     # Get the retriever

       async def evaluate_single(
           self, query: str, retrieved_chunks: list[str], generated_response: str
       ) -> RagTriadResult:
           """Evaluate a single query-response pair against the RAG triad."""
           ...

       async def evaluate_batch(
           self, test_cases: list[dict[str, str]]
       ) -> list[RagTriadResult]:
           """Evaluate a batch of test cases."""
           ...

       async def run_golden_dataset_evaluation(self) -> list[RagTriadResult]:
           """Run evaluation against a predefined golden dataset."""
           ...
   ```

2. **Implement the three evaluation dimensions:**

   Each dimension uses a structured LLM call (reusing the local GGUF model) with a specific evaluation prompt:

   **Context Relevance** — "Given the user query: '{query}', rate from 0.0 to 1.0 how relevant the following retrieved chunks are to answering the query:"
   ```
   Retrieved chunks: {chunks}
   Score (0.0-1.0):
   Reasoning:
   ```

   **Groundedness / Faithfulness** — "Given the following context chunks and the generated response, rate from 0.0 to 1.0 how well the response is grounded in (supported by) the provided chunks. A score of 1.0 means every claim in the response is directly verifiable from the chunks:"
   ```
   Context: {chunks}
   Response: {response}
   Score (0.0-1.0):
   Reasoning:
   ```

   **Answer Relevance** — "Given the user query: '{query}' and the generated response, rate from 0.0 to 1.0 how directly and completely the response addresses the original question:"
   ```
   Query: {query}
   Response: {response}
   Score (0.0-1.0):
   Reasoning:
   ```

3. **Create a golden test dataset** at a configurable path (e.g., `d:\CODE\Hackathon\data\rag_golden_dataset.json`):
   ```json
   [
     {"query": "What BIS standard applies to TMT steel bars?", "expected_standard": "IS 1786"},
     {"query": "Solar panel standards for government buildings", "expected_standard": "IS 14286"},
     {"query": "Portland cement specifications", "expected_standard": "IS 269"},
     {"query": "PVC insulated cables for house wiring", "expected_standard": "IS 694"},
     {"query": "LED bulb energy efficiency standards", "expected_standard": "IS 16102"}
   ]
   ```

4. **Integrate with Prometheus metrics** (from Task 4.1):
   After each evaluation, update Prometheus Gauges:
   ```python
   from backend.metrics import RAG_CONTEXT_RELEVANCE, RAG_GROUNDEDNESS, RAG_ANSWER_RELEVANCE

   RAG_CONTEXT_RELEVANCE.set(result.context_relevance_score)
   RAG_GROUNDEDNESS.set(result.groundedness_score)
   RAG_ANSWER_RELEVANCE.set(result.answer_relevance_score)
   ```

5. **Add an API endpoint** for triggering evaluation (optional, for admin use):
   Add to `main.py` or create a new `metrics_router.py`:
   ```python
   @app.post("/api/v1/admin/evaluate-rag")
   async def trigger_rag_evaluation() -> list[RagTriadResult]:
       evaluator = RagEvaluator()
       results = await evaluator.run_golden_dataset_evaluation()
       return results
   ```

### Acceptance Criteria
- [ ] `RagEvaluator` class created with `evaluate_single()`, `evaluate_batch()`, and `run_golden_dataset_evaluation()` methods
- [ ] All three RAG Triad dimensions are evaluated: Context Relevance, Groundedness, Answer Relevance
- [ ] Each evaluation returns a score between 0.0 and 1.0 with reasoning
- [ ] Golden test dataset exists with at least 5 representative queries
- [ ] Evaluation scores are published to Prometheus Gauges
- [ ] Golden dataset path is configurable (not hardcoded)
- [ ] An API endpoint exists to trigger evaluation on demand

---

## Verification Plan

### Automated Tests

```powershell
# Run all tests
python -m pytest tests/ -v

# Run specific tests
python -m pytest tests/test_rag_evaluation.py -v
python -m pytest tests/test_metrics.py -v
```

Write tests covering:

1. **Metrics Endpoint Test:** Use FastAPI `TestClient` to GET `/metrics` and verify:
   - Response status is 200
   - Response body contains `bisspecai_http_requests_total`
   - Response body contains `bisspecai_gpu_vram_bytes`
2. **RAG Evaluator Unit Test:** Mock the LLM provider and verify:
   - `evaluate_single()` returns a `RagTriadResult` with scores in [0.0, 1.0]
   - All three dimensions are populated
3. **Golden Dataset Test:** Verify the golden dataset JSON loads correctly and contains required fields.
4. **Prometheus Counter Test:** Make a request, then check `/metrics` to verify counter incremented.

### Manual Verification

```powershell
# Start backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Test Prometheus metrics endpoint
curl http://127.0.0.1:8000/metrics
# Expected: Prometheus text format with bisspecai_* metrics
# Should include:
#   bisspecai_http_requests_total{method="GET",endpoint="/metrics",status_code="200"} 1.0
#   bisspecai_gpu_vram_bytes 1234567.0
#   bisspecai_gpu_temperature_celsius 45.0

# Test RAG evaluation endpoint
curl -X POST http://127.0.0.1:8000/api/v1/admin/evaluate-rag
# Expected: JSON array of RagTriadResult objects with scores for each golden query
# Example:
# [
#   {
#     "query": "What BIS standard applies to TMT steel bars?",
#     "context_relevance_score": 0.92,
#     "groundedness_score": 0.88,
#     "answer_relevance_score": 0.95,
#     "overall_score": 0.917,
#     "evaluation_details": {...},
#     "evaluated_at": "2026-08-31T12:00:00+05:30"
#   },
#   ...
# ]

# Verify RAG scores appear in Prometheus after evaluation
curl http://127.0.0.1:8000/metrics | findstr "rag"
# Expected:
#   bisspecai_rag_context_relevance 0.92
#   bisspecai_rag_groundedness 0.88
#   bisspecai_rag_answer_relevance 0.95
```

---

## Expected Outcome

After Phase 4 completion:
- `/metrics` endpoint provides full Prometheus-compatible telemetry
- GPU VRAM and temperature are continuously monitored
- HTTP request counts, latencies, cache hits/misses are all tracked
- RAG Triad evaluation can be triggered on demand against a golden dataset
- Context Relevance, Groundedness, and Answer Relevance scores are published to Prometheus
- Administrators have full visibility into both system health and AI output quality

---

## Full Project Completion Summary

With all four phases complete, the BIS-SpecAI system will have:

| Capability | Phase |
|---|---|
| Query Expansion & Domain Normalization | Phase 1 |
| Cross-Encoder Reranking | Phase 1 |
| Strict Citation Format `[IS Number:Year, Clause X.Y, Page Z]` | Phase 1 |
| GBNF Grammar Constraints (Zero Hallucination) | Phase 2 |
| Proper SSE Streaming | Phase 2 |
| Semantic Query Caching (<5ms for repeat queries) | Phase 3 |
| Async Request Queue with Backpressure (HTTP 429) | Phase 3 |
| Prometheus Telemetry & GPU Monitoring | Phase 4 |
| Automated RAG Triad Evaluation | Phase 4 |
