"""Converter to hydrate typed IndianStandard instances from ChromaDB records."""
from __future__ import annotations

from typing import Any
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.standard_model import CertificationScheme, IndianStandard, MandatoryQCO, StandardStatus


def hydrate_standard_from_chroma(res: dict[str, Any], loader: StandardsLoader) -> IndianStandard:
    """Convert ChromaDB search result dictionary into validated IndianStandard model."""
    is_num = str(res.get("is_number") or res.get("standard_id", "")).split(":")[0].strip()
    existing = loader.get_by_code(is_num)
    if existing:
        return existing

    status_str = str(res.get("status", "Active"))
    status = StandardStatus.ACTIVE if "active" in status_str.lower() else StandardStatus.SUPERSEDED
    is_mand = bool(res.get("mandatory", False))
    scheme_str = str(res.get("bis_scheme", ""))
    scheme = (
        CertificationScheme.ISI_MARK if "Scheme-I" in scheme_str or "ISI" in scheme_str
        else (CertificationScheme.CRS if "CRS" in scheme_str or "Scheme-II" in scheme_str
        else (CertificationScheme.BEE_STAR if "BEE" in scheme_str else CertificationScheme.NONE))
    )
    title_raw = str(res.get("snippet", "")).split("\n")[0].replace("STANDARD:", "").strip()
    title = title_raw.split(" - ")[-1] if " - " in title_raw else (res.get("product_category") or is_num)
    year = int(res.get("year") or 2015)

    return IndianStandard(
        is_code=is_num,
        title=title,
        division=str(res.get("division_council") or "CED"),
        status=status,
        year=year,
        scope=str(res.get("snippet") or f"Standard specification for {title}"),
        key_parameters=[str(res.get("product_category") or "Technical Specification")],
        test_methods=[f"Standard Quality & Testing Conformance for {is_num}"],
        normative_references=[],
        mandatory_qco=MandatoryQCO(
            is_mandatory=is_mand,
            scheme=scheme,
            order_number=str(res.get("qco_order_title") or ""),
            issuing_ministry="DPIIT / Ministry of Commerce / BIS" if is_mand else "",
            clause_requirement=f"Valid BIS Certification required per {res.get('qco_order_title')}" if is_mand else "",
        ),
        category_keywords=[str(res.get("product_category") or ""), is_num],
        gem_categories=[str(res.get("product_category") or "")],
    )
