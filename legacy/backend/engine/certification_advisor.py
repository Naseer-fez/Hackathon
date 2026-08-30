"""Evaluates mandatory QCO and BIS certification requirements."""
from __future__ import annotations

from backend.ingestion.qco_registry import QcoRegistry
from backend.models.standard_model import CertificationScheme, IndianStandard


class CertificationAdvisor:
    """Provides certification guidance and statutory compliance alerts."""

    def __init__(self, qco_reg: QcoRegistry | None = None) -> None:
        self._qco_reg = qco_reg or QcoRegistry()

    def get_certification_alert(self, std: IndianStandard) -> str:
        """Generate human-readable certification alert for procurement."""
        qco = self._qco_reg.get_qco_for_standard(std.is_code)
        if not qco.is_mandatory and not std.mandatory_qco.is_mandatory:
            return "Voluntary Standard: BIS certification is recommended but not legally mandatory under QCO."

        effective_qco = qco if qco.is_mandatory else std.mandatory_qco
        scheme = effective_qco.scheme

        if scheme == CertificationScheme.ISI_MARK:
            return (
                f"MANDATORY ISI MARK (Scheme I): Regulated under {effective_qco.order_number} "
                f"by {effective_qco.issuing_ministry}. All bidders must possess a valid BIS CML license."
            )
        if scheme == CertificationScheme.CRS:
            return (
                f"MANDATORY CRS REGISTRATION: Compulsory under {effective_qco.order_number} "
                f"by {effective_qco.issuing_ministry}. Products must bear valid R-number registration."
            )
        if scheme == CertificationScheme.BEE_STAR:
            return (
                f"MANDATORY BEE STAR RATING: Governed by BEE Energy Efficiency regulations. "
                f"Minimum Star rating certification is mandatory."
            )
        return f"MANDATORY REGULATION: {effective_qco.clause_requirement}"
