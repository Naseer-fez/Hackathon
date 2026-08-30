"""Registry and lookup service for mandatory Quality Control Orders."""
from __future__ import annotations

import json
from pathlib import Path
from backend.config.settings import app_settings
from backend.models.standard_model import CertificationScheme, MandatoryQCO


class QcoRegistry:
    """Registry maintaining active Indian Quality Control Orders."""

    def __init__(self, qco_file_path: str | None = None) -> None:
        self._path = Path(qco_file_path or app_settings.storage.qco_file)
        self._registry: dict[str, MandatoryQCO] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load QCO database from disk if available."""
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
                for is_code, data in raw.items():
                    self._registry[is_code.strip().upper()] = (
                        MandatoryQCO.model_validate(data)
                    )
        except (json.JSONDecodeError, OSError, ValueError):
            self._registry = {}

    def get_qco_for_standard(self, is_code: str) -> MandatoryQCO:
        """Retrieve QCO mandatory requirements for given Indian Standard."""
        normalized = is_code.strip().upper()
        if normalized in self._registry:
            return self._registry[normalized]
        for key, qco in self._registry.items():
            if key in normalized or normalized in key:
                return qco
        return MandatoryQCO(
            is_mandatory=False,
            scheme=CertificationScheme.NONE,
            clause_requirement="Voluntary compliance recommended.",
        )

    def register_qco(self, is_code: str, qco: MandatoryQCO) -> None:
        """Register or update a QCO in memory."""
        self._registry[is_code.strip().upper()] = qco

    def get_all_qcos(self) -> dict[str, MandatoryQCO]:
        """Return full map of registered QCOs."""
        return self._registry.copy()
