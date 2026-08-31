"""Unit tests for llm specification extractor."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.parsers.llm_spec_extractor import LlmSpecExtractor
from backend.models.tender_model import ExtractedLineItem
from backend.models.standard_model import StandardStatus

@pytest.mark.asyncio
async def test_llm_spec_extractor_extract_items() -> None:
    """Test extracting cited IS codes using LLM."""
    with patch("backend.parsers.llm_spec_extractor.get_llm_service") as mock_get_llm:
        mock_service = MagicMock()
        mock_provider = MagicMock()
        mock_service._provider = mock_provider
        
        # Mock LLM returning valid JSON
        mock_provider.generate_text = AsyncMock(return_value='''```json
{
  "items": [
    {
      "item_id": 1,
      "product_title": "Supply of TMT Steel bars",
      "spec_summary": "Supply of TMT Steel bars according to IS 1786:1985 for building foundation.",
      "cited_standards": ["IS 1786:1985"]
    },
    {
      "item_id": 2,
      "product_title": "Supply of LED street lighting fixtures",
      "spec_summary": "Supply of LED street lighting fixtures 120W without specification.",
      "cited_standards": []
    }
  ],
  "findings": [
    {
      "item_no": 2,
      "product": "Supply of LED street lighting fixtures",
      "standard_cited": "",
      "requirement_type": "generic_bis_requirement",
      "finding_type": "No BIS Requirement Identified",
      "issue": "No specific BIS standard cited",
      "evidence": "120W without specification",
      "recommended_action": "Specify IS standard",
      "confidence": "high"
    }
  ]
}
```''')
        mock_get_llm.return_value = mock_service
        
        extractor = LlmSpecExtractor()
        
        sample_text = (
            "Item 1: Supply of TMT Steel bars according to IS 1786:1985 for building foundation.\n\n"
            "Item 2: Supply of LED street lighting fixtures 120W without specification."
        )

        items = await extractor.extract_items(sample_text)
        
        assert len(items) == 2
        assert items[0].product_title == "Supply of TMT Steel bars"
        assert "IS 1786:1985" in items[0].cited_standards
        
        assert len(items[1].cited_standards) == 0

        issues = extractor.identify_compliance_issues(items)
        assert len(issues) >= 1

