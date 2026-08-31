"""Unit tests for CUDA GPU layer offloading and fallback in LocalGgufLlmProvider."""
from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from backend.config.settings import app_settings
from backend.engine.local_gguf_provider import LocalGgufLlmProvider


def test_gpu_offload_settings_configured() -> None:
    """Verify settings schema includes n_gpu_layers and chat_format."""
    assert hasattr(app_settings.llm, "n_gpu_layers")
    assert isinstance(app_settings.llm.n_gpu_layers, int)
    assert app_settings.llm.n_gpu_layers > 0
    assert bool(app_settings.llm.chat_format)


def test_provider_initializes_with_gpu_layers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify LocalGgufLlmProvider passes nf_gpu_layers to Llama constructor."""
    captured_args: dict[str, object] = {}

    def mock_init(self: LocalGgufLlmProvider, ctx: int, gpu_layers: int | None = None) -> MagicMock:
        captured_args["ctx"] = ctx
        captured_args["gpu_layers"] = gpu_layers if gpu_layers is not None else self._n_gpu_layers
        return MagicMock()

    monkeypatch.setattr(LocalGgufLlmProvider, "_init_llama_instance", mock_init)
    monkeypatch.setattr("pathlib.Path.exists", lambda _: True)

    provider = LocalGgufLlmProvider(n_gpu_layers=33)
    model = provider._load_model()
    assert model is not None
    assert captured_args.get("gpu_layers") == 33


def test_provider_falls_back_to_cpu_when_gpu_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify LocalGgufLlmProvider falls back to CPU if GPU load fails."""
    attempts: list[tuple[int, int | None]] = []

    def mock_init(self: LocalGgufLlmProvider, ctx: int, gpu_layers: int | None = None) -> MagicMock:
        effective_gpu = gpu_layers if gpu_layers is not None else self._n_gpu_layers
        attempts.append((ctx, effective_gpu))
        if effective_gpu != 0:
            raise RuntimeError("CUDA out of memory")
        return MagicMock()

    monkeypatch.setattr(LocalGgufLlmProvider, "_init_llama_instance", mock_init)
    monkeypatch.setattr("pathlib.Path.exists", lambda _: True)

    provider = LocalGgufLlmProvider(n_ctx=2048, n_gpu_layers=33)
    model = provider._load_model()
    assert model is not None
    gpu_attempts = [a for a in attempts if a[1] == 33]
    cpu_attempts = [a for a in attempts if a[1] == 0]
    assert len(gpu_attempts) == 2
    assert len(cpu_attempts) >= 1
    assert cpu_attempts[0][1] == 0
