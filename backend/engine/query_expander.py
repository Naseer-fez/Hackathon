"""Query expansion and domain normalization for BIS trade-term mapping."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from backend.config.settings import app_settings
from backend.logger.app_logger import get_logger

logger = get_logger("engine.query_expander")


class QueryExpander:
    """Expands colloquial and trade terms to formal BIS nomenclature before retrieval."""

    def __init__(self) -> None:
        self._expansions: list[dict[str, Any]] = self._load_expansions()

    def _load_expansions(self) -> list[dict[str, Any]]:
        """Load domain expansion dictionary from the configured YAML file."""
        expansions_path = Path(app_settings.ai_engine.domain_expansions_file)
        if not expansions_path.exists():
            logger.warning(f"Domain expansions file not found: {expansions_path}")
            return []
        try:
            with open(expansions_path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            if not isinstance(data, dict) or "expansions" not in data:
                logger.warning(f"Invalid domain expansions format in {expansions_path}")
                return []
            entries = data["expansions"]
            logger.info(f"Loaded {len(entries)} domain expansion entries from {expansions_path}")
            return entries
        except (yaml.YAMLError, OSError) as exc:
            logger.warning(f"Failed to load domain expansions: {type(exc).__name__}: {exc}")
            return []

    def expand(self, query: str) -> str:
        """Expand query by appending matched BIS nomenclature terms.

        The original query text is always preserved; expansion is additive only.
        """
        if not self._expansions:
            return query

        query_lower = query.lower()
        matched_terms: list[str] = []

        for entry in self._expansions:
            triggers: list[str] = entry.get("triggers", [])
            expansion: str = entry.get("expansion", "")
            if not expansion:
                continue
            for trigger in triggers:
                if trigger.lower() in query_lower:
                    matched_terms.append(expansion)
                    break

        if not matched_terms:
            return query

        expanded = f"{query} {' '.join(matched_terms)}"
        logger.info(f"Query expanded: '{query}' -> '{expanded[:120]}...'")
        return expanded
