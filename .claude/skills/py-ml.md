# PYTHON & ML SKILL

## Module Template
```python
"""[MOD purpose - 1 line]"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import ...

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

## Model Template
```python
class Model(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self._cfg = config
        self._build_layers()

    def _build_layers(self) -> None: ...
    def forward(self, x: Tensor) -> Tensor: ...
```

## Training Loop
```python
async def train_epoch(
    model: Model, loader: DataLoader,
    opt: Optimizer, cfg: TrainConfig,
) -> dict[str, float]:
    model.train()
    metrics = {"loss": 0.0, "acc": 0.0}
    for batch in loader:
        loss, preds = model(batch)
        opt.zero_grad(); loss.backward(); opt.step()
        metrics["loss"] += loss.item()
    return {k: v / len(loader) for k, v in metrics.items()}
```

## Common Imports
```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from transformers import AutoModel, AutoTokenizer
import numpy as np
from pathlib import Path
from dataclasses import dataclass
```

## Anti-Patterns [NEVER DO]
- ❌ `import *`
- ❌ Mutable default args: `def fn(x=[])`
- ❌ Bare `except:`
- ❌ Global mutable ST in MODs
- ❌ Missing `torch.no_grad()` during inference
- ❌ Not calling `model.eval()` before inference
