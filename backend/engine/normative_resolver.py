"""Graph resolver for allied standards, normative references, and supersessions."""
from __future__ import annotations

from backend.ingestion.standards_loader import StandardsLoader
from backend.models.recommendation_model import AlliedStandardItem
from backend.models.standard_model import IndianStandard, StandardStatus
from backend.logger.app_logger import get_logger

logger = get_logger("engine.normative_resolver")


class NormativeGraphCache:
    """Pre-computes and caches normative references in RAM at startup."""

    def __init__(self, loader: StandardsLoader) -> None:
        self._graph: dict[str, list[AlliedStandardItem]] = {}
        self._build_cache(loader)

    def _build_cache(self, loader: StandardsLoader) -> None:
        logger.info("Building in-memory normative reference graph cache...")
        standards = loader.get_all_standards()
        for std in standards:
            allied: list[AlliedStandardItem] = []
            
            for code in std.normative_references:
                ref = loader.get_by_code(code)
                title = ref.title if ref else f"Referenced standard {code}"
                allied.append(
                    AlliedStandardItem(
                        is_code=code, title=title, relation_type="Normative Reference",
                        is_mandatory=True, details="Direct compliance required to fulfill parent standard."
                    )
                )

            for test in std.test_methods:
                code = test.split("(")[0].strip()
                allied.append(
                    AlliedStandardItem(
                        is_code=code, title=test, relation_type="Test Method",
                        is_mandatory=True, details="Prescribed test procedure for quality assurance."
                    )
                )

            for safety in std.safety_standards:
                code = safety.split("(")[0].strip()
                allied.append(
                    AlliedStandardItem(
                        is_code=code, title=safety, relation_type="Safety Standard",
                        is_mandatory=True, details="Statutory safety and hazard mitigation standard."
                    )
                )

            for inst in std.installation_standards:
                code = inst.split("(")[0].strip()
                allied.append(
                    AlliedStandardItem(
                        is_code=code, title=inst, relation_type="Installation Code",
                        is_mandatory=False, details="Field installation and commissioning code of practice."
                    )
                )
            
            self._graph[std.is_code.strip().upper()] = allied
        logger.info(f"Successfully cached relationships for {len(standards)} standards in RAM.")

    def get_allied(self, is_code: str) -> list[AlliedStandardItem]:
        """O(1) retrieval of allied standards from RAM cache."""
        return self._graph.get(is_code.strip().upper(), [])


class NormativeResolver:
    """Traverses relationships to resolve allied standards and supersessions."""

    def __init__(self, loader: StandardsLoader | None = None) -> None:
        self._loader = loader or StandardsLoader()
        self._cache = NormativeGraphCache(self._loader)

    def resolve_allied(self, std: IndianStandard) -> list[AlliedStandardItem]:
        """Resolve all linked normative standards using the in-memory graph cache."""
        return self._cache.get_allied(std.is_code)

    def check_deprecation(self, std: IndianStandard) -> str | None:
        """Check if standard is superseded or outdated."""
        if std.status == StandardStatus.SUPERSEDED:
            return (
                f"WARNING: {std.is_code} is SUPERSEDED. "
                f"Use latest standard: {std.superseded_by or 'Check latest BIS gazette'}."
            )
        return None
