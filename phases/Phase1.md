# Phase 1: Core Retrieval & Prompt Formatting

## Project Context

**BIS-SpecAI** is an AI-powered Indian Standards (BIS) recommendation engine for e-Procurement portals (GeM, CPPP, State/PSU Tenders). It automates discovery of Indian Standards (IS), resolves normative reference graphs, tracks reaffirmations/amendments, enforces Quality Control Orders (QCOs), and supports multilingual Indic queries.

The system runs on a local NVIDIA RTX 3050 6GB GPU using a quantized GGUF model via `llama-cpp-python`, with a FastAPI backend and React + TypeScript frontend.

**Project root:** `d:\CODE\Hackathon`

**Coding rules:** Read `d:\CODE\Hackathon\GEMINI.md` for project-wide coding constraints (type hints, async/await, CUDA, no hardcoded secrets, tests required, etc.)

---

## Phase Objective

Improve the accuracy of retrieved context delivered to the LLM and enforce strict adherence to the required markdown citation format. This phase targets the **retrieval pipeline** and **prompt engineering layer** — the two components that determine what the LLM sees and how it formats its output.

**Features to Build:**
1. Query Expansion & Domain Normalization (HyDE)
2. Two-Stage Retrieval with Cross-Encoder Reranking
3. Strict Source Attribution & Rejection Criteria

**Why Combined:** Both Query Expansion and Cross-Encoder Reranking modify the `HybridRetriever` logic. Once the context is retrieved with higher precision, the immediate next step in the pipeline is prompt generation, making it efficient to fix the strict source attribution format at the same time.

---

## Prerequisites

None — this is the first phase.

---

## Files to Modify

| File | Action | Purpose |
|---|---|---|
| `d:\CODE\Hackathon\backend\engine\hybrid_retriever.py` | MODIFY | Add query expansion + cross-encoder reranking |
| `d:\CODE\Hackathon\backend\engine\prompts\system_prompt.py` | MODIFY | Update citation format in MASTER_SYSTEM_PROMPT |
| `d:\CODE\Hackathon\backend\engine\prompts\evaluation_prompt.py` | MODIFY | Update citation format in EVALUATION_PROMPT_TEMPLATE |
| `d:\CODE\Hackathon\tests\test_hybrid_retriever.py` | CREATE or MODIFY | Tests for new retrieval features |

---

## Current Code: `hybrid_retriever.py`

**Path:** `d:\CODE\Hackathon\backend\engine\hybrid_retriever.py` (98 lines)

