# Phase 2: Generation Guardrails & UX Streaming

## Project Context

**BIS-SpecAI** is an AI-powered Indian Standards (BIS) recommendation engine for e-Procurement portals (GeM, CPPP, State/PSU Tenders). It uses a local GGUF model via `llama-cpp-python` on an NVIDIA RTX 3050 6GB GPU for inference, with a FastAPI backend and React + TypeScript frontend.

The system recommends Indian Standards, resolves normative reference graphs, enforces QCO compliance, and supports multilingual Indic queries.

**Project root:** `d:\CODE\Hackathon`

**Coding rules:** Read `d:\CODE\Hackathon\GEMINI.md` for project-wide coding constraints.

---

## Phase Objective

Enforce strict structured generation to prevent the LLM from hallucinating Indian Standard codes, and fix the streaming transport layer so the frontend receives proper Server-Sent Events (SSE) for a real-time typing experience.

**Features to Build:**
1. Constrained Decoding & GBNF Grammars
2. Token Streaming (Server-Sent Events / SSE)

**Why Combined:** Both features modify the LLM generation layer and API routers. When implementing GBNF grammars, the streaming generator logic in `local_gguf_provider.py` must be tested to ensure constrained tokens are properly yielded. Fixing the streaming format at the same time ensures the UX layer correctly parses the constrained output.

---

## Prerequisites

**Phase 1 must be completed first.** Assumes:
- Cross-Encoder reranking is operational in `hybrid_retriever.py`
- Query expansion is working
- Citations are formatted as `[IS Number:Year, Clause X.Y, Page Z]` in prompt templates

---

## Files to Modify

| File | Action | Purpose |
|---|---|---|
| `d:\CODE\Hackathon\backend\engine\local_gguf_provider.py` | MODIFY | Add GBNF grammar constraints to generation calls |
| `d:\CODE\Hackathon\backend\api\llm_router.py` | MODIFY | Fix streaming to use proper SSE format |
| `d:\CODE\Hackathon\tests\test_local_gguf_provider.py` | CREATE or MODIFY | Tests for GBNF + streaming |
| `d:\CODE\Hackathon\tests\test_llm_router.py` | CREATE or MODIFY | Tests for SSE endpoints |

---

## Current Code: `local_gguf_provider.py`

**Path:** `d:\CODE\Hackathon\backend\engine\local_gguf_provider.py` (135 lines)

```python
"""Local GGUF LLM provider using llama-cpp-python with persistent VRAM caching."""
from __future__ import annotations
import asyncio
from pathlib import Path
import threading
import time
from typing import Any, AsyncGenerator
from backend.config.settings import app_settings
from backend.engine.gguf_loader import instantiate_llama
from backend.engine.llm_interface import BaseLlmProvider
from backend.logger.app_logger import get_logger

logger = get_logger("engine.local_gguf_provider")
_STREAM_END = object()


def _safe_get_next(iterator: Any) -> Any:
    """Fetch next item safely without raising StopIteration into an asyncio.Future."""
    return next(iterator, _STREAM_END)


class LocalGgufLlmProvider(BaseLlmProvider):
    """Local GGUF provider with CUDA GPU acceleration, warm-up, and zero-unload caching."""

    def __init__(
        self,
        model_path: str | None = None,
        n_ctx: int | None = None,
        n_threads: int | None = None,
        n_gpu_layers: int | None = None,
        chat_format: str | None = None,
    ) -> None:
        self._model_path = model_path or app_settings.llm.model_path
        self._n_ctx = n_ctx or app_settings.llm.n_ctx
        self._n_threads = n_threads or app_settings.llm.n_threads
        self._n_gpu_layers = n_gpu_layers if n_gpu_layers is not None else app_settings.llm.n_gpu_layers
        self._chat_format = chat_format or app_settings.llm.chat_format
        self._model, self._lock = None, threading.Lock()

    # ... (model loading, preload, warmup methods unchanged) ...

    def _sync_generate(self, prompt: str, system_prompt: str | None) -> str | None:
        with self._lock:
            if self._model is None:
                self._model = self._load_model()
            if self._model is None:
                return None
            msgs = [{"role": "system", "content": system_prompt or "Expert BIS advisor."}, {"role": "user", "content": prompt}]
            try:
                resp = self._model.create_chat_completion(
                    messages=msgs,
                    temperature=app_settings.llm.temperature,
                    max_tokens=app_settings.llm.max_tokens
                )
                choices = resp.get("choices", [])
                return str(choices[0]["message"].get("content", "")) if choices and "message" in choices[0] else None
            except (ValueError, RuntimeError, TypeError, KeyError, IndexError, OSError) as exc:
                logger.warning(f"[FALLBACK] GGUF inference error ({type(exc).__name__}: {exc})")
                return None

    def _sync_generate_stream(self, prompt: str, system_prompt: str | None) -> Any:
        with self._lock:
            if self._model is None:
                self._model = self._load_model()
            if self._model is None:
                yield "No LLM model is currently available (Local GGUF model not active)."
                return
            msgs = [{"role": "system", "content": system_prompt or "Expert BIS advisor."}, {"role": "user", "content": prompt}]
            try:
                resp = self._model.create_chat_completion(
                    messages=msgs,
                    temperature=app_settings.llm.temperature,
                    max_tokens=app_settings.llm.max_tokens,
                    stream=True
                )
                for chunk in resp:
                    choices = chunk.get("choices", [])
                    if choices and "delta" in choices[0]:
                        c = choices[0]["delta"].get("content", "")
                        if c:
                            yield c
            except (ValueError, RuntimeError, TypeError, KeyError, IndexError, OSError) as exc:
                logger.warning(f"[FALLBACK] GGUF streaming error ({type(exc).__name__}: {exc})")
                yield f"\n[Error: {type(exc).__name__}]"

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            out = await asyncio.to_thread(self._sync_generate, prompt, system_prompt)
            if out and out.strip():
                return out.strip()
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning(f"Local GGUF: Async generation error ({type(exc).__name__}: {exc})")
        return "No LLM model is currently available (Local GGUF model not active)."

    async def generate_text_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        try:
            gen = await asyncio.to_thread(self._sync_generate_stream, prompt, system_prompt)
            while True:
                chunk = await asyncio.to_thread(_safe_get_next, gen)
                if chunk is _STREAM_END:
                    break
                yield chunk
        except (ValueError, RuntimeError, OSError, Exception) as exc:
            logger.warning(f"Local GGUF: Async stream error ({type(exc).__name__}: {exc})")
            yield "\n[Stream Interrupted]"
```

