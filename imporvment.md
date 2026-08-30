# BIS-SpecAI: Production Readiness & RAG Engineering Roadmap

This document outlines the architectural improvements, reliability upgrades, and engineering specifications required to transition the BIS-SpecAI RAG recommendation engine from a prototype into an enterprise-grade, high-performance production system.

---

## 1. Advanced Retrieval & Reranking Architecture (Highest Accuracy Impact)

### 1.1 Dual-Index (Hierarchical) Retrieval
- **Macro Standard Discovery**: Query `bis_standards_catalog` (3,310 records) to locate matching Standard IDs, titles, active/withdrawn status, and statutory Quality Control Order (QCO) mandates.
- **Micro Deep-Text Evidence**: Simultaneously query `document_chunks` (8,095 extracted PDF slices) at `vectordb/data/chroma` to extract exact test parameters, tolerances, clause numbers, and amendment paragraphs.
- **Hierarchical Linking**: Return structured standard metadata along with specific PDF page references and clause numbers to the LLM.

### 1.2 Two-Stage Retrieval with Cross-Encoder Reranking
- **First Stage (High Recall)**: Pull coarse Top-25 candidates using hybrid dense vector search + lexical token matching (BM25 / RapidFuzz).
- **Second Stage (High Precision)**: Pass the Top-25 candidates through a lightweight local cross-encoder model (`BAAI/bge-reranker-small` or `FlashRank`).
- **Impact**: Eliminates irrelevant context, boosting Top-1/Top-3 precision from ~70% to **>93%**.

### 1.3 Query Expansion & Domain Normalization
- Pre-process user inputs to translate colloquial search terms (*"solar panel for home rooftop"*) into formal BIS nomenclature (*"Terrestrial photovoltaic (PV) modules, crystalline silicon, IS 14286, IS/IEC 61730"*).
- Implement Hypothetical Document Embeddings (HyDE) for complex multi-requirement procurement specifications.

---

## 2. Zero-Hallucination Guardrails & Structured Output

### 2.1 Constrained Decoding & GBNF Grammars
- Implement GBNF grammar constraints or Pydantic JSON schema enforcement during local GGUF decoding.
- Guarantee that the LLM cannot hallucinate fabricated Indian Standard numbers or non-existent gazette order numbers.

### 2.2 Strict Source Attribution & Rejection Criteria
- Enforce mandatory markdown citation format: `[IS Number:Year, Clause X.Y, Page Z]`.
- Enforce strict negative rejection: If no matching standard exists in the vector catalog, the model must faithfully report unavailability rather than guessing.

---

## 3. Latency & User Experience

### 3.1 Token Streaming (Server-Sent Events / SSE)
- Implement FastAPI `StreamingResponse` using chunked transfer encoding (`text/event-stream`).
- Enables Time-to-First-Token (TTFT) under **250ms**, eliminating multi-second waiting periods.

### 3.2 Semantic Query Caching
- Cache verified question-answer and recommendation pairs in SQLite or Redis.
- Frequently asked queries (*"What is the mandatory standard for cement?"*, *"Is IS 14286 under QCO?"*) resolve in **< 5ms** with zero GPU load.

---

## 4. Hardware Optimization & Concurrency Management

### 4.1 Server Startup Pre-warming & Lifespan Caching
- Preload model weights into VRAM during FastAPI `@asynccontextmanager lifespan` boot.
- Execute a 1-token dummy generation and 1 dummy embedding pass at startup to pre-allocate CUDA computation graphs.
- Maintain persistent singleton instances across all API routers to prevent unloading cycles.

### 4.2 Asynchronous Request Queue & Backpressure
- Single consumer GPU (RTX 3050 6GB) inference serialized via `asyncio.Queue` / worker lock.
- Return real-time queue position indicators (`"Query queued at position 2..."`) to prevent connection timeouts under concurrent load.

---

## 5. Continuous Evaluation & Observability (RAGOps)

### 5.1 Automated RAG Triad Evaluation
- Measure traffic continuously using automated RAG evaluation metrics:
  1. **Context Relevance**: Proportion of retrieved standard clauses relevant to the user query.
  2. **Groundedness / Faithfulness**: Verification that 100% of claims are mathematically or technically grounded in retrieved PDF text.
  3. **Answer Relevance**: Measure how directly the final generated text answers the buyer's requirement.

### 5.2 Telemetry & Health Monitoring
- Expose a `/metrics` Prometheus endpoint tracking:
  - GPU VRAM allocation & Temperature
  - Inference generation throughput (tokens/sec)
  - Vector search P95 and P99 latency

---

## Implementation Priority Roadmap

| Priority | Initiative | Complexity | Expected Impact |
| :--- | :--- | :--- | :--- |
| 🔴 **P0** | **Startup Pre-warming & Singleton Lifespan** | Low | Zero cold-start latency; weights stay permanently in VRAM |
| 🔴 **P0** | **Dual-Index Retrieval (Catalog + Full Chunks)** | Medium | 100% catalog coverage + exact page/clause citations |
| 🟡 **P1** | **Token Streaming (SSE) to Web UI** | Low | Sub-second Time-to-First-Token |
| 🟡 **P1** | **Local Cross-Encoder Reranker (`bge-reranker-small`)** | Low | Major boost in response precision and relevance |
| 🟢 **P2** | **Semantic Query Caching (Redis/SQLite)** | Low | Sub-5ms response time for common regulatory queries |
| 🟢 **P2** | **Constrained JSON / GBNF Output Guardrails** | Medium | Mathematically eliminates fabricated standard codes |
