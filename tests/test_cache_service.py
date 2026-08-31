"""Tests for SemanticCacheService: store, retrieve, similarity threshold, and invalidation."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from backend.engine.cache_service import SemanticCacheService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pipeline_response(**overrides: Any) -> Any:
    """Build a minimal PipelineResponse-like object for testing."""
    from backend.engine.pipeline import PipelineResponse
    defaults = {
        "query": "test query",
        "detected_language": "en",
        "extracted_text_snippet": "",
        "recommendations": [],
        "document_evidences": [],
    }
    defaults.update(overrides)
    return PipelineResponse(**defaults)


def _deterministic_embedding(text: str, dim: int = 384) -> np.ndarray:
    """Simple deterministic embedding for testing (hash-based)."""
    import hashlib
    vec = np.zeros(dim, dtype=np.float32)
    for i, ch in enumerate(text.lower()):
        idx = int(hashlib.md5(ch.encode()).hexdigest(), 16) % dim
        vec[idx] += float(i + 1)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def cache_service(tmp_path: Path) -> SemanticCacheService:
    """Create a SemanticCacheService with isolated temp SQLite DB and mocked embeddings."""
    db_path = str(tmp_path / "test_cache.db")

    mock_embed_svc = MagicMock()
    mock_embed_svc.get_embedding.side_effect = _deterministic_embedding
    mock_embed_svc.compute_similarity.side_effect = (
        lambda a, b: float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        if (np.linalg.norm(a) > 0 and np.linalg.norm(b) > 0)
        else 0.0
    )

    with patch("backend.engine.cache_service.app_settings") as mock_settings:
        mock_settings.cache.sqlite_db_path = db_path
        mock_settings.cache.similarity_threshold = 0.95
        svc = SemanticCacheService()
        svc._embed = mock_embed_svc
    return svc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCacheStoreAndRetrieve:
    """Verify store + retrieve round-trip with identical queries."""

    def test_store_and_retrieve_exact_match(self, cache_service: SemanticCacheService) -> None:
        """Store a response, retrieve with identical query → cache hit."""
        resp = _make_pipeline_response(query="Portland cement standards")

        async def run() -> Any:
            await cache_service.store_cache("Portland cement standards", resp)
            return await cache_service.check_cache("Portland cement standards")

        cached = asyncio.get_event_loop().run_until_complete(run())
        assert cached is not None
        assert cached.query == "Portland cement standards"


class TestCacheMiss:
    """Verify cache miss on unrelated queries."""

    def test_cache_miss_on_unrelated_query(self, cache_service: SemanticCacheService) -> None:
        """Retrieve with semantically different query → returns None."""
        resp = _make_pipeline_response(query="Portland cement standards")

        async def run() -> Any:
            await cache_service.store_cache("Portland cement standards", resp)
            return await cache_service.check_cache("xyz completely different unrelated topic")

        cached = asyncio.get_event_loop().run_until_complete(run())
        assert cached is None


class TestSimilarityThreshold:
    """Verify similarity threshold is enforced."""

    def test_below_threshold_is_miss(self, cache_service: SemanticCacheService) -> None:
        """Queries with similarity below threshold are NOT cache hits."""
        resp = _make_pipeline_response(query="TMT steel bars IS 1786")

        async def run() -> Any:
            await cache_service.store_cache("TMT steel bars IS 1786", resp)
            # Use a very high threshold to force a miss
            return await cache_service.check_cache(
                "TMT steel bars IS 1786 extra words here", threshold=0.9999
            )

        cached = asyncio.get_event_loop().run_until_complete(run())
        assert cached is None


class TestInvalidateCache:
    """Verify cache invalidation clears all entries."""

    def test_invalidate_clears_all(self, cache_service: SemanticCacheService) -> None:
        """After invalidate_cache(), previously cached query → miss."""
        resp = _make_pipeline_response(query="Portland cement")

        async def run() -> Any:
            await cache_service.store_cache("Portland cement", resp)
            # Verify it's cached
            hit = await cache_service.check_cache("Portland cement")
            assert hit is not None
            # Invalidate
            await cache_service.invalidate_cache()
            # Verify miss
            return await cache_service.check_cache("Portland cement")

        cached = asyncio.get_event_loop().run_until_complete(run())
        assert cached is None


class TestCacheDbPath:
    """Verify the SQLite DB is created at the configured path."""

    def test_cache_db_path_from_config(self, cache_service: SemanticCacheService) -> None:
        """SQLite DB file is created at the configured path."""
        resp = _make_pipeline_response(query="test")

        async def run() -> None:
            await cache_service.store_cache("test", resp)

        asyncio.get_event_loop().run_until_complete(run())
        assert Path(cache_service._db_path).exists()