```python
"""Hybrid semantic and lexical dual-index retriever for Indian Standards backed by ChromaDB."""
from __future__ import annotations
import re
from typing import Any
from rapidfuzz import fuzz
from backend.config.settings import app_settings
from backend.engine.chroma_hydrator import hydrate_standard_from_chroma
from backend.engine.embedding_service import EmbeddingService
from backend.ingestion.standards_loader import StandardsLoader
from backend.logger.app_logger import get_logger
from backend.models.recommendation_model import DocumentChunkEvidence
from backend.models.standard_model import IndianStandard
from backend.vectordb.search_service import VectorDbSearchService

logger = get_logger("engine.hybrid_retriever")


class HybridRetriever:
    """Combines ChromaDB dense retrieval with in-memory lexical matching and document chunk evidence."""

    def __init__(self, loader: StandardsLoader | None = None, embed_svc: EmbeddingService | None = None) -> None:
        self._loader = loader or StandardsLoader()
        self._embed_svc = embed_svc or EmbeddingService()
        self._vectordb = VectorDbSearchService()
        self._standards = self._loader.get_all_standards()

    def _calculate_lexical_score(self, query: str, s: IndianStandard) -> float:
        target = f"{s.is_code} {s.title} {' '.join(s.category_keywords)}".lower()
        return float(fuzz.token_set_ratio(query.lower(), target) / 100.0)

    def search(self, query: str, division: str | None = None, top_k: int = 5) -> list[tuple[IndianStandard, float, list[str]]]:
        """Perform Stage 1: Macro Standard Discovery."""
        if not query.strip():
            return []
        results_map: dict[str, tuple[IndianStandard, float, list[str]]] = {}
        alpha = app_settings.ai_engine.hybrid_alpha
        logger.info(f"HybridRetriever: Macro search for '{query}' (Division: {division or 'All'})")

        try:
            hits = self._vectordb.search(query=query, division=division, top_k=top_k * 2)
            for hit in hits:
                std = hydrate_standard_from_chroma(hit, self._loader)
                lex_score, dense_score = self._calculate_lexical_score(query, std), float(hit.get("similarity_score", 0.0))
                hybrid_score = (alpha * dense_score) + ((1.0 - alpha) * lex_score)
                reasons = [f"ChromaDB Vector match ({dense_score:.2f})"]
                if lex_score > 0.4:
                    reasons.append(f"Keyword alignment ({lex_score:.2f})")
                results_map[std.is_code] = (std, hybrid_score, reasons)
        except (KeyError, ValueError, Exception) as exc:
            logger.warning(f"[FALLBACK] ChromaDB search error ({type(exc).__name__}) -> using in-memory catalog")

        for s in self._standards:
            if division and s.division.upper() != division.upper():
                continue
            lex_score = self._calculate_lexical_score(query, s)
            reasons = []
            code_num = re.sub(r"[^\d]", "", s.is_code)
            if code_num and code_num in query:
                lex_score, reasons = max(lex_score, 0.95), [f"Direct match on standard code {s.is_code}"]
            if s.is_code in results_map:
                std, ex_sc, ex_r = results_map[s.is_code]
                results_map[s.is_code] = (s, max(ex_sc, lex_score), list(set(ex_r + reasons)))
            elif lex_score > 0.45:
                results_map[s.is_code] = (s, lex_score, [f"Curated catalog match ({lex_score:.2f})"])

        ranked = sorted(results_map.values(), key=lambda item: item[1], reverse=True)
        return ranked[:top_k]

    def search_document_evidence(self, query: str, top_k: int = 5) -> list[DocumentChunkEvidence]:
        """Perform Stage 2: Micro Evidence & Deep Clause Retrieval from PDF chunks."""
        raw_chunks = self._vectordb.search_document_chunks(query=query, top_k=top_k)
        evidences: list[DocumentChunkEvidence] = []
        for c in raw_chunks:
            evidences.append(DocumentChunkEvidence(
                chunk_id=c.get("chunk_id", ""), doc_id=c.get("doc_id", ""),
                file_name=c.get("file_name", ""), page_number=c.get("page_number", 1),
                total_pages=c.get("total_pages", 1), folder_category=c.get("folder_category", "Standard"),
                snippet=c.get("snippet", ""), relevance_score=c.get("similarity_score", 0.0),
            ))
        return evidences

    def search_with_evidence(
        self, query: str, division: str | None = None, top_k: int = 5, top_k_chunks: int = 5
    ) -> tuple[list[tuple[IndianStandard, float, list[str]]], list[DocumentChunkEvidence]]:
        """Perform unified Dual-Index Retrieval unifying macro standards and micro PDF clause excerpts."""
        standards = self.search(query=query, division=division, top_k=top_k)
        evidences = self.search_document_evidence(query=query, top_k=top_k_chunks)
        codes = [s[0].is_code for s in standards]
        for ev in evidences:
            for c in codes:
                code_digits = re.sub(r"[^\d]", "", c)
                if code_digits and (c.lower() in ev.file_name.lower() or code_digits in ev.file_name.lower() or c.lower() in ev.snippet.lower()):
                    ev.matched_standard = c
                    break
        return standards, evidences
```

**Key observations:**
- No query expansion exists — the raw query goes directly to `_vectordb.search()` and `_calculate_lexical_score()`
- No cross-encoder reranking — results are ranked purely by hybrid alpha-blended score
- The `search()` method retrieves `top_k * 2` from ChromaDB but needs to retrieve `top_k * 5` (Top-25) for cross-encoder input
- The `EmbeddingService` is injected but only used downstream — it can be reused for query expansion embedding

---

## Current Code: `system_prompt.py`

**Path:** `d:\CODE\Hackathon\backend\engine\prompts\system_prompt.py` (187 lines)

The `MASTER_SYSTEM_PROMPT` is a large string constant. The **citation format that needs changing** is at lines ~159-162 in the `EVIDENCE AND CITATION RULES` section:

```python
# EVIDENCE AND CITATION RULES

1. For every clause-level claim, provide a citation in this format:
   File name, page number, clause number if available.
2. If no clause number is available, cite file name and page number only.
3. If no file name is available, cite the provided source label.
```

This must be updated to enforce the strict format: `[IS Number:Year, Clause X.Y, Page Z]`

Also add a strict negative rejection rule: If the standard is not provided in the context, explicitly state "Standard not found in provided context" and do not guess.

---

## Current Code: `evaluation_prompt.py`

**Path:** `d:\CODE\Hackathon\backend\engine\prompts\evaluation_prompt.py` (105 lines)

The `EVALUATION_PROMPT_TEMPLATE` references citation format at line ~62 and ~84:

```python
4. Cite file name, page number, and clause number where available.
```

and in the Technical Parameter Match Matrix:

```python
6. Citation must include file name, page number, and clause number if available.
   If clause number is unavailable, cite file and page only.
```

Both must be updated to the `[IS Number:Year, Clause X.Y, Page Z]` format.

