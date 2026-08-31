# Phase 3: Performance & Concurrency

## Project Context

**BIS-SpecAI** is an AI-powered Indian Standards (BIS) recommendation engine for e-Procurement portals (GeM, CPPP, State/PSU Tenders). It uses a local GGUF model via `llama-cpp-python` on an NVIDIA RTX 3050 6GB GPU (6GB VRAM) for inference, with a FastAPI backend and React + TypeScript frontend.

The system runs on a single GPU — concurrent LLM requests will crash or timeout if not properly managed. This phase ensures the system scales gracefully under load.

**Project root:** `d:\CODE\Hackathon`

**Coding rules:** Read `d:\CODE\Hackathon\GEMINI.md` for project-wide coding constraints.

---

## Phase Objective

Ensure the system scales efficiently under concurrent load by:
1. Caching semantically similar queries to avoid redundant GPU computation
2. Replacing the naive `threading.Lock()` with an async request queue that provides backpressure and queue position feedback

**Features to Build:**
1. Semantic Query Caching
2. Asynchronous Request Queue & Backpressure

**Why Combined:** Both are concurrency optimizations forming a complete request-handling pipeline. When a request arrives: check cache first (sub-5ms response on hit) → if cache miss, enter the async queue → queue protects GPU from overload. Implementing them together creates the full fast-path.

---

## Prerequisites

**Phases 1 and 2 must be completed first.** Assumes:
- Cross-Encoder reranking and query expansion are operational in `hybrid_retriever.py`
- GBNF grammar constraints are applied to LLM generation
- SSE streaming is working with proper `text/event-stream` format in `llm_router.py`
- Citations follow `[IS Number:Year, Clause X.Y, Page Z]` format

---

## Files to Modify / Create

| File | Action | Purpose |
|---|---|---|
| `d:\CODE\Hackathon\backend\engine\cache_service.py` | CREATE | Semantic query cache using SQLite |
| `d:\CODE\Hackathon\backend\engine\pipeline.py` | MODIFY | Integrate cache check before retrieval + LLM |
| `d:\CODE\Hackathon\backend\engine\local_gguf_provider.py` | MODIFY | Replace threading.Lock with asyncio.Queue |
| `d:\CODE\Hackathon\tests\test_cache_service.py` | CREATE | Tests for cache service |
| `d:\CODE\Hackathon\tests\test_backpressure.py` | CREATE | Tests for async queue + backpressure |

---

## Current Code: `pipeline.py`

**Path:** `d:\CODE\Hackathon\backend\engine\pipeline.py` (98 lines)

```python
"""Unified multi-modal pipeline for Indian Standards recommendation and QCO compliance."""
from __future__ import annotations
import base64
import tempfile
from pydantic import BaseModel, Field
from backend.engine.certification_advisor import CertificationAdvisor
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.llm_orchestrator import LlmOrchestrator
from backend.engine.multilingual_processor import MultilingualProcessor
from backend.engine.normative_resolver import NormativeResolver
from backend.engine.tender_clause_generator import TenderClauseGenerator
from backend.engine.voice_service import VoiceService
from backend.models.llm_contracts import LlmInputContract, LlmStandardizedResponse
from backend.models.recommendation_model import DocumentChunkEvidence, StandardRecommendation
from backend.parsers.document_parser import DocumentParser
from backend.parsers.image_classifier import ImageClassificationResult, ImageClassifier


class PipelineResponse(BaseModel):
    """Unified response contract for multi-modal standard identification."""
    query: str
    detected_language: str
    extracted_text_snippet: str = ""
    image_analysis: ImageClassificationResult | None = None
    recommendations: list[StandardRecommendation] = Field(default_factory=list)
    document_evidences: list[DocumentChunkEvidence] = Field(default_factory=list)
    llm_analysis: LlmStandardizedResponse | None = None
    voice_audio_base64: str | None = None


class RecommendationPipeline:
    """End-to-end multi-modal recommendation engine orchestrator."""

    def __init__(self) -> None:
        self._multi = MultilingualProcessor()
        self._retriever = HybridRetriever()
        self._resolver = NormativeResolver()
        self._advisor = CertificationAdvisor()
        self._clause_gen = TenderClauseGenerator()
        self._doc_parser = DocumentParser()
        self._image_clf = ImageClassifier()
        self._voice_svc = VoiceService()
        self._llm = LlmOrchestrator()

    async def process_input(
        self, query: str | None = None, pdf_bytes: bytes | None = None,
        image_bytes: bytes | None = None, audio_bytes: bytes | None = None,
        division: str | None = None, generate_voice_response: bool = False,
    ) -> PipelineResponse:
        """Process any input modality and produce standardized recommendations."""
        raw_parts: list[str] = []
        eff_query = (query or "").strip()
        img_res: ImageClassificationResult | None = None

        # ... (audio, image, pdf processing) ...

        comb_txt = " ".join(raw_parts)
        sq = eff_query or (comb_txt[:300] if comb_txt else "General Indian Standards")
        exp_q, lang = self._multi.translate_and_expand(sq)
        matches, evidences = self._retriever.search_with_evidence(query=exp_q, division=division, top_k=5, top_k_chunks=5)

        # ... (builds recommendations, calls LLM orchestrator, returns PipelineResponse) ...
```