**Key observations:**
- `create_chat_completion()` is called WITHOUT any `grammar` parameter — no constrained decoding
- Both `_sync_generate` and `_sync_generate_stream` need the grammar parameter added
- Uses `threading.Lock()` for serialization (Phase 3 will replace with asyncio.Queue)

---

## Current Code: `llm_router.py`

**Path:** `d:\CODE\Hackathon\backend\api\llm_router.py` (120 lines)

```python
# ... (imports, models, non-streaming endpoints unchanged) ...

@router.post("/explain-standard-stream")
async def explain_standard_stream(req: ExplainStandardRequest) -> StreamingResponse:
    """Stream LLM technical justification via SSE."""
    # ... (standard lookup, alert, evidences) ...

    async def stream_generator():
        try:
            async for chunk in llm_service.explain_recommendation_stream(
                query=req.query, standard=std, qco_alert=alert, document_chunks=evidences
            ):
                yield chunk
        except (ValueError, RuntimeError, OSError, Exception) as exc:
            yield f"\n[Stream error: {type(exc).__name__}]"

    return StreamingResponse(
        stream_generator(),
        media_type="text/plain",                    # <-- WRONG: should be "text/event-stream"
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@router.post("/ask-assistant-stream")
async def ask_assistant_stream(req: AssistantQuestionRequest) -> StreamingResponse:
    # ... (retrieval) ...

    async def stream_generator():
        try:
            async for chunk in llm_service.answer_procurement_query_stream(
                question=req.question, context_standards=standards, document_chunks=evidences
            ):
                yield chunk
        except (ValueError, RuntimeError, OSError, Exception) as exc:
            yield f"\n[Stream error: {type(exc).__name__}]"

    return StreamingResponse(
        stream_generator(),
        media_type="text/plain",                    # <-- WRONG: should be "text/event-stream"
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
```

**Key observations:**
- Both streaming endpoints use `media_type="text/plain"` — must be `"text/event-stream"`
- Chunks are yielded as raw text — must be formatted as SSE: `data: {chunk}\n\n`
- No terminal `data: [DONE]\n\n` event is sent

---

## Task 2.1: Constrained Decoding & GBNF Grammars

**File:** `d:\CODE\Hackathon\backend\engine\local_gguf_provider.py`

### What to Build

Integrate GBNF grammar constraints into `llama-cpp-python`'s `create_chat_completion()` calls so that Indian Standard code references in the LLM output are forced to follow the pattern `IS [digits]:[4-digit year]`.

### How to Build

1. Create a GBNF grammar file at a configurable path (e.g., `d:\CODE\Hackathon\backend\engine\grammars\bis_output.gbnf`). The grammar should constrain IS code references to the format `"IS " [0-9]+ ":" [0-9]{4}`.

   **Note:** The grammar should NOT constrain the entire output — only the IS code citation tokens. The rest of the output should be free-form text. Consider using `llama-cpp-python`'s `response_format` parameter with a JSON schema (via Pydantic model) as an alternative approach if the full GBNF grammar is too restrictive.

2. **Option A — GBNF Grammar File:**
   ```
   # Load grammar from file
   from llama_cpp import LlamaGrammar
   grammar = LlamaGrammar.from_file(grammar_path)
   resp = self._model.create_chat_completion(
       messages=msgs, grammar=grammar, ...
   )
   ```

