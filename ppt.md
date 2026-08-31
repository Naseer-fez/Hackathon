# Project Context Brief: BIS-SpecAI

## 1. Project Title & One-Paragraph Summary
**BIS-SpecAI: Indian Standards & Procurement Assistant**  
An AI-powered recommendation engine bridging Bureau of Indian Standards (BIS) registries with e-procurement platforms like GeM. It utilizes hybrid search, multilingual NLP, and automated Quality Control Order (QCO) enforcement to resolve complex normative dependencies, validate compliance, and auto-generate legally sound tender specifications.

## 2. Problem Statement
**What problem does this solve and for whom?**  
Procurement officers, legal teams, and vendors face significant compliance risks and inefficiencies when manually discovering and validating Indian Standards. BIS-SpecAI solves this by automating the discovery of accurate standards, enforcing statutory Gazette orders (ISI Mark, CRS), and flagging deprecated or superseded standards in real-time before tenders are finalized.

## 3. Architecture Overview
```text
+-------------------------------------------------------------+
|                        Frontend UI                          |
|         (React 19, Vite, Tailwind CSS, TypeScript)          |
+------------------------------+------------------------------+
                               | 
                               | HTTP/JSON (REST API)
                               v 
+-------------------------------------------------------------+
|                    FastAPI Backend Server                   |
|                                                             |
|  +-------------------+  +--------------------------------+  |
|  |   API Routers     |  |       Document Parsers         |  |
|  | (Recommendations, |  | (PyMuPDF, docling, PaddleOCR)  |  |
|  |  Tenders, GeM)    |  +--------------------------------+  |
|  +-------------------+                                      |
|                         +--------------------------------+  |
|  +-------------------+  |           AI Engine            |  |
|  |   Data & Graph    |  | (Multilingual NLP, RAG, Hybrid |  |
|  |    Ingestion      |  |  Search, llama-cpp-python)     |  |
|  +-------------------+  +--------------------------------+  |
+------------------------------+------------------------------+
                               |
                               | Embeddings / Retrievals
                               v
+-------------------------------------------------------------+
|                 Vector DB & Storage Layer                   |
|                 (ChromaDB, SQLite, FAISS)                   |
+-------------------------------------------------------------+
```
*   **Frontend**: A modern React-based UI for user interaction and dashboards.
*   **Backend Server**: FastAPI manages REST endpoints, document parsing, and orchestration.
*   **AI Engine**: Handles local LLM execution, embedding generation, multilingual translation, and semantic search.
*   **Vector DB Layer**: ChromaDB and FAISS serve as the dual-index retrieval foundation for RAG operations.

## 4. Tech Stack
*   **Backend**: Python 3, FastAPI, Uvicorn, Pydantic
*   **Frontend**: Vite, React 19, TypeScript, Tailwind CSS, Framer Motion
*   **AI & ML**: PyTorch, Hugging Face `transformers`, `sentence-transformers`, `llama-cpp-python` (Local GGUF execution)
*   **Databases & Search**: ChromaDB, SQLite, FAISS, `rank-bm25`
*   **Document Parsing**: PyMuPDF, `pdfplumber`, `docling`, PaddleOCR

