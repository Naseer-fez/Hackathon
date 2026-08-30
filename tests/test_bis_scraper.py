"""Unit tests for BIS scraper module."""
from __future__ import annotations

import pytest
from backend.ingestion.bis_scraper import BisScraper


def test_bis_scraper_parse_html() -> None:
    """Test parsing BIS portal HTML output."""
    scraper = BisScraper()
    dummy_html = (
        "<html><head><title>IS 456 Details</title></head>"
        "<body><h4>IS 456: Plain Concrete</h4>"
        "<div class='scope-text'>Covers structural concrete design.</div></body></html>"
    )
    res = scraper.parse_standard_details(dummy_html, "IS 456")
    assert res is not None
    assert res.is_code == "IS 456"
    assert "IS 456: Plain Concrete" in res.title


@pytest.mark.asyncio
async def test_bis_scraper_empty_response() -> None:
    """Test scraper handling empty response gracefully."""
    scraper = BisScraper(base_url="http://invalid-non-existent-url.local")
    html = await scraper.fetch_standard_html("99999")
    assert html == ""