**Key observation:** The `process_input()` method goes directly to retriever + LLM. There is NO cache check. The cache intercept point is right after `exp_q` (the expanded query) is computed and before `self._retriever.search_with_evidence()` is called.

---

## Current Code: `local_gguf_provider.py` (relevant concurrency section)

**Path:** `d:\CODE\Hackathon\backend\engine\local_gguf_provider.py`

```python
class LocalGgufLlmProvider(BaseLlmProvider):
    def __init__(self, ...) -> None:
        # ...
        self._model, self._lock = None, threading.Lock()   # <-- naive threading.Lock

    def _sync_generate(self, prompt: str, system_prompt: str | None) -> str | None:
        with self._lock:                                    # <-- blocks all threads
            # ... model loading + inference ...

    def _sync_generate_stream(self, prompt: str, system_prompt: str | None) -> Any:
        with self._lock:                                    # <-- blocks all threads
            # ... model loading + streaming inference ...

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        out = await asyncio.to_thread(self._sync_generate, prompt, system_prompt)
        # ...

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        gen = await asyncio.to_thread(self._sync_generate_stream, prompt, system_prompt)
        # ...
```

**Key observation:** Uses `threading.Lock()` which blocks ALL waiting threads. No queue position feedback. No backpressure — if 10 users hit the endpoint simultaneously, 9 will silently wait or timeout.

---

## Task 3.1: Semantic Query Caching

**Files:**
- CREATE: `d:\CODE\Hackathon\backend\engine\cache_service.py`
- MODIFY: `d:\CODE\Hackathon\backend\engine\pipeline.py`

### What to Build

A lightweight semantic cache that stores verified query-response pairs. Before hitting the retriever and LLM, check if a semantically similar query has been answered before.

### How to Build

#### Step 1: Create `cache_service.py`

```python
# d:\CODE\Hackathon\backend\engine\cache_service.py

# Build a class `SemanticCacheService` with:
# 1. SQLite backend (zero-dependency local setup) storing:
#    - query_text: str
#    - query_embedding: bytes (serialized numpy array)
#    - response_json: str (serialized PipelineResponse)
#    - created_at: datetime
#    - hit_count: int
# 2. Method: async def check_cache(self, query: str, threshold: float = 0.95) -> PipelineResponse | None
#    - Generate embedding for the incoming query using EmbeddingService
#    - Load all cached embeddings
#    - Compute cosine similarity against each cached embedding
#    - If max similarity >= threshold, return the cached response
#    - If no match, return None
# 3. Method: async def store_cache(self, query: str, response: PipelineResponse) -> None
#    - Generate embedding for the query
#    - Serialize response to JSON
#    - Insert into SQLite
# 4. Method: async def invalidate_cache(self) -> None
#    - Clear all cached entries (admin use)
# 5. SQLite DB path should be configurable via app_settings (NOT hardcoded)
# 6. Use the existing EmbeddingService for embedding generation
```

#### Step 2: Integrate cache into `pipeline.py`

Modify `RecommendationPipeline.__init__()` to instantiate `SemanticCacheService`:
```python
from backend.engine.cache_service import SemanticCacheService
# In __init__:
self._cache = SemanticCacheService()
```

Modify `process_input()` — add cache check right after query expansion:
```python
# After: exp_q, lang = self._multi.translate_and_expand(sq)

# Cache check
cached = await self._cache.check_cache(exp_q)
if cached is not None:
    logger.info(f"Cache HIT for query: {exp_q[:50]}...")
    return cached

# ... (existing retrieval + LLM code) ...

# Before return: store result in cache
await self._cache.store_cache(exp_q, response)
return response
```

### Acceptance Criteria
- [ ] `SemanticCacheService` class created with SQLite backend
- [ ] Cache check happens BEFORE retriever and LLM calls
- [ ] Cosine similarity threshold is configurable (default 0.95)
- [ ] Cache hit returns response in <5ms (no GPU computation)
- [ ] SQLite DB path is configurable (not hardcoded)
- [ ] Cache miss proceeds through normal pipeline and stores result
- [ ] `invalidate_cache()` method exists for admin use

---

## Task 3.2: Asynchronous Request Queue & Backpressure

**File:** `d:\CODE\Hackathon\backend\engine\local_gguf_provider.py`

### What to Build

Replace the naive `threading.Lock()` with an `asyncio.Queue`-based worker mechanism that:
- Serializes GPU access (only one inference at a time)
- Provides queue position feedback to waiting clients
- Returns HTTP 429 when queue is full (backpressure)