## 5. End-to-End Workflow
1.  **Multimodal Input Processing**: The system accepts text queries, audio (transcribed to text), images (classified/OCR'd), or PDFs (parsed into text).
2.  **Translation & Expansion**: The `MultilingualProcessor` translates non-English text and semantically expands search terms for higher recall.
3.  **Dual-Index Retrieval (Hybrid Search)**: 
    *   **Macro Search**: Retrieves high-level catalog standards via ChromaDB (dense vectors) + BM25 (lexical).
    *   **Micro Search**: Retrieves deep document chunks for exact clause evidence.
4.  **Enrichment & Graph Resolution**: The `NormativeResolver` flags deprecations and fetches allied dependencies. The `CertificationAdvisor` enforces mandatory QCO alerts.
5.  **Cascading LLM Orchestrator**: The aggregated context is sent to a primary Cloud LLM. If it times out (>6.0s) or fails, execution falls back seamlessly to a local GGUF model running on the GPU.
6.  **Output Generation**: Returns JSON containing standard metadata, chunk evidence, technical justification, QCO verdicts, and optional Base64 voice synthesis.

## 6. Key Algorithms & Models
*   **Hybrid Search with RRF**: Combines Dense Retrieval (ChromaDB) and Lexical Matching (`rapidfuzz`/BM25) using Reciprocal Rank Fusion (RRF) for ultimate accuracy.
*   **Cascading LLM Fallback**: Prioritizes fast Cloud LLMs but ensures high availability via local 6GB VRAM-constrained GGUF models.
*   **Multi-relational Graph Traversal**: Recursively resolves Standard dependencies (Safety, Test Methods, Installation).
*   **Models**: Embedding via `all-MiniLM-L6-v2`, Multilingual via `paraphrase-multilingual-MiniLM-L12-v2`, and generation via local GGUF (e.g., `Qwen2.5-7B-Instruct`).

## 7. Data In → Processing → Data Out
*   **Data In**: 
    *   JSON Registries (`standards_database.json`, `qco_registry.json`).
    *   PDF Uploads (`Indian_Public_Procurement_Tender_Document.pdf`).
    *   Configs (`config.yaml`, `domain_expansions.yaml`).
*   **Processing**: Semantic term expansion, PDF chunking, dense vector embedding mapping, cross-lingual translation, and GBNF grammar-constrained generation.
*   **Data Out**: 
    *   `chroma.sqlite3` vector spaces and semantic caches (`semantic_cache.db`).
    *   REST API JSON responses containing actionable tender clauses and compliance scores.

## 8. Major Design Decisions & Rationale
*   **Dual-Index Hybrid Retrieval**: *Why?* Allows simultaneous querying of macro standard metadata (broad catalog) and micro deep-text evidence (exact clauses) for pinpoint accuracy.
*   **Local AI on Constrained Hardware (6GB VRAM)**: *Why?* Strict adherence to hardware mandates to prevent Out-Of-Memory (OOM) crashes by using lightweight embeddings and maintaining GGUF singletons during app lifespan.
*   **Multi-relational Graph Resolution**: *Why?* Flat search fails on standard dependencies. A graph approach accurately tracks Deprecation/Supersession paths.
*   **Automated QCO Enforcement**: *Why?* Bakes statutory compliance directly into the search engine to prevent illegal procurement clauses from being generated.

## 9. Results / Key Metrics
*   **Strict Latency Bounds**: Enforces a rigid 6.0-second timeout on Cloud LLMs before failing over to local compute.
*   **GPU Mandate Guard**: Tracks VRAM usage, assuming a strict 5.5GB threshold to maintain operational stability.

## 10. Limitations & Future Scope
*   **Retrieval Gaps**: Currently missing the planned second-stage Cross-Encoder reranker implementation (technical debt), impacting top-5 precision.
*   **Multilingual Routing Bug**: Fails to dynamically route Indic queries, defaulting incorrectly to English-only embedding and TTS models.
*   **Guardrail Risks**: Missing constrained decoding (GBNF) on the local fallback path, leaving room for hallucinated IS codes.
*   **Concurrency Bottleneck**: Uses basic thread locking instead of async queues, risking timeouts under heavy concurrent load.

## 11. Suggested Slide Deck Outline
1.  **Title Slide**: BIS-SpecAI - AI-Powered Indian Standards & Procurement Assistant.
2.  **The Problem**: Manual, error-prone standard discovery and compliance risks in e-procurement.
3.  **The Solution**: An intelligent engine seamlessly bridging BIS registries and GeM.
4.  **Platform Architecture**: Overview of FastAPI backend, React UI, and local AI Engine.
5.  **Semantic Standard Discovery**: Deep dive into Dual-Index Hybrid Retrieval (RRF).
6.  **Normative Graph Resolution**: Handling complex multi-level dependencies.
7.  **Automated QCO Enforcement**: Instantly validating statutory Gazette orders (ISI, CRS).
8.  **Deprecation Engine**: Flagging outdated IS citations before tender finalization.
9.  **Multilingual Access**: NLP for Hindi, Tamil, Telugu, and Bengali searches.
10. **Tender Auditor**: Multi-format document parsers extracting line-item specs.
11. **GeM-Ready Clause Generator**: Auto-generating 1-click specification clauses.
12. **Seamless Webhook Integrations**: Real-time bid validation via REST endpoints.
13. **Local LLM Engine Deep Dive**: Cascading fallbacks and local GGUF 6GB constraints.
14. **UI Walkthrough / Demo**: Dashboard and compliance coverage scores.
15. **Impact & Future Roadmap**: Procurement efficiency, reduced friction, and scaling.

## 12. Glossary
*   **QCO (Quality Control Order)**: Government mandates requiring products to conform to Indian Standards (e.g., mandatory ISI Mark).
*   **RRF (Reciprocal Rank Fusion)**: An algorithm that combines multiple search ranking lists (e.g., lexical and semantic) into one unified result.
*   **GGUF**: A highly optimized file format for running large language models locally on constrained hardware.
*   **GeM (Government e-Marketplace)**: The national public procurement portal in India.
*   **Normative Reference**: A standard that is cited in another standard and is indispensable for its application.

## 13. Appendix: File-by-File Reference
| Path | Purpose |
|---|---|
| `backend/main.py` | FastAPI application entry point and server lifecycle. |
| `backend/api/` | FastAPI routers (Recommendations, Tenders, GeM). |
| `backend/engine/` | Core AI: semantic search, normative graphs, clause generation. |
| `backend/data/` | Seed data generation, mock datasets, and SQlite caches. |
| `backend/parsers/` | Document parsing (PDF/DOCX) using docling, PyMuPDF. |
| `frontend/src/` | React 19 UI components and frontend state. |
| `vectordb/` | Local ChromaDB instance and vector management scripts. |
| `tests/` | Pytest test suite for validating backend business logic. |
| `backend/config/config.yaml` | Core configurations for models, paths, and search thresholds. |
