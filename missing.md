# BIS-SpecAI: Project Missing Features & Gap Analysis

This document maps the expected features outlined in the project description against the current state of the codebase, explicitly identifying what is currently missing or partially implemented. It also covers missing systemic architectural components required for production readiness.

## 1. Feature Coverage & Gap Mapping

### Feature 1: Accept product descriptions, technical specifications, or tender documents
- **Current Status:** Functional (Implemented via `pipeline.py`, `document_parser.py`, and React components like `TenderAnalyzerView.tsx`).
- **Missing / Needs Implementation:**
  - **Tender Compliance Scoring Engine:** Lacks a holistic numerical compliance score (e.g., 0-100 gauge) and a weighted penalty decomposition for missing or outdated standards within parsed tenders.

### Feature 2: Recommend the most relevant Indian Standard(s) based on semantic understanding
- **Current Status:** Functional (Hybrid Dense/Lexical Retriever exists).
- **Missing / Needs Implementation:**
  - **Cross-Encoder Reranker:** Missing a second-stage reranking model (e.g., `bge-reranker-small` or `ms-marco-MiniLM-L-6-v2`) to improve top-5 result precision.
  - **Strict Source Attribution (Clause-Level):** Missing exact clause numbers (`clause_number`, `section_heading`) extracted during PDF chunking, and strict adherence to the citation format `[IS Number:Year, Clause X.Y, Page Z]`.
  - **Zero-Hallucination Guardrails:** Missing GBNF (Grammar-Based Network Format) or Pydantic JSON schema decoding constraints to prevent the LLM from hallucinating non-existent Indian Standard codes.
  - **Semantic Query Caching:** Missing a caching layer (e.g., Redis or SQLite with cosine similarity thresholds) for frequently requested standards.

### Feature 3: Identify allied standards (normative, test, safety, installation, etc.)
- **Current Status:** Implemented (`normative_resolver.py` maps 4 different relationship types natively).
- **Missing / Needs Implementation:** 
  - (Fundamentally covered, minimal structural gaps).

### Feature 4: Highlight the latest published version and amendments
- **Current Status:** Functional (`check_deprecation()` flags superseded standards).
- **Missing / Needs Implementation:**
  - **`WITHDRAWN` Status Handling:** The engine currently only alerts on `SUPERSEDED` standards but lacks explicit UI warnings and logic processing for standards marked as `WITHDRAWN`.

### Feature 5: Suggest mandatory certification requirements (e.g., BIS, CRS, Hallmarking)
- **Current Status:** Functional (Powered by `certification_advisor.py` and `QcoRegistry`).
- **Missing / Needs Implementation:**
  - **Hallmarking Coverage:** The `HALLMARKING` scheme is defined as an enum, but the recommendation tree branch mapping to specific hallmarking advisory text is missing.

### Feature 6: Support multilingual input and natural language queries
- **Current Status:** Functional (Handled via `multilingual_processor.py` for term expansions and script detection).
- **Missing / Needs Implementation:**
  - **Dynamic Multilingual Embeddings:** The system defaults to the English-only `all-MiniLM-L6-v2` embedding model instead of dynamically routing Indic queries to the configured `paraphrase-multilingual-MiniLM-L12-v2` model, resulting in semantic degradation for Hindi/regional inputs.
  - **Dynamic TTS Routing:** The Text-to-Speech (TTS) logic always synthesizes English audio, bypassing the available Hindi TTS model path configured in `config.yaml`.

---

## 2. Additional Architectural & Performance Missings

Beyond functional feature mapping, the following backend architecture layers are missing to ensure the solution adheres to the 6GB VRAM limitation and runs effectively in production:

1. **Token Streaming (Server-Sent Events):** All LLM generation is currently blocking. Needs an SSE (`text/event-stream`) FastAPI streaming pipeline to provide sub-second time-to-first-token in the frontend.
2. **VRAM Budget Guard (Hardware Limits):** Missing a memory guard function that checks active VRAM overhead dynamically and downscales GPU layers if the 5.5GB threshold is exceeded on the RTX 3050.
3. **Concurrency Backpressure (Async Queue):** The backend needs an `asyncio.Queue` worker mechanism to handle multiple concurrent search requests cleanly without OOM (Out of Memory) crashing.
4. **Automated RAGOps / Metrics Endpoints:** The project currently lacks `/metrics` endpoints (Prometheus) to monitor GPU temperatures, query latency, and automated evaluations (Context Relevance and Groundedness metrics).