### How to Build

1. **Remove** `self._lock = threading.Lock()` from `__init__`.

2. **Add** an `asyncio.Queue` with a configurable max size:
   ```python
   self._queue: asyncio.Queue = asyncio.Queue(maxsize=app_settings.llm.max_queue_size)  # e.g., 5
   self._active_request: bool = False
   ```

3. **Create** a new async method `_enqueue_request(self, coro)` that:
   - Checks if the queue is full → raise an HTTP-friendly exception (the router should catch this and return 429)
   - Puts the request into the queue
   - Waits for its turn
   - Returns the result

4. **Modify** `generate_text()` and `generate_text_stream()` to use the queue:
   ```python
   async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
       # Acquire queue slot
       # If queue full, raise BackpressureError
       # Wait for turn, then execute _sync_generate via asyncio.to_thread
       # Release slot when done
   ```

5. **For streaming**, optionally yield a preliminary queue position event:
   ```python
   # If the request is queued (not immediately served):
   yield f'{{"status": "queued", "position": {position}}}'
   # Then yield actual LLM tokens
   ```

6. **Add** a configurable `max_queue_size` to `app_settings.llm` (or equivalent config). **Do not hardcode.**

7. **Create a custom exception** `BackpressureError` that the router can catch and return 429:
   ```python
   class BackpressureError(Exception):
       """Raised when the LLM inference queue is full."""
       pass
   ```

8. **Update `llm_router.py`** to catch `BackpressureError` and return HTTP 429:
   ```python
   from fastapi import HTTPException
   # In stream endpoints:
   except BackpressureError:
       raise HTTPException(status_code=429, detail="Server busy. Please retry.")
   ```

### Acceptance Criteria
- [ ] `threading.Lock()` is removed, replaced by `asyncio.Queue`
- [ ] Queue max size is configurable (not hardcoded)
- [ ] When queue is full, HTTP 429 is returned with a clear message
- [ ] Queue position feedback is available (at minimum via logs; optionally via SSE event)
- [ ] Only one inference runs on the GPU at a time (serialized access)
- [ ] When the queue is empty, requests are served immediately (no unnecessary delay)
- [ ] Streaming endpoints properly handle the queue (yield queue position before tokens)

---

## Verification Plan

### Automated Tests

```powershell
# Run all tests
python -m pytest tests/ -v

# Run specific tests
python -m pytest tests/test_cache_service.py -v
python -m pytest tests/test_backpressure.py -v
```

Write tests covering:

1. **Cache Store & Retrieve Test:** Store a query-response pair, then check cache with the same query — should return cached response.
2. **Cache Miss Test:** Check cache with a semantically different query — should return None.
3. **Cache Similarity Threshold Test:** Check that queries with similarity below 0.95 are NOT cache hits.
4. **Backpressure 429 Test:** Mock a full queue, send a request, assert HTTP 429 is returned.
5. **Queue Position Test:** Send multiple concurrent requests, verify they are serialized (not parallel on GPU).

### Manual Verification

```powershell
# Start backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Test cache - First request (cache miss, normal latency)
curl -X POST http://127.0.0.1:8000/api/v1/ask-assistant -H "Content-Type: application/json" -d "{\"question\": \"What BIS standards apply to Portland cement?\"}" -w "\nTime: %{time_total}s\n"
# Expected: Normal response time (several seconds for LLM inference)

# Test cache - Second identical request (cache hit, <100ms)
curl -X POST http://127.0.0.1:8000/api/v1/ask-assistant -H "Content-Type: application/json" -d "{\"question\": \"What BIS standards apply to Portland cement?\"}" -w "\nTime: %{time_total}s\n"
# Expected: Near-instant response (<100ms)

# Test backpressure - Open multiple concurrent streams
# In separate terminals, run simultaneously:
curl -X POST http://127.0.0.1:8000/api/v1/ask-assistant-stream -H "Content-Type: application/json" -d "{\"question\": \"Tell me about IS 269\"}" -N
curl -X POST http://127.0.0.1:8000/api/v1/ask-assistant-stream -H "Content-Type: application/json" -d "{\"question\": \"Tell me about IS 1786\"}" -N
curl -X POST http://127.0.0.1:8000/api/v1/ask-assistant-stream -H "Content-Type: application/json" -d "{\"question\": \"Tell me about IS 14286\"}" -N
# Expected: Requests are queued and served sequentially, not crashing the GPU
```

---

## Expected Outcome

After Phase 3 completion:
- Repeated/similar queries are served from cache in <5ms (no GPU computation)
- Concurrent requests are queued gracefully with position feedback
- The GPU never processes more than one inference at a time
- When the queue overflows, clients get a clear HTTP 429 response
- No more silent timeouts or GPU crashes under load