---

## Task 1.1: Query Expansion & Domain Normalization

**File:** `d:\CODE\Hackathon\backend\engine\hybrid_retriever.py`

### What to Build

Add a query pre-processing step that expands colloquial/trade terms to formal BIS nomenclature before the vector and lexical searches execute.

### How to Build

1. Create a new private method `_expand_query(self, query: str) -> str` in `HybridRetriever`.
2. Inside this method, implement a domain normalization dictionary that maps common trade terms to BIS nomenclature. Examples:
   - `"solar panel"` → `"Terrestrial photovoltaic (PV) modules, crystalline silicon"`
   - `"rooftop solar"` → `"Terrestrial photovoltaic (PV) modules, IS 14286"`
   - `"TMT bar"` / `"saria"` / `"sariya"` / `"सरिया"` → `"High strength deformed steel bars and wires for concrete reinforcement, IS 1786"`
   - `"cement"` → `"Ordinary Portland Cement, Portland Pozzolana Cement, IS 269, IS 1489"`
   - `"electric wire"` / `"house wire"` → `"PVC insulated cables, IS 694"`
   - `"LED bulb"` / `"LED light"` → `"Self-ballasted LED lamps, IS 16102"`
   - `"steel pipe"` → `"ERW steel tubes, IS 1239, IS 3589"`
   - `"street light"` / `"स्ट्रीट लाइट"` → `"LED luminaires for road and street lighting, IS 10322"`
3. Store the domain dictionary in a config-friendly structure (e.g., a dict loaded from `app_settings` or a YAML file) — **do not hardcode in source**.
4. Concatenate the expanded terms with the original query: `expanded = f"{query} {expansion_terms}"`
5. Call `_expand_query()` at the start of both `search()` and `search_document_evidence()` methods.

### Acceptance Criteria
- [ ] A query like `"solar panel for government building"` retrieves IS 14286 in the top 3 results
- [ ] A query like `"TMT bar"` retrieves IS 1786 in the top 3 results
- [ ] The domain dictionary is **not hardcoded** — it is loaded from a config file or settings object
- [ ] The original query text is preserved (expansion is additive, not replacing)

---

## Task 1.2: Two-Stage Retrieval with Cross-Encoder Reranking

**File:** `d:\CODE\Hackathon\backend\engine\hybrid_retriever.py`

### What to Build

After the first-stage hybrid retrieval, pass the Top-25 candidates through a local cross-encoder model and return the reranked Top-K.

### How to Build

1. Add a cross-encoder model name to the project configuration (e.g., `app_settings.ai_engine.reranker_model` or a YAML key). Recommended model: `BAAI/bge-reranker-v2-m3` or `BAAI/bge-reranker-small` (lightweight, fits in VRAM alongside the GGUF model).
2. Create a new private method `_rerank_with_cross_encoder(self, query: str, candidates: list[tuple[IndianStandard, float, list[str]]], top_k: int) -> list[tuple[IndianStandard, float, list[str]]]`.
3. Inside this method:
   - Load or initialize the `CrossEncoder` from `sentence_transformers` (lazy-load and cache the model instance on `self._cross_encoder`).
   - Construct `(query, candidate_text)` pairs where `candidate_text = f"{std.is_code} {std.title} {std.scope}"`.
   - Call `self._cross_encoder.predict(pairs)` to get relevance logits.
   - Sort by logits descending, return top_k.
   - Update the `reasons` list to include `"Cross-Encoder reranked (score: {score:.3f})"`.
4. Modify `search()` method:
   - Change `top_k=top_k * 2` to `top_k=25` (or a configurable value) to retrieve more first-stage candidates.
   - After the existing hybrid scoring and before `return ranked[:top_k]`, call `_rerank_with_cross_encoder(query, ranked[:25], top_k)`.
5. The cross-encoder model **must** run on CUDA (`device="cuda:0"`).

### Acceptance Criteria
- [ ] Cross-encoder model loads on CUDA and reranks candidates
- [ ] The `search()` method retrieves 25 first-stage candidates, then reranks to final top_k
- [ ] Cross-encoder model name is configurable (not hardcoded)
- [ ] Reranking reasons appear in the match reasons list
- [ ] If cross-encoder fails to load, the system gracefully falls back to the original hybrid ranking with a logged warning

---

## Task 1.3: Strict Source Attribution & Rejection Criteria

**Files:**
- `d:\CODE\Hackathon\backend\engine\prompts\system_prompt.py`
- `d:\CODE\Hackathon\backend\engine\prompts\evaluation_prompt.py`

### What to Build

Update citation formatting rules in both prompt files to enforce a strict, parseable citation format and add explicit rejection instructions.

### How to Build

#### In `system_prompt.py` — Update `MASTER_SYSTEM_PROMPT`:

