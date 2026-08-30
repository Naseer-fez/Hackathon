"""Aggregates all Indian Standards and persists initial database files."""
from __future__ import annotations

import json
from pathlib import Path
from backend.config.settings import app_settings
from backend.data.civil_standards import get_civil_standards
from backend.data.electrical_standards import get_electrical_standards
from backend.data.electronics_solar_standards import (
    get_electronics_solar_standards,
)
from backend.data.mech_safety_standards import get_mech_safety_standards
from backend.models.standard_model import IndianStandard


def build_all_standards() -> list[IndianStandard]:
    """Combine all division standards into a single collection."""
    all_stds: list[IndianStandard] = []
    all_stds.extend(get_civil_standards())
    all_stds.extend(get_electrical_standards())
    all_stds.extend(get_electronics_solar_standards())
    all_stds.extend(get_mech_safety_standards())
    return all_stds


def generate_seed_data(
    standards_out: str | Path | None = None,
    qco_out: str | Path | None = None,
) -> int:
    """Generate and write standards database and QCO registry to disk."""
    stds_path = Path(standards_out or app_settings.storage.standards_file)
    qco_path = Path(qco_out or app_settings.storage.qco_file)

    stds_path.parent.mkdir(parents=True, exist_ok=True)
    qco_path.parent.mkdir(parents=True, exist_ok=True)

    standards = build_all_standards()
    stds_payload = [s.model_dump() for s in standards]

    with open(stds_path, "w", encoding="utf-8") as f:
        json.dump(stds_payload, f, indent=2, ensure_ascii=False)

    qco_map = {
        s.is_code: s.mandatory_qco.model_dump()
        for s in standards
        if s.mandatory_qco.is_mandatory
    }
    with open(qco_path, "w", encoding="utf-8") as f:
        json.dump(qco_map, f, indent=2, ensure_ascii=False)

    return len(standards)


if __name__ == "__main__":
    count = generate_seed_data()
    print(f"Successfully generated {count} Indian Standards.")
