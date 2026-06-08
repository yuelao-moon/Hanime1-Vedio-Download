from __future__ import annotations

import asyncio
import time
from pathlib import Path

from .chrome_cookies import load_cookies, save_cookies


HANIME_ORIGIN = "https://hanime1.me"


class BrowserCookieCollector:
    def __init__(self, home: str | Path):
        self.home = Path(home)
        self._playwright = None
        self._context = None

    async def refresh(self) -> dict:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError("playwright 未安装，无法打开浏览器抓取 Cookie") from exc

        self._playwright = await async_playwright().start()
        try:
            profile_dir = self.home / ".cookie_browser_profile"
            profile_dir.mkdir(parents=True, exist_ok=True)
            last_error: Exception | None = None
            for kwargs in browser_launch_options():
                try:
                    self._context = await self._playwright.chromium.launch_persistent_context(
                        str(profile_dir),
                        headless=False,
                        args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
                        viewport=None,
                        **kwargs,
                    )
                    break
                except Exception as exc:
                    last_error = exc
            if self._context is None:
                raise RuntimeError(f"无法启动 Cookie 抓取浏览器: {last_error}") from last_error

            page = self._context.pages[0] if self._context.pages else await self._context.new_page()
            await page.goto(HANIME_ORIGIN + "/", wait_until="domcontentloaded", timeout=60000)
            await wait_for_cf_cookie(self._context, timeout_seconds=180)
            cookies = await self._context.cookies(HANIME_ORIGIN)
            user_agent = await page.evaluate("navigator.userAgent")
            save_cookies(cookies, self.home, user_agent=user_agent)
            cf_count = sum(1 for cookie in cookies if cookie.get("name") == "cf_clearance")
            return {"ok": True, "cookieCount": len(cookies), "hasCfClearance": cf_count > 0, "cfClearanceCount": cf_count}
        finally:
            await self.close()

    async def close(self) -> None:
        if self._context:
            try:
                await self._context.close()
            finally:
                self._context = None
        if self._playwright:
            try:
                await self._playwright.stop()
            finally:
                self._playwright = None


class CookieRefreshManager:
    def __init__(self, home: str | Path, scraper, collector: BrowserCookieCollector | None = None):
        self.home = Path(home)
        self.scraper = scraper
        self.collector = collector or BrowserCookieCollector(self.home)
        self._lock = asyncio.Lock()

    async def ensure_valid(self) -> dict:
        async with self._lock:
            if await self.scraper.validate_cookie_session():
                return {"valid": True, "refreshed": False}
            await self.collector.refresh()
            reload_session = getattr(self.scraper, "reload_cookie_session", None)
            if reload_session:
                reload_session()
            valid = await self.scraper.validate_cookie_session()
            return {"valid": valid, "refreshed": True}

    async def refresh(self) -> dict:
        async with self._lock:
            result = await self.collector.refresh()
            reload_session = getattr(self.scraper, "reload_cookie_session", None)
            if reload_session:
                reload_session()
            result["valid"] = await self.scraper.validate_cookie_session()
            return result

    def status(self) -> dict:
        cookies = load_cookies(self.home)
        return {
            "cookieCount": len(cookies),
            "hasCfClearance": any(cookie.get("name") == "cf_clearance" for cookie in cookies),
        }

    async def close(self) -> None:
        await self.collector.close()


def browser_launch_options() -> list[dict]:
    return [
        {"channel": "msedge"},
        {"channel": "chrome"},
        {},
    ]


async def wait_for_cf_cookie(context, timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        cookies = await context.cookies(HANIME_ORIGIN)
        if any(cookie.get("name") == "cf_clearance" for cookie in cookies):
            return
        await asyncio.sleep(1)
    raise RuntimeError("未能在限定时间内抓取到 cf_clearance Cookie")
