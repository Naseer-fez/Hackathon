"""LLM-based semantic specification extractor."""
from __future__ import annotations

import json
from backend.engine.llm_service import get_llm_service
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.standard_model import StandardStatus
from backend.models.tender_model import ComplianceIssue, ExtractedLineItem


class LlmSpecExtractor:
    """Extracts specification items and audits cited standards using an LLM."""

    def __init__(self, loader: StandardsLoader | None = None) -> None:
        self._loader = loader or StandardsLoader()
        self._llm_service = get_llm_service()
        self._llm_findings = []

    async def extract_items(self, text: str) -> list[ExtractedLineItem]:
        system_prompt = (
            "You are a procurement compliance analyst. Before generating ANY compliance finding, first build an internal structured mapping:\n"
            "Item Number → Product Description → Quantity/Unit → Referenced Standard → BIS/Conformity Requirement → Relevant Clause\n\n"
            "You MUST follow these rules strictly:\n"
            "RULE 1 — NEVER FLAG A PRESENT STANDARD AS MISSING. If an item explicitly contains an IS/Indian Standard reference, do NOT report 'Missing Standard Reference'.\n"
            "RULE 2 — DISTINGUISH EXPLICIT, GENERIC, AND ABSENT REQUIREMENTS. Classify the source requirement as EXPLICIT_STANDARD, GENERIC_BIS_REQUIREMENT, or NO_STANDARD_OR_BIS_REQUIREMENT. Do NOT convert a generic BIS requirement into an absent one.\n"
            "RULE 3 — VALIDATE ITEM NUMBER BEFORE REPORTING. Never infer additional items not present in the source.\n"
            "RULE 4 — MAINTAIN ITEM-TO-STANDARD ASSOCIATION. Each standard must remain attached to the row/item from which it was extracted.\n"
            "RULE 5 — SEPARATE EXTRACTION FROM COMPLIANCE ANALYSIS. Map items first, then classify, then analyze.\n"
            "RULE 6 — OUTDATED STANDARD FINDINGS MUST USE THE CORRECT ITEM. Never mix standards between items.\n"
            "RULE 7 — DO NOT MAKE UNSUPPORTED CURRENT-STANDARD CLAIMS. Say 'Standard currency requires verification' if unsure.\n"
            "RULE 8 — DO NOT INVENT QCO REQUIREMENTS. Do not automatically add a QCO clause unless supported by the source.\n"
            "RULE 9 — EVERY FINDING MUST BE TRACEABLE. Ensure the finding is supported by an exact clause/evidence.\n"
            "RULE 10 — PREFER 'VERIFICATION REQUIRED' OVER A FALSE POSITIVE.\n\n"
            "The priority order is: SOURCE ACCURACY > ITEM/STANDARD MAPPING > REQUIREMENT CLASSIFICATION > COMPLIANCE ANALYSIS > RECOMMENDATION.\n\n"
            "Strictly output a JSON object with two keys:\n"
            "- 'items': array of objects with keys: 'item_id' (integer), 'product_title' (string), 'spec_summary' (string), 'cited_standards' (list of strings representing IS codes).\n"
            "- 'findings': array of objects with EXACTLY these keys:\n"
            "  'item_no' (string or integer),\n"
            "  'product' (string),\n"
            "  'standard_cited' (string),\n"
            "  'requirement_type' (string: 'explicit_standard' | 'generic_bis_requirement' | 'absent'),\n"
            "  'finding_type' (string),\n"
            "  'issue' (string),\n"
            "  'evidence' (string),\n"
            "  'recommended_action' (string),\n"
            "  'confidence' (string: 'high' | 'medium' | 'low').\n"
            "Output only valid JSON."
        )

        prompt = f"Tender document text:\n{text}\n\nExecute the flow and output the JSON object."

        response_text = await self._llm_service._provider.generate_text(prompt, system_prompt)

        try:
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            extracted_data = json.loads(clean_text.strip())
        except json.JSONDecodeError:
            extracted_data = {"items": [], "findings": []}

        if isinstance(extracted_data, list):
            items_data = extracted_data
            self._llm_findings = []
        elif isinstance(extracted_data, dict):
            items_data = extracted_data.get("items", [])
            self._llm_findings = extracted_data.get("findings", [])
        else:
            items_data = []
            self._llm_findings = []

        items: list[ExtractedLineItem] = []
        for idx, item_data in enumerate(items_data, start=1):
            product_title = item_data.get("product_title", f"Procurement Item {idx}")
            spec_summary = item_data.get("spec_summary", "")
            cited = item_data.get("cited_standards", [])

            formatted_cited: list[str] = []
            for code in cited:
                if not str(code).upper().startswith("IS "):
                    formatted_cited.append(f"IS {code}")
                else:
                    formatted_cited.append(str(code).upper())

            outdated: list[str] = []
            for code in formatted_cited:
                std = self._loader.get_by_code(code)
                if std and std.status == StandardStatus.SUPERSEDED:
                    outdated.append(f"{code} (Superseded by {std.superseded_by})")

            # Fallback item_id from data or use idx
            item_id = item_data.get("item_id", idx)

            items.append(
                ExtractedLineItem(
                    item_id=item_id,
                    product_title=product_title,
                    spec_summary=spec_summary,
                    cited_standards=formatted_cited,
                    outdated_citations=outdated,
                )
            )

        return items

    def identify_compliance_issues(
        self, items: list[ExtractedLineItem]
    ) -> list[ComplianceIssue]:
        """Detect compliance risks utilizing LLM findings and internal audits."""
        issues: list[ComplianceIssue] = []

        # Add LLM generated findings
        for finding in self._llm_findings:
            finding_type = finding.get("finding_type", "Unknown")
            requirement_type = finding.get("requirement_type", "")
            severity = "MEDIUM"
            if requirement_type == "absent" or finding_type in ["Missing Explicit IS Number", "No BIS Requirement Identified", "Standard Currency Verification Required", "Missing Standard Reference"]:
                severity = "HIGH"
            elif requirement_type == "explicit_standard" or finding_type == "Standard Explicitly Cited":
                severity = "LOW"

            item_no = finding.get("item_no", "Unknown")
            product = finding.get("product", "")
            issue_text = finding.get("issue", "")
            evidence = finding.get("evidence", "")
            std_cited = finding.get("standard_cited", "")

            issues.append(
                ComplianceIssue(
                    severity=severity,
                    category=finding_type,
                    issue_text=f"Item #{item_no} ({product}): {issue_text} (Standard Cited: {std_cited}) (Evidence: {evidence})",
                    corrective_action=finding.get("recommended_action", ""),
                )
            )

        # Add authoritative outdated checks from the loader
        for item in items:
            if item.outdated_citations:
                for out in item.outdated_citations:
                    issues.append(
                        ComplianceIssue(
                            severity="HIGH",
                            category="Outdated Standard",
                            issue_text=f"Item #{item.item_id} '{item.product_title}' cites {out}.",
                            corrective_action="Update tender reference to latest active reaffirmed standard.",
                        )
                    )

        return issues
