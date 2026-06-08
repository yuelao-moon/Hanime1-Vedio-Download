from __future__ import annotations

import pytest

from python_backend.app.cookie_refresh import CookieRefreshManager
from python_backend.app.cookie_refresh import BrowserCookieCollector


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


class TimeoutPage:
    async def goto(self, *args, **kwargs):
        raise TimeoutError("challenge still running")

    async def evaluate(self, script: str):
        return "Mozilla/5.0 Test"


class DelayedCookieContext:
    def __init__(self):
        self.pages = [TimeoutPage()]
        self.cookie_calls = 0
        self.closed = False

    async def cookies(self, origin: str):
        self.cookie_calls += 1
        if self.cookie_calls >= 2:
            return [{"name": "cf_clearance", "value": "ok", "domain": ".hanime1.me", "path": "/"}]
        return []

    async def close(self):
        self.closed = True


class FakePlaywright:
    def __init__(self, context):
        self.chromium = self
        self.context = context
        self.stopped = False

    async def launch_persistent_context(self, *args, **kwargs):
        return self.context

    async def stop(self):
        self.stopped = True


@pytest.mark.asyncio
async def test_browser_cookie_collector_waits_after_cloudflare_navigation_timeout(tmp_path, monkeypatch):
    context = DelayedCookieContext()
    collector = BrowserCookieCollector(tmp_path)
    fake_playwright = FakePlaywright(context)

    class Starter:
        async def start(self):
            return fake_playwright

    def fake_async_playwright():
        return Starter()

    monkeypatch.setattr("playwright.async_api.async_playwright", fake_async_playwright)

    result = await collector.refresh()

    assert result["ok"] is True
    assert result["hasCfClearance"] is True
    assert context.cookie_calls >= 2
    assert context.closed is True
    assert fake_playwright.stopped is True


class AlwaysCookieContext:
    def __init__(self):
        self.pages = [TimeoutPage()]
        self.cookie_calls = 0
        self.closed = False

    async def cookies(self, origin: str):
        self.cookie_calls += 1
        return [{"name": "cf_clearance", "value": "ok", "domain": ".hanime1.me", "path": "/"}]

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_browser_cookie_collector_keeps_browser_open_until_http_validation_passes(tmp_path, monkeypatch):
    context = AlwaysCookieContext()
    collector = BrowserCookieCollector(tmp_path)
    fake_playwright = FakePlaywright(context)
    validate_calls = 0
    reload_calls = 0

    class Starter:
        async def start(self):
            return fake_playwright

    def fake_async_playwright():
        return Starter()

    async def validate():
        nonlocal validate_calls
        validate_calls += 1
        return validate_calls >= 3

    def reload_session():
        nonlocal reload_calls
        reload_calls += 1

    monkeypatch.setattr("playwright.async_api.async_playwright", fake_async_playwright)

    result = await collector.refresh(validate=validate, reload_session=reload_session, timeout_seconds=5)

    assert result["ok"] is True
    assert result["valid"] is True
    assert validate_calls == 3
    assert reload_calls >= 3
    assert context.closed is True
