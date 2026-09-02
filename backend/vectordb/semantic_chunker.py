"""Semantic chunking and rich metadata payload generator for Indian Standards."""
from __future__ import annotations

import json
from typing import Any
from backend.vectordb.taxonomy_enricher import TaxonomyEnricher


class SemanticChunker:
    """Generates structured semantic chunks with rich metadata for Vector DB indexing."""

    def __init__(self, enricher: TaxonomyEnricher | None = None) -> None:
        self._enricher = enricher or TaxonomyEnricher()

    def _extract_field(self, obj: Any, field_name: str, default: Any = None) -> Any:
        """Safely extract field from either Pydantic model or dict."""
        if hasattr(obj, field_name):
            val = getattr(obj, field_name)
            return val if val is not None else default
        if isinstance(obj, dict):
            return obj.get(field_name, default)
        return default

    def build_chunk(self, standard: Any, qco_data: Any = None) -> tuple[str, str, dict[str, Any]]:
        """Create a semantically complete document text, chunk ID, and metadata payload."""
        std_id = str(self._extract_field(standard, "standard_id", "") or self._extract_field(standard, "is_code", ""))
        is_num = str(self._extract_field(standard, "is_number", "") or self._extract_field(standard, "is_code", ""))
        if not std_id and is_num:
            std_id = is_num
        if not is_num and std_id:
            is_num = std_id
        year = int(self._extract_field(standard, "year", 2015) or 2015)
        title = str(self._extract_field(standard, "title", ""))
        scope = str(self._extract_field(standard, "scope", ""))
        sector = str(self._extract_field(standard, "sector", "General Engineering"))
        prod_cat = str(self._extract_field(standard, "product_category", "General"))
        div_council = str(self._extract_field(standard, "division_council", "CED"))
        committee = str(self._extract_field(standard, "technical_committee", "CED 2"))

        raw_status = self._extract_field(standard, "status", "Active")
        status_val = raw_status.value if hasattr(raw_status, "value") else str(raw_status)

        is_mandatory = bool(self._extract_field(standard, "certification_mandatory", False))
        has_qco = bool(qco_data is not None) or is_mandatory
        qco_title = getattr(qco_data, "order_title", "") if qco_data else ""
        scheme = str(self._extract_field(standard, "bis_scheme", "Scheme-I (ISI Mark Scheme)"))

        # Assemble structured semantic document text
        sections: list[str] = [
            f"STANDARD: {std_id} - {title}",
            f"IDENTIFIER: Base IS Number: {is_num} | Year: {year} | Status: {status_val}",
            f"COMMITTEE: {committee} | DIVISION: {div_council} | SECTOR: {sector} | CATEGORY: {prod_cat}",
        ]
        if scope:
            sections.append(f"SCOPE & APPLICABILITY:\n{scope}")

        materials = self._extract_field(standard, "materials_covered", []) or []
        if materials:
            sections.append(f"MATERIALS COVERED: {', '.join(materials)}")

        tech_reqs = self._extract_field(standard, "key_technical_requirements", {}) or {}
        if tech_reqs:
            sections.append(f"TECHNICAL REQUIREMENTS: {json.dumps(tech_reqs, ensure_ascii=False)}")

        testing = self._extract_field(standard, "testing_requirements", []) or []
        if testing:
            sections.append(f"MANDATED TESTING: {', '.join(testing)}")

        norm_refs = self._extract_field(standard, "normative_references", []) or []
        if norm_refs:
            sections.append(f"NORMATIVE REFERENCES: {', '.join(norm_refs)}")

        sections.append(f"REGULATORY STATUS: Mandatory QCO: {has_qco} | Scheme: {scheme} | Order: {qco_title or 'Voluntary'}")

        # Inject taxonomy and Indic domain terminology
        combined_text = " ".join(sections)
        tax_block = self._enricher.build_taxonomy_injection_block(is_num or std_id, combined_text)
        if tax_block:
            sections.append(tax_block)

        full_doc = "\n\n".join(sections)
        chunk_id = f"chunk_{std_id.replace(' ', '_').replace(':', '_')}_0"

        amendments = self._extract_field(standard, "amendments", []) or []
        metadata: dict[str, Any] = {
            "standard_id": std_id,
            "is_number": is_num,
            "year": year,
            "status": status_val,
            "mandatory": has_qco,
            "has_qco": has_qco,
            "qco_order_title": qco_title or "None",
            "bis_scheme": scheme,
            "division_council": div_council.split()[0] if div_council else "CED",
            "division_council_full": div_council,
            "technical_committee": committee,
            "sector": sector,
            "product_category": prod_cat,
            "amendment_count": len(amendments),
            "chunk_type": "master_profile",
            "chunk_index": 0,
        }
        return full_doc, chunk_id, metadata
