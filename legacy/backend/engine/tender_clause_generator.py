"""Generates formal tender specification clauses with exact IS citations."""
from __future__ import annotations

from backend.models.standard_model import IndianStandard


class TenderClauseGenerator:
    """Creates GeM/CPPP compliant technical specification clauses."""

    def generate_clause(self, std: IndianStandard) -> str:
        """Construct comprehensive procurement tender clause text."""
        year_str = f":{std.year}"
        if std.reaffirmation_year:
            year_str += f" (Reaffirmed {std.reaffirmation_year})"

        amd_text = (
            f"including all amendments up to {std.amendments[-1]}"
            if std.amendments
            else "incorporating latest gazette amendments"
        )

        test_lines = ", ".join(std.test_methods) if std.test_methods else "prescribed standard test methods"
        params_lines = "; ".join(std.key_parameters) if std.key_parameters else "as per standard specifications"

        lines = [
            f"1. TECHNICAL COMPLIANCE: The supplied product/equipment must strictly conform to {std.is_code}{year_str} - '{std.title}', {amd_text}.",
            f"2. KEY SPECIFICATIONS: The item shall satisfy all performance parameters including: {params_lines}.",
            f"3. TESTING & QUALITY ASSURANCE: Batch testing and sample verification must be performed according to {test_lines}.",
        ]

        if std.mandatory_qco.is_mandatory:
            lines.append(
                f"4. STATUTORY MANDATE: Product must bear mandatory {std.mandatory_qco.scheme.value} under {std.mandatory_qco.order_number}. "
                "Bidders must attach valid BIS license copy with technical bid."
            )
        else:
            lines.append(
                "4. INSPECTION: Manufacturer Test Certificate (MTC) and Third-Party NABL accredited lab test report must accompany each consignment."
            )

        return "\n".join(lines)
