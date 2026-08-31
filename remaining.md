# BIS-SpecAI: Remaining Production Improvements

Based on the `improvement.md` document, the following architectural improvements, reliability upgrades, and engineering specifications are currently **missing or not fully implemented** in the codebase. These require implementation to transition the prototype into a production-grade system.

## 1. Advanced Retrieval & Reranking Architecture

### 1.2 Two-Stage Retrieval with Cross-Encoder Reranking
- **Status**: Missing
- **Requirement**: Implement a second-stage local cross-encoder model (e.g., `BAAI/bge-reranker-small` or `FlashRank`) to rerank the Top-25 candidates retrieved by the `HybridRetriever`.

### 1.3 Query Expansion & Domain Normalization
- **Status**: Missing
- **Requirement**: Implement colloquial search term translation to formal BIS nomenclature and Hypothetical Document Embeddings (HyDE) for complex procurement specifications.

## 2. Zero-Hallucination Guardrails & Structured Output

### 2.1 Constrained Decoding & GBNF Grammars
- **Status**: Missing
- **Requirement**: Enforce GBNF grammar constraints or Pydantic JSON schema constraints during local GGUF decoding in `local_gguf_provider.py` to prevent hallucinated codes.

### 2.2 Strict Source Attribution & Rejection Criteria
- **Status**: Missing (Incorrect Format)
- **Requirement**: Update the `MASTER_SYSTEM_PROMPT` in `backend/engine/prompts/system_prompt.py` and evaluation prompts to strictly enforce the markdown citation format: `[IS Number:Year, Clause X.Y, Page Z]`. 

## 3. Latency & User Experience

### 3.1 Token Streaming (Server-Sent Events / SSE)
- **Status**: Partially Implemented / Incorrect Format
- **Requirement**: While streaming is present in `llm_router.py`, it uses `media_type="text/plain"`. This needs to be updated to use FastAPI `StreamingResponse` with chunked transfer encoding (`text/event-stream`) and proper SSE formatting.

### 3.2 Semantic Query Caching
- **Status**: Missing
- **Requirement**: Introduce a caching layer (SQLite or Redis) in the backend to cache verified question-answer and recommendation pairs for frequently asked queries.

## 4. Hardware Optimization & Concurrency Management

### 4.2 Asynchronous Request Queue & Backpressure
- **Status**: Missing
- **Requirement**: Replace the simple `threading.Lock()` in `LocalGgufLlmProvider` with an `asyncio.Queue` / worker lock mechanism that returns real-time queue position indicators (e.g., "Query queued at position 2...") to clients.

## 5. Continuous Evaluation & Observability (RAGOps)

### 5.1 Automated RAG Triad Evaluation
- **Status**: Missing
- **Requirement**: Implement automated continuous evaluation for Context Relevance, Groundedness/Faithfulness, and Answer Relevance.

### 5.2 Telemetry & Health Monitoring
- **Status**: Missing
- **Requirement**: Expose a `/metrics` Prometheus endpoint (e.g., via `prometheus_client` in FastAPI) tracking GPU VRAM allocation, inference generation throughput, and vector search latency.

---

### Files to be Modified / Created:
- **`backend/engine/hybrid_retriever.py`**: Needs updates for Cross-Encoder Reranking and Query Expansion.
- **`backend/engine/local_gguf_provider.py`**: Needs GBNF grammar support and `asyncio.Queue` backpressure implementation.
- **`backend/engine/prompts/system_prompt.py`** & **`evaluation_prompt.py`**: Needs citation format updates.
- **`backend/api/llm_router.py`**: Needs SSE (`text/event-stream`) updates for endpoints.
- **`backend/main.py`**: Needs `/metrics` Prometheus endpoint integration.
- **`backend/engine/cache_service.py` (New)**: Needs to be created for Semantic Query Caching.
- **`backend/engine/rag_evaluation.py` (New)**: Needs to be created for RAG Triad Evaluation.
