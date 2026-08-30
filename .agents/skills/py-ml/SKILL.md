---
name: py-ml
description: >-
  Python and ML/AI development patterns, templates, and conventions.
  Use when working with .py files, PyTorch models, training loops,
  data pipelines, or any machine learning code.
---

# Python & ML Skill

## Module Template
```python
"""[MOD purpose - 1 line]"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# ── Constants ──────────────────────────────
CONST: type = value

# ── Helpers ────────────────────────────────
def helper_fn(arg: type) -> RET_type:
    """[FN purpose]"""
    ...

# ── Core Logic ─────────────────────────────
class CoreClass:
    def __init__(self, arg: type) -> None:
        self._arg = arg

    def method(self, arg: type) -> RET_type:
        ...

# ── Entry Point ────────────────────────────
def main() -> None:
    ...
```

## Embedding & Offline Fallback Pattern
```python
class ResilientEmbeddingService:
    """Loads transformer model with graceful fallback to deterministic neural hashing."""
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: Any = None
        self._offline = False

    def get_embedding(self, text: str) -> np.ndarray:
        try:
            if not self._offline and self._model is None:
                self._model = SentenceTransformer(self._model_name)
            if self._model:
                return self._model.encode(text, normalize_embeddings=True)
        except (OSError, RuntimeError, ImportError):
            self._offline = True
        return self._hash_embed(text)
```

## Mandatory GPU Acceleration & CUDA Enforcement
- Target Hardware: NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB VRAM).
- PyTorch tensors and SentenceTransformer embeddings MUST load on `cuda:0` when GPU is enabled.
- GGUF llama.cpp inference must offload layers to GPU VRAM (`n_gpu_layers: 99`).
- Never install or revert to `+cpu` wheels in `.venv`. Always use CUDA 12.4+ wheels (`--index-url https://download.pytorch.org/whl/cu124`).
- Storage Preference: Always use `D:\` drive for model downloads and pip cache (`--cache-dir D:\pip_cache`).

## Anti-Patterns [NEVER DO]
- ❌ `import *`
- ❌ Mutable default args: `def fn(x=[])`
- ❌ Bare `except:`
- ❌ Global mutable ST in MODs
- ❌ Missing `torch.no_grad()` during inference
- ❌ Reverting or falling back silently to CPU without diagnostic logging
- ❌ Installing CPU-only `+cpu` PyTorch or non-CUDA llama-cpp-python
- ❌ Unhandled network timeouts in transformer downloads
