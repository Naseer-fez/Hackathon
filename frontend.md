# BIS-SpecAI Frontend Integration & API Reference Guide

### Architecture & Base Configuration
- **Default Base URL**: `http://localhost:8000/api/v1` (configured via `VITE_API_BASE_URL` or fallback to `/api/v1`).
- **Server Health Check**: `GET /api/v1/health`
- **Prometheus Metrics**: `GET /metrics`
- **Content Types**:
  - Standard JSON: `application/json`
  - File/Multimodal Uploads: `multipart/form-data`
  - Streaming (LLM / Assistant / Explanations): Server-Sent Events (`text/event-stream`)

---

## 1. Core Recommendation & Search Endpoints

### 1.1 Standard Recommendations
Matches procurement queries or descriptions against Indian Standards (IS), computing semantic relevance, normative references, and QCO mandates.
- **Endpoint**: `POST /api/v1/recommend`
- **Request Headers**: `Content-Type: application/json`
- **Request Payload**:
  ```typescript
  {
    query: string;           // e.g. "LED street light with surge protection"
    division?: string;       // Optional filter: "ETD", "CED", "MED", etc.
    top_k?: number;          // Default: 5
  }
  ```
- **Response**: `RecommendationResponse`
  ```typescript
  {
    query: string;
    detected_language: string;
    translated_query: string;
    total_matches: number;
    recommendations: Array<{
      standard: {
        is_code: string;               // e.g. "IS 10322 (Part 5/Sec 3)"
        title: string;
        division: string;
        status: string;               // "ACTIVE" | "WITHDRAWN" | "SUPERSEDED"
        superseded_by?: string | null;
        year: number;
        reaffirmation_year?: number | null;
        amendments: string[];
        scope: string;
        key_parameters: string[];
        test_methods: string[];
        normative_references: string[];
        safety_standards: string[];
        installation_standards: string[];
        mandatory_qco: {
          is_mandatory: boolean;
          scheme: string;
          order_number: string;
          issuing_ministry: string;
          effective_date: string;
          clause_requirement: string;
        };
        category_keywords: string[];
        gem_categories: string[];
      };
      relevance_score: number;         // 0.0 to 1.0
      match_reasons: string[];
      allied_standards: Array<{
        is_code: string;
        title: string;
        relation_type: string;
        status: string;
        is_mandatory: boolean;
        details: string;
      }>;
      certification_alert: string;
      deprecation_warning?: string | null;
      sample_tender_clause: string;
    }>;
    latency_ms: number;
  }
  ```

---

### 1.2 Standards Catalog Search & Filter
Used for catalog browsing, dropdown search, and standard lookups.
- **Endpoint**: `GET /api/v1/standards`
- **Query Parameters**:
  - `division`: (Optional string)
  - `query`: (Optional string)
- **Response**: `Array<IndianStandard>` (array of standards with the same structure as above).

---

### 1.3 Knowledge Graph Visualization
Used to render network graphs / interactive nodes showing standard dependencies, normative references, and safety links.
- **Endpoint**: `GET /api/v1/graph`
- **Response**: `GraphData`
  ```typescript
  {
    nodes: Array<{
      id: string;              // e.g. "IS 10322"
      label: string;
      title: string;
      division: string;
      is_mandatory: boolean;
      status: string;
    }>;
    edges: Array<{
      source: string;          // Source IS code
      target: string;          // Target IS code
      relation: string;        // "references" | "safety_standard" | "installation"
    }>;
  }
  ```

---

### 1.4 Mandatory QCO Registry
Returns the complete database registry of Quality Control Orders currently in force in India.
- **Endpoint**: `GET /api/v1/qco-list`
- **Response**: `Record<string, MandatoryQCO>`
  - Key is standard code (e.g. `"IS 10322 (Part 5/Sec 3)"`)
  - Value is `MandatoryQCO` object.

---

## 2. Tender Document & GeM Integration Endpoints

### 2.1 Tender Document Analysis & Audit
Parses uploaded tender PDFs, DOCX, or pasted raw text to extract product items, detect outdated/withdrawn standard citations, flag non-compliance issues, and compute QCO coverage.
- **Endpoint**: `POST /api/v1/analyze-tender`
- **Request Format**: `multipart/form-data`
- **Form Fields**:
  - `file`: (Optional File/Blob) Uploaded Tender PDF or DOCX
  - `raw_text`: (Optional string) Raw pasted RFP / Tender specifications
