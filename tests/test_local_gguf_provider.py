"""Tests for LocalGgufLlmProvider GBNF grammar integration and generation."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from backend.engine.local_gguf_provider import LocalGgufLlmProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_settings(tmp_path: Path) -> Any:
    """Patch app_settings with grammar-enabled config pointing to a temp GBNF file."""
    gbnf_path = tmp_path / "test.gbnf"
    gbnf_path.write_text('root ::= [a-zA-Z .,!?0-9:]*\n')

    mock_llm = MagicMock()
    mock_llm.model_path = str(tmp_path / "fake.gguf")
    mock_llm.n_ctx = 512
    mock_llm.n_threads = 1
    mock_llm.n_gpu_layers = 0
    mock_llm.chat_format = "chatml"
    mock_llm.temperature = 0.2
    mock_llm.max_tokens = 64
    mock_llm.enable_grammar = True
    mock_llm.grammar_file = str(gbnf_path)

    mock_llama_cpp = MagicMock()
    mock_grammar = MagicMock()
    mock_llama_cpp.LlamaGrammar = mock_grammar

    with patch("backend.engine.local_gguf_provider.app_settings") as patched, \
         patch.dict("sys.modules", {"llama_cpp": mock_llama_cpp, "llama_cpp.llama_cpp": MagicMock()}):
        patched.llm = mock_llm
        yield patched, gbnf_path


@pytest.fixture()
def mock_settings_no_grammar(tmp_path: Path) -> Any:
    """Patch app_settings with grammar disabled."""
    mock_llm = MagicMock()
    mock_llm.model_path = str(tmp_path / "fake.gguf")
    mock_llm.n_ctx = 512
    mock_llm.n_threads = 1
    mock_llm.n_gpu_layers = 0
    mock_llm.chat_format = "chatml"
    mock_llm.temperature = 0.2
    mock_llm.max_tokens = 64
    mock_llm.enable_grammar = False
    mock_llm.grammar_file = ""

    with patch("backend.engine.local_gguf_provider.app_settings") as patched:
        patched.llm = mock_llm
        yield patched


# ---------------------------------------------------------------------------
# Grammar loading tests
# ---------------------------------------------------------------------------

class TestGrammarLoading:
    """Verify grammar is loaded, cached, and degrades gracefully."""

    def test_grammar_loaded_when_enabled(self, mock_settings: Any) -> None:
        """Grammar file exists and enable_grammar=True → _load_grammar returns non-None."""
        _patched, gbnf_path = mock_settings
        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False

        with patch("backend.engine.local_gguf_provider.app_settings", _patched):
            grammar = provider._load_grammar()

        assert grammar is not None

    def test_grammar_none_when_disabled(self, mock_settings_no_grammar: Any) -> None:
        """enable_grammar=False → _load_grammar returns None."""
        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False
        assert provider._load_grammar() is None

    def test_grammar_none_when_file_missing(self, mock_settings: Any) -> None:
        """Grammar file does not exist → _load_grammar returns None (graceful fallback)."""
        _patched, gbnf_path = mock_settings
        gbnf_path.unlink()  # delete the file

        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False
        assert provider._load_grammar() is None

    def test_grammar_cached_after_first_load(self, mock_settings: Any) -> None:
        """Grammar is loaded once and cached — subsequent calls return cached value."""
        _patched, _gbnf_path = mock_settings
        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False

        first = provider._load_grammar()
        second = provider._load_grammar()
        assert first is second
        assert provider._grammar_loaded is True


# ---------------------------------------------------------------------------
# Generation tests (grammar passed to model)
# ---------------------------------------------------------------------------

class TestGrammarPassedToGeneration:
    """Verify grammar kwarg reaches create_chat_completion in both modes."""

    def test_grammar_passed_to_sync_generate(self, mock_settings: Any) -> None:
        """_sync_generate passes grammar= kwarg to create_chat_completion."""
        _patched, _gbnf_path = mock_settings
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "IS 1786:2008 applies to TMT bars."}}]
        }

        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False
        provider._model = mock_model
        provider._lock = __import__("threading").Lock()

        result = provider._sync_generate("test prompt", "system")

        call_kwargs = mock_model.create_chat_completion.call_args
        assert "grammar" in call_kwargs.kwargs
        assert call_kwargs.kwargs["grammar"] is not None
        assert "IS 1786:2008" in (result or "")

    def test_grammar_passed_to_sync_generate_stream(self, mock_settings: Any) -> None:
        """_sync_generate_stream passes grammar= kwarg to create_chat_completion."""
        _patched, _gbnf_path = mock_settings
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = iter([
            {"choices": [{"delta": {"content": "IS 456:2000"}}]},
            {"choices": [{"delta": {"content": " for concrete."}}]},
        ])

        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False
        provider._model = mock_model
        provider._lock = __import__("threading").Lock()

        chunks = list(provider._sync_generate_stream("test prompt", "system"))

        call_kwargs = mock_model.create_chat_completion.call_args
        assert "grammar" in call_kwargs.kwargs
        assert call_kwargs.kwargs["grammar"] is not None
        assert any("IS 456:2000" in c for c in chunks)
        assert any("concrete" in c for c in chunks)


# ---------------------------------------------------------------------------
# Inference fallback tests
# ---------------------------------------------------------------------------

class TestGrammarInferenceFallback:
    """Verify that grammar-related runtime errors fall back to unconstrained generation."""

    def test_sync_generate_falls_back_on_grammar_error(self, mock_settings: Any) -> None:
        """If grammar causes RuntimeError, retry without grammar succeeds."""
        _patched, _gbnf_path = mock_settings
        mock_model = MagicMock()

        # First call (with grammar) raises, second call (without) succeeds
        mock_model.create_chat_completion.side_effect = [
            RuntimeError("grammar mismatch"),
            {"choices": [{"message": {"content": "Fallback response with IS 1786:2008."}}]},
        ]

        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False
        provider._model = mock_model
        provider._lock = __import__("threading").Lock()

        result = provider._sync_generate("test prompt", "system")

        assert mock_model.create_chat_completion.call_count == 2
        assert result is not None
        assert "Fallback response" in result

    def test_stream_falls_back_on_grammar_error(self, mock_settings: Any) -> None:
        """If grammar causes RuntimeError during streaming, retry without grammar succeeds."""
        _patched, _gbnf_path = mock_settings
        mock_model = MagicMock()

        # First call (with grammar) raises, second call (without) returns chunks
        mock_model.create_chat_completion.side_effect = [
            RuntimeError("grammar sampling error"),
            iter([
                {"choices": [{"delta": {"content": "Unconstrained "}}]},
                {"choices": [{"delta": {"content": "prose output."}}]},
            ]),
        ]

        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False
        provider._model = mock_model
        provider._lock = __import__("threading").Lock()

        chunks = list(provider._sync_generate_stream("test prompt", "system"))

        assert mock_model.create_chat_completion.call_count == 2
        assert any("Unconstrained" in c for c in chunks)
        assert any("prose" in c for c in chunks)


# ---------------------------------------------------------------------------
# Async interface tests
# ---------------------------------------------------------------------------

class TestAsyncGeneration:
    """Verify async wrappers work correctly."""

    def test_generate_text_returns_content(self, mock_settings: Any) -> None:
        """generate_text() returns stripped content from the model."""
        _patched, _gbnf_path = mock_settings
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "  IS 1786:2008 is the standard for TMT bars.  "}}]
        }

        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False
        provider._model = mock_model
        provider._lock = __import__("threading").Lock()
        provider._semaphore = asyncio.Semaphore(1)
        provider._queue_count = 0
        provider._max_queue = 5

        result = asyncio.get_event_loop().run_until_complete(
            provider.generate_text("test prompt", "system")
        )
        assert result == "IS 1786:2008 is the standard for TMT bars."

    def test_generate_text_stream_yields_chunks(self, mock_settings: Any) -> None:
        """generate_text_stream() yields each content chunk from the model."""
        _patched, _gbnf_path = mock_settings
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = iter([
            {"choices": [{"delta": {"content": "Natural English prose "}}]},
            {"choices": [{"delta": {"content": "alongside IS 456:2000 citation."}}]},
        ])

        provider = LocalGgufLlmProvider.__new__(LocalGgufLlmProvider)
        provider._grammar = None
        provider._grammar_loaded = False
        provider._model = mock_model
        provider._lock = __import__("threading").Lock()
        provider._semaphore = asyncio.Semaphore(1)
        provider._queue_count = 0
        provider._max_queue = 5

        async def collect() -> list[str]:
            return [c async for c in provider.generate_text_stream("test", "sys")]

        chunks = asyncio.get_event_loop().run_until_complete(collect())
        combined = "".join(chunks)
        # Verify natural prose AND constrained IS code coexist
        assert "Natural English prose" in combined
        assert "IS 456:2000" in combined
