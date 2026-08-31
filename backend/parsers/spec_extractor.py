"""Extracts procurement line items, cited IS codes, and compliance gaps."""
from __future__ import annotations

import re
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.standard_model import StandardStatus
from backend.models.tender_model import ComplianceIssue, ExtractedLineItem


class SpecExtractor:
    """Extracts specification items and audits cited standards."""

    IS_REGEX = re.compile(r"\bIS\s*[:/-]?\s*(\d+(?:\s*\([^)]+\))?(?::\d{4})?)", re.IGNORECASE)

    def __init__(self, loader: StandardsLoader | None = None) -> None:
        self._loader = loader or StandardsLoader()

    def find_cited_standards(self, text: str) -> list[str]:
        """Find all mentioned IS codes in text."""
        matches = self.IS_REGEX.findall(text)
        return list(dict.fromkeys(f"IS {m.strip()}" for m in matches))

    def split_into_items(self, text: str) -> list[ExtractedLineItem]:
        """Segment raw text into procurement line items."""
        # Force double newline before ITEM or SL NO to ensure they are split properly
        text = re.sub(r'(?im)^((?:ITEM|SL\s*NO\.?|S\.NO\.?)\s*\d+[\s.-])', r'\n\n\1', text)
        
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
        if not paragraphs:
            paragraphs = [text.strip()] if text.strip() else []

        # If we found ITEM markers, try to filter out preamble/headers
        has_items = any(re.match(r'(?i)^(ITEM|SL\s*NO\.?|S\.NO\.?)\s*\d+', p) for p in paragraphs)

        items: list[ExtractedLineItem] = []
        for idx, para in enumerate(paragraphs, start=1):
            if has_items and not re.match(r'(?i)^(ITEM|SL\s*NO\.?|S\.NO\.?)\s*\d+', para):
                # Skip paragraphs that are just preamble if this document clearly uses ITEM markers
                continue
                
            cited = self.find_cited_standards(para)
            outdated: list[str] = []

            for code in cited:
                std = self._loader.get_by_code(code)
                if std and std.status == StandardStatus.SUPERSEDED:
                    outdated.append(f"{code} (Superseded by {std.superseded_by})")

            first_line = para.split("\n")[0][:80]
            title = first_line if len(first_line) > 5 else f"Procurement Item {idx}"

            items.append(
                ExtractedLineItem(
                    item_id=idx,
                    product_title=title,
                    spec_summary=para[:300],
                    cited_standards=cited,
                    outdated_citations=outdated,
                )
            )
        
        # Re-number item_id if we skipped preambles
        for i, item in enumerate(items, start=1):
            item.item_id = i

        return items

    def identify_compliance_issues(
        self, items: list[ExtractedLineItem]
    ) -> list[ComplianceIssue]:
        """Detect compliance risks such as missing or outdated standards."""
        issues: list[ComplianceIssue] = []
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
            if not item.cited_standards:
                issues.append(
                    ComplianceIssue(
                        severity="MEDIUM",
                        category="Missing Standard Reference",
                        issue_text=f"Item #{item.item_id} '{item.product_title}' has no explicit Indian Standard cited.",
                        corrective_action="Add recommended IS standard code and mandatory QCO clause.",
                    )
                )
        return issues