- **Response**: `TenderAnalysisReport`
  ```typescript
  {
    document_name: string;
    extracted_items_count: number;
    items: Array<{
      item_id: number;
      product_title: string;
      spec_summary: string;
      cited_standards: string[];
      outdated_citations: string[];
      recommended_standards: StandardRecommendation[];
    }>;
    compliance_issues: Array<{
      severity: "HIGH" | "MEDIUM" | "LOW";
      category: string;
      issue_text: string;
      corrective_action: string;
    }>;
    mandatory_qco_coverage: number;       // e.g. 85.5 (%)
    complete_spec_clause_text: string;    // Auto-generated legally sound tender clause
    raw_text?: string;
  }
  ```

---

### 2.2 GeM (Government e-Marketplace) Webhook / Bid Validation
Simulates or handles GeM bid validation checks before tenders go live on the portal.
- **Endpoint**: `POST /api/v1/gem-webhook`
- **Request Headers**: `Content-Type: application/json`
- **Request Payload**:
  ```typescript
  {
    bid_id: string;
    category_name: string;
    product_title: string;
    buyer_specifications: string;
  }
  ```
- **Response**:
  ```typescript
  {
    bid_id: string;
    status: "COMPLIANT" | "NON_COMPLIANT" | "WARNING";
    compliance_score: number;
    primary_standard: string;
    is_qco_mandatory: boolean;
    qco_order: string;
    recommended_clause: string;
    allied_standards: string[];
  }
  ```

---

## 3. Two-Tier AI & LLM Inference Endpoints

The backend implements a two-tier LLM system:
1. **Tier 1 (Fast)**: Qwen 2.5 7B (GGUF / GPU-accelerated) for immediate queries (<1s)
2. **Tier 2 (Heavy)**: DeepSeek R1 14B / RAG for in-depth engineering compliance, reasoning steps, and tender clause synthesis.

---

### 3.1 Fast Answer (Tier 1)
- **Endpoint**: `POST /api/v1/fast-answer`
- **Request Format**: `multipart/form-data`
- **Form Fields**:
  - `query`: string (required)
  - `pdf_text`: string (optional, up to 3000 chars)
  - `pdf_file`: File (optional)
- **Response**:
  ```typescript
  {
    query: string;
    answer: string;
    source_tier: string;       // "Tier 1: Qwen 2.5 7B" or fallback
  }
  ```

---

### 3.2 Heavy Reasoning & CoT (Tier 2)
- **Endpoint**: `POST /api/v1/heavy-reasoning`
- **Request Format**: `multipart/form-data`
- **Form Fields**:
  - `query`: string (required)
  - `pdf_text`: string (optional, up to 5000 chars)
  - `pdf_file`: File (optional)
  - `chat_history`: stringified JSON `[{ role: "user" | "assistant", content: string }]`
  - `refresh_context`: `"true"` | `"false"`
- **Response**:
  ```typescript
  {
    query: string;
    answer: string;
    source_tier: string;
    synthesized_context?: string;
    summarized_history?: string;
  }
  ```

---

### 3.3 Streaming Explanations & Assistant (Server-Sent Events)

#### Standard Explanation Stream:
- **Endpoint**: `POST /api/v1/explain-standard-stream`
- **Request**: `{ query: string, is_code: string }`
- **Format**: SSE `text/event-stream`
- **Stream protocol**:
  - Each chunk emitted as: `data: <token_string>\n\n`
  - Stream termination token: `data: [DONE]`
  - Error token: `data: [ERROR: <reason>]`

#### Procurement Assistant Stream:
- **Endpoint**: `POST /api/v1/ask-assistant-stream`
- **Request**:
  ```typescript
  {
    question: string;
    pdf_text?: string;
    chat_history?: Array<{ role: "user" | "assistant"; content: string }>;
  }
  ```
- **Format**: SSE `text/event-stream` (same protocol as above).

*(Note: Synchronous non-streaming alternatives exist at `POST /api/v1/explain-standard` and `POST /api/v1/ask-assistant` returning `{ question/query, answer/explanation }`).*

---

### 3.4 Chat Context Summarization
Summarizes ongoing procurement dialogue to prevent context overflow while retaining technical specs.
- **Endpoint**: `POST /api/v1/summarize-context`
- **Request**: `{ chat_history: Array<{ role: string; content: string }> }`
- **Response**: `{ summarized_context: string }`