3. **Option B — Pydantic JSON Schema (Recommended for structured responses):**
   ```python
   resp = self._model.create_chat_completion(
       messages=msgs,
       response_format={"type": "json_object", "schema": BISResponseSchema.model_json_schema()},
       ...
   )
   ```
   Where `BISResponseSchema` is a Pydantic model defining the expected output structure.

4. Add the grammar/schema to both `_sync_generate()` and `_sync_generate_stream()` methods.
5. Make the grammar file path configurable via `app_settings` — **do not hardcode**.
6. If grammar loading fails, log a warning and fall back to unconstrained generation.

### Acceptance Criteria
- [ ] GBNF grammar or JSON schema is applied to `create_chat_completion()` calls
- [ ] IS code references in LLM output follow `IS [digits]:[year]` pattern
- [ ] Grammar file path is configurable (not hardcoded)
- [ ] Graceful fallback if grammar fails to load
- [ ] Both streaming and non-streaming generation use the grammar

---

## Task 2.2: Token Streaming — Server-Sent Events (SSE)

**File:** `d:\CODE\Hackathon\backend\api\llm_router.py`

### What to Build

Fix both streaming endpoints to use proper SSE format so the frontend can consume events via `EventSource` API or Fetch chunked reading.

### How to Build

1. **Update `explain_standard_stream` endpoint:**

   Change the `stream_generator()` to yield SSE-formatted events:
   ```python
   async def stream_generator():
       try:
           async for chunk in llm_service.explain_recommendation_stream(
               query=req.query, standard=std, qco_alert=alert, document_chunks=evidences
           ):
               yield f"data: {chunk}\n\n"
       except (ValueError, RuntimeError, OSError, Exception) as exc:
           yield f"data: [ERROR: {type(exc).__name__}]\n\n"
       yield "data: [DONE]\n\n"
   ```

   Change `StreamingResponse`:
   ```python
   return StreamingResponse(
       stream_generator(),
       media_type="text/event-stream",
       headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache", "Connection": "keep-alive"},
   )
   ```

2. **Update `ask_assistant_stream` endpoint** with the exact same SSE formatting pattern.

3. **SSE Protocol Requirements:**
   - Each chunk must be prefixed with `data: ` and suffixed with `\n\n`
   - A final `data: [DONE]\n\n` event signals stream completion
   - `media_type` must be `"text/event-stream"`
   - Add `"Connection": "keep-alive"` header

### Acceptance Criteria
- [ ] Both `/explain-standard-stream` and `/ask-assistant-stream` return `Content-Type: text/event-stream`
- [ ] Each chunk is formatted as `data: {content}\n\n`
- [ ] A final `data: [DONE]\n\n` event is sent when the stream completes
- [ ] Error events are formatted as `data: [ERROR: ...]\n\n`
- [ ] Frontend can consume the stream using `EventSource` or Fetch API

---

## Verification Plan

### Automated Tests

```powershell
# Run all tests
python -m pytest tests/ -v

# Run specific tests
python -m pytest tests/test_local_gguf_provider.py -v
python -m pytest tests/test_llm_router.py -v
```

Write tests covering:

1. **GBNF Grammar Test:** Mock `create_chat_completion` and verify the `grammar` parameter is passed.
2. **SSE Format Test:** Use FastAPI `TestClient` to call `/ask-assistant-stream` and verify:
   - Response `Content-Type` is `text/event-stream`
   - Response body contains `data: ` prefixed lines
   - Response body ends with `data: [DONE]\n\n`
3. **Grammar Fallback Test:** Verify that if grammar file doesn't exist, generation still works without grammar.

### Manual Verification

```powershell
# Start backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Test SSE streaming format
curl -X POST http://127.0.0.1:8000/api/v1/ask-assistant-stream -H "Content-Type: application/json" -d "{\"question\": \"What BIS standards apply to TMT steel bars?\"}" -N
# Expected output format:
# data: The primary
# data:  Indian Standard
# data:  for TMT
# data:  steel bars is
# data:  [IS 1786:2008
# data: , Clause 6.2
# data: , Page 12]
# data: [DONE]

# Verify Content-Type header
curl -X POST http://127.0.0.1:8000/api/v1/explain-standard-stream -H "Content-Type: application/json" -d "{\"query\": \"requirements\", \"is_code\": \"IS 1786\"}" -v -N 2>&1 | findstr "Content-Type"
# Expected: Content-Type: text/event-stream
```

---

## Expected Outcome

After Phase 2 completion:
- LLM output cannot produce hallucinated IS codes — grammar constraints force valid format
- Frontend receives proper SSE events with `data:` prefix and `[DONE]` terminator
- Real-time typing effect works correctly on the frontend
- All constrained tokens are properly yielded through the streaming pipeline
