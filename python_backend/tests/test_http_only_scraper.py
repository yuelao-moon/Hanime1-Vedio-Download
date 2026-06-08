from __future__ import annotations

import httpx
import pytest

from python_backend.app.scraper import HanimeScraper, SessionBlockedError


@pytest.mark.asyncio
async def test_fetch_html_raises_on_http_block_without_browser_fallback(tmp_path):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="<html>blocked</html>")

    scraper = HanimeScraper(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        home=tmp_path,
    )

    assert not hasattr(scraper, "fetch_with_browser")
    assert not hasattr(scraper, "fetch_with_play" + "wright")

    with pytest.raises(SessionBlockedError):
        await scraper.fetch_html("https://hanime1.me/watch?v=1")
