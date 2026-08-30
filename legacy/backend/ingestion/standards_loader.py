"""Data loader and indexer for Indian Standards knowledge base."""
from __future__ import annotations

import json
from pathlib import Path
from backend.config.settings import app_settings
from backend.models.standard_model import IndianStandard


class StandardsLoader:
    """Loads and caches Indian Standards from local JSON repository."""

    def __init__(self, db_path: str | None = None) -> None:
        self._path = Path(db_path or app_settings.storage.standards_file)
        self._standards: dict[str, IndianStandard] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load standards from disk or initialize empty map."""
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as handle:
                raw_list = json.load(handle)
                for item in raw_list:
                    std = IndianStandard.model_validate(item)
                    self._standards[std.is_code.strip().upper()] = std
        except (json.JSONDecodeError, OSError, ValueError):
            self._standards = {}

    def get_all_standards(self) -> list[IndianStandard]:
        """Return list of all loaded Indian Standards."""
        return list(self._standards.values())

    def get_by_code(self, is_code: str) -> IndianStandard | None:
        """Retrieve standard by exact or partial IS code."""
        norm = is_code.strip().upper()
        if norm in self._standards:
            return self._standards[norm]
        for code, std in self._standards.items():
            if norm in code or code in norm:
                return std
        return None

    def save_standards(self, standards: list[IndianStandard]) -> None:
        """Persist list of Indian Standards to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [s.model_dump() for s in standards]
        with open(self._path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        self._load_data()