---

## 4. Multimodal & Audio/Vision Endpoints

### 4.1 End-to-End Multimodal Pipeline
Processes voice, technical diagrams, and query text all in one atomic execution.
- **Endpoint**: `POST /api/v1/pipeline/process`
- **Request Format**: `multipart/form-data`
  - `query`: (optional string)
  - `image_file`: (optional image file e.g. drawing/spec sheet)
  - `audio_file`: (optional audio blob e.g. voice query)
  - `division`: (optional filter)
- **Response**: `PipelineResponse`
  ```typescript
  {
    query: string;
    detected_language: string;
    extracted_text_snippet?: string;
    image_analysis?: ImageClassificationResult | null;
    recommendations: StandardRecommendation[];
    llm_analysis?: LlmStandardizedResponse | null;
    voice_audio_base64?: string | null;  // Base64 TTS audio response if voice requested
  }
  ```

---

### 4.2 Voice Transcription (STT)
Uses local Whisper / audio processing to transcribe engineer voice inputs in Hindi/English/Hinglish.
- **Endpoint**: `POST /api/v1/voice/transcribe`
- **Request Format**: `multipart/form-data` with `audio_file` (Blob/File, `.wav` or `.webm`)
- **Response**:
  ```json
  {
    "transcribed_text": "Need IS code for fire resistant cables"
  }
  ```

---

### 4.3 Voice Synthesis (TTS)
Speaks compliance decisions and summaries.
- **Endpoint**: `POST /api/v1/voice/synthesize`
- **Request**: `{ "text": "Under QCO 2024, IS 694 certification is strictly mandatory." }`
- **Response**: Binary audio stream (`audio/wav` or `audio/mpeg` Blob)

---

### 4.4 Technical Drawing / Image Classification (Vision)
Analyses engineering schematics, wiring diagrams, or product photos to identify component types and extract technical text.
- **Endpoint**: `POST /api/v1/image/classify`
- **Request Format**: `multipart/form-data` with `image_file`
- **Response**: `ImageClassificationResult`
  ```typescript
  {
    category: string;                  // e.g. "circuit_breaker", "transformer", "cable"
    confidence: number;
    dimensions: [number, number];      // [width, height]
    aspect_ratio: number;
    is_technical_drawing: boolean;
    extracted_text: string;            // OCR / vision recognized technical ratings
    technical_attributes?: Record<string, unknown>;
  }
  ```

---

## 5. Summary Route Table For Quick Frontend Implementation

| HTTP Method | Route | Content-Type | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | `application/json` | System health check & version |
| `POST` | `/api/v1/recommend` | `application/json` | Primary hybrid search & standard recommendations |
| `GET` | `/api/v1/standards` | Query Params | Standards catalog browsing & filtering |
| `GET` | `/api/v1/graph` | `application/json` | Relationship graph nodes & edges |
| `GET` | `/api/v1/qco-list` | `application/json` | Active Mandatory Quality Control Orders |
| `POST` | `/api/v1/analyze-tender`| `multipart/form-data` | PDF/Text tender audit & non-compliance flagging |
| `POST` | `/api/v1/gem-webhook` | `application/json` | GeM portal bid verification simulate |
| `POST` | `/api/v1/fast-answer` | `multipart/form-data` | Tier 1 Fast LLM answers (<1 sec) |
| `POST` | `/api/v1/heavy-reasoning`| `multipart/form-data` | Tier 2 Deep reasoning & CoT evaluation |
| `POST` | `/api/v1/explain-standard-stream` | SSE (`text/event-stream`) | Real-time streaming standard explanations |
| `POST` | `/api/v1/ask-assistant-stream` | SSE (`text/event-stream`) | Real-time streaming procurement assistant chat |
| `POST` | `/api/v1/summarize-context` | `application/json` | Chat history compaction & context window refresher |
| `POST` | `/api/v1/pipeline/process` | `multipart/form-data` | Unified Multimodal (Voice + Image + Text) pipeline |
| `POST` | `/api/v1/voice/transcribe` | `multipart/form-data` | Audio recording to text (STT) |
| `POST` | `/api/v1/voice/synthesize` | `application/json` | Text to spoken audio blob (TTS) |
| `POST` | `/api/v1/image/classify` | `multipart/form-data` | Technical image/schematic classification |
