from __future__ import annotations

import pytest

from python_backend.app.cookie_refresh import CookieRefreshManager


class FakeScraper:
    def __init__(self, blocked_once: bool):
        self.blocked_once = blocked_once
        self.calls = 0
        self.closed = False

    async def validate_cookie_session(self) -> bool:
        self.calls += 1
        if self.blocked_once and self.calls == 1:
            return False
        return True


class FakeCollector:
    def __init__(self):
        self.calls = 0

    async def refresh(self) -> dict:
        self.calls += 1
        return {"ok": True, "cookieCount": 2, "hasCfClearance": True}

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_cookie_refresh_manager_skips_browser_when_cookie_valid(tmp_path):
    scraper = FakeScraper(blocked_once=False)
    collector = FakeCollector()
    manager = CookieRefreshManager(tmp_path, scraper=scraper, collector=collector)

    result = await manager.ensure_valid()

    assert result["valid"] is True
    assert result["refreshed"] is False
    assert collector.calls == 0


@pytest.mark.asyncio
async def test_cookie_refresh_manager_opens_browser_when_cookie_invalid(tmp_path):
    scraper = FakeScraper(blocked_once=True)
    collector = FakeCollector()
    manager = CookieRefreshManager(tmp_path, scraper=scraper, collector=collector)

    result = await manager.ensure_valid()

    assert result["valid"] is True
    assert result["refreshed"] is True
    assert collector.calls == 1
    assert scraper.calls == 2
