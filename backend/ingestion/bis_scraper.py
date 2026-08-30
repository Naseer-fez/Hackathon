"""Web scraper and client for Bureau of Indian Standards (BIS) online data."""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup
from backend.config.settings import app_settings
from backend.models.standard_model import IndianStandard, StandardStatus


class BisScraper:
    """Asynchronous client for fetching metadata from BIS services."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or app_settings.bis_scraper.base_url
        self._timeout = app_settings.bis_scraper.request_timeout_sec
        self._headers = {"User-Agent": app_settings.bis_scraper.user_agent}

    async def fetch_standard_html(self, is_number: str) -> str:
        """Fetch raw HTML for standard detail page from BIS portal."""
        params = {"is_no": is_number.replace("IS ", "").strip()}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                res = await client.get(
                    self._base_url, params=params, headers=self._headers
                )
                res.raise_for_status()
                return res.text
        except (httpx.HTTPError, httpx.TimeoutException, OSError):
            return ""

    def parse_standard_details(
        self, html_content: str, is_code: str
    ) -> IndianStandard | None:
        """Parse BIS HTML content into structured IndianStandard model."""
        if not html_content:
            return None
        soup = BeautifulSoup(html_content, "html.parser")
        title_el = soup.find("h4") or soup.find("title")
        title = title_el.get_text(strip=True) if title_el else f"Standard {is_code}"
        scope_el = soup.find("div", class_="scope-text") or soup.find("p")
        scope = (
            scope_el.get_text(strip=True)
            if scope_el
            else "Standard specification."
        )

        return IndianStandard(
            is_code=is_code.strip().upper(),
            title=title,
            division="ETD",
            status=StandardStatus.ACTIVE,
            year=2020,
            scope=scope,
            category_keywords=[is_code.lower()],
        )

    async def query_live_standard(self, is_code: str) -> IndianStandard | None:
        """Fetch and parse Indian Standard live from BIS portal."""
        html = await self.fetch_standard_html(is_code)
        return self.parse_standard_details(html, is_code)