1. Find the `# EVIDENCE AND CITATION RULES` section (around line 152).
2. Replace the current citation rules:

   **Current:**
   ```
   1. For every clause-level claim, provide a citation in this format:
      File name, page number, clause number if available.
   2. If no clause number is available, cite file name and page number only.
   3. If no file name is available, cite the provided source label.
   ```

   **New:**
   ```
   1. For every clause-level claim, provide a citation in EXACTLY this format:
      [IS Number:Year, Clause X.Y, Page Z]
      Example: [IS 1786:2008, Clause 6.2, Page 12]
   2. If no clause number is available, use: [IS Number:Year, Page Z]
   3. If no page number is available, use: [IS Number:Year]
   4. If the standard is NOT provided in the retrieved context, explicitly state:
      "Standard not found in provided context. Cannot provide verified recommendation."
      Do NOT guess or fabricate any standard number, year, clause, or page.
   ```

3. Also add to the `# NON-NEGOTIABLE GROUNDING RULES` section (after rule 10):
   ```
   11. If no relevant standard is found in the provided context for the user's query, explicitly respond with:
       "No matching Indian Standard was found in the provided context for this query. Please verify with the official BIS catalog."
       Do not synthesize or guess a standard.
   ```

#### In `evaluation_prompt.py` — Update `EVALUATION_PROMPT_TEMPLATE`:

1. Find line ~62: `4. Cite file name, page number, and clause number where available.`
   Replace with: `4. Cite using the strict format: [IS Number:Year, Clause X.Y, Page Z]. If clause or page is unavailable, omit that field.`

2. Find in the Technical Parameter Match Matrix section:
   ```
   6. Citation must include file name, page number, and clause number if available.
      If clause number is unavailable, cite file and page only.
   ```
   Replace with:
   ```
   6. Citation must use the strict format: [IS Number:Year, Clause X.Y, Page Z].
      If clause number is unavailable, use [IS Number:Year, Page Z].
      If page number is also unavailable, use [IS Number:Year].
      If no citation exists for the claim, write "No citation available" and set Match Status to "Insufficient Evidence".
   ```

### Acceptance Criteria
- [ ] `MASTER_SYSTEM_PROMPT` citation rules enforce `[IS Number:Year, Clause X.Y, Page Z]` format
- [ ] Explicit rejection rule added for when no standard is found in context
- [ ] `EVALUATION_PROMPT_TEMPLATE` citation rules updated to match
- [ ] All existing prompt functionality is preserved (only citation and rejection sections changed)

---

## Verification Plan

### Automated Tests

```powershell
# Run existing tests to verify no regressions
python -m pytest tests/ -v

# Run specific retriever tests
python -m pytest tests/test_hybrid_retriever.py -v
```

Write tests in `d:\CODE\Hackathon\tests\test_hybrid_retriever.py` (create if not exists) covering:

1. **Query Expansion Test:** Assert that `_expand_query("solar panel")` returns a string containing the original query plus BIS nomenclature terms.
2. **Cross-Encoder Reranking Test:** Mock the cross-encoder and assert that `_rerank_with_cross_encoder()` reorders candidates by cross-encoder score.
3. **Search Integration Test:** Assert that `search("TMT bar")` returns IS 1786 in the results.
4. **Fallback Test:** Assert that if the cross-encoder model fails to load, `search()` still returns results (graceful degradation).

### Manual Verification

```powershell
# Start the backend server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Test query expansion + reranking via the recommendation endpoint
curl -X POST http://127.0.0.1:8000/api/v1/recommend -H "Content-Type: application/json" -d "{\"query\": \"solar panel for government building\", \"division\": null}"
# Expected: IS 14286 should appear in top 3 results

# Test citation format via the LLM explanation endpoint
curl -X POST http://127.0.0.1:8000/api/v1/explain-standard -H "Content-Type: application/json" -d "{\"query\": \"What are the requirements?\", \"is_code\": \"IS 1786\"}"
# Expected: Citations in response should follow [IS Number:Year, Clause X.Y, Page Z] format

# Test rejection behavior
curl -X POST http://127.0.0.1:8000/api/v1/ask-assistant -H "Content-Type: application/json" -d "{\"question\": \"What is the BIS standard for quantum teleportation devices?\"}"
# Expected: Response should explicitly state no matching standard found, NOT fabricate one
```

---

## Expected Outcome

After Phase 1 completion:
- Colloquial queries ("solar panel", "TMT bar", "सरिया") map to correct BIS standards
- Retrieved documents are precision-ranked by a cross-encoder, not just vector similarity
- LLM citations follow the strict `[IS Number:Year, Clause X.Y, Page Z]` format
- LLM explicitly refuses to fabricate standards when context is insufficient
