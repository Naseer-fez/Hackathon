"""Semantic query cache using SQLite for sub-5ms responses on repeated/similar queries."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import aiosqlite
import numpy as np

from backend.config.settings import app_settings
from backend.engine.embedding_service import get_embedding_service
from backend.logger.app_logger import get_logger

if TYPE_CHECKING:
    from backend.engine.pipeline import PipelineResponse

logger = get_logger("engine.cache_service")

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS semantic_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    query_embedding BLOB NOT NULL,
    response_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    hit_count INTEGER DEFAULT 0
)
"""


class SemanticCacheService:
    """Lightweight semantic cache backed by SQLite — zero-GPU fast-path for repeated queries."""

    def __init__(self) -> None:
        self._db_path: str = app_settings.cache.sqlite_db_path
        self._threshold: float = app_settings.cache.similarity_threshold
        self._embed = get_embedding_service()
        self._table_ready: bool = False

    async def _ensure_table(self) -> None:
        """Create the cache table if it does not exist (idempotent)."""
        if self._table_ready:
            return
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(_CREATE_TABLE_SQL)
            await db.commit()
        self._table_ready = True

    async def check_cache(
        self, query: str, threshold: float | None = None,
    ) -> PipelineResponse | None:
        """Return cached response if a semantically similar query exists, else None."""
        from backend.engine.pipeline import PipelineResponse

        await self._ensure_table()
        t0 = time.perf_counter()
        thr = threshold if threshold is not None else self._threshold
        query_vec = self._embed.get_embedding(query)

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT id, query_embedding, response_json FROM semantic_cache"
            )
            rows = await cursor.fetchall()

        best_id, best_sim, best_json = None, -1.0, None
        for row_id, emb_blob, resp_json in rows:
            cached_vec = np.frombuffer(emb_blob, dtype=np.float32)
            sim = self._embed.compute_similarity(query_vec, cached_vec)
            if sim > best_sim:
                best_id, best_sim, best_json = row_id, sim, resp_json

        if best_sim >= thr and best_json is not None:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    "UPDATE semantic_cache SET hit_count = hit_count + 1 WHERE id = ?",
                    (best_id,),
                )
                await db.commit()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            logger.info(f"Cache HIT (sim={best_sim:.4f}, {elapsed_ms:.1f}ms)")
            return PipelineResponse.model_validate_json(best_json)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        logger.debug(f"Cache MISS (best_sim={best_sim:.4f}, {elapsed_ms:.1f}ms)")
        return None

    async def store_cache(self, query: str, response: PipelineResponse) -> None:
        """Persist a query-response pair into the semantic cache."""
        await self._ensure_table()
        query_vec = self._embed.get_embedding(query)
        emb_blob = query_vec.astype(np.float32).tobytes()
        resp_json = response.model_dump_json()
        now = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO semantic_cache (query_text, query_embedding, response_json, created_at) VALUES (?, ?, ?, ?)",
                (query, emb_blob, resp_json, now),
            )
            await db.commit()
        logger.info(f"Cache STORE for query: {query[:60]}...")

    async def invalidate_cache(self) -> None:
        """Clear all cached entries (admin use)."""
        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM semantic_cache")
            await db.commit()
        logger.info("Cache INVALIDATED — all entries cleared")
