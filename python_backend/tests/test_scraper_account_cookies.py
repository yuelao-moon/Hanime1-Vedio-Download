from __future__ import annotations

import httpx
import pytest

from python_backend.app.account import AccountSession
from python_backend.app.chrome_cookies import save_cookies
from python_backend.app.scraper import HanimeScraper


@pytest.mark.asyncio
async def test_fetch_html_sends_saved_login_cookie_without_cloudflare_cookie(tmp_path):
    seen_cookie = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_cookie
        seen_cookie = request.headers.get("cookie", "")
        return httpx.Response(200, text="<html>hanime1.me</html>")

    account = AccountSession(tmp_path)
    account.save_login_cookies(["hanime1_session=session-123; Path=/"])
    scraper = HanimeScraper(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        home=tmp_path,
        account_session=account,
    )

    html = await scraper.fetch_html("https://hanime1.me/watch?v=1")

    assert "hanime1.me" in html
    assert "hanime1_session=session-123" in seen_cookie


@pytest.mark.asyncio
async def test_fetch_html_sends_saved_cloudflare_cookie(tmp_path):
    seen_cookie = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_cookie
        seen_cookie = request.headers.get("cookie", "")
        return httpx.Response(200, text="<html>hanime1.me</html>")

    save_cookies([
        {"name": "cf_clearance", "value": "cf-123", "domain": ".hanime1.me", "path": "/", "expires": -1}
    ], tmp_path, user_agent="Mozilla/5.0 Test")
    scraper = HanimeScraper(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        home=tmp_path,
    )

    html = await scraper.fetch_html("https://hanime1.me/watch?v=1")

    assert "hanime1.me" in html
    assert "cf_clearance=cf-123" in seen_cookie


@pytest.mark.asyncio
async def test_fetch_json_sends_saved_login_cookie(tmp_path):
    seen_cookie = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_cookie
        seen_cookie = request.headers.get("cookie", "")
        return httpx.Response(200, json={"ok": True})

    account = AccountSession(tmp_path)
    account.save_login_cookies(["hanime1_session=session-123; Path=/"])
    scraper = HanimeScraper(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        home=tmp_path,
        account_session=account,
    )

    data = await scraper.fetch_json("https://hanime1.me/loadComment?id=1")

    assert data == {"ok": True}
    assert "hanime1_session=session-123" in seen_cookie


@pytest.mark.asyncio
async def test_post_form_sends_saved_login_cookie_and_csrf(tmp_path):
    seen_cookie = ""
    seen_token = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_cookie, seen_token
        seen_cookie = request.headers.get("cookie", "")
        seen_token = request.headers.get("x-csrf-token", "")
        return httpx.Response(200, json={"success": True})

    account = AccountSession(tmp_path)
    account.save_login_cookies(["hanime1_session=session-123; Path=/"])
    scraper = HanimeScraper(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        home=tmp_path,
        account_session=account,
    )

    data = await scraper.post_form("https://hanime1.me/like", {"_token": "csrf-123"})

    assert data == {"success": True}
    assert "hanime1_session=session-123" in seen_cookie
    assert seen_token == "csrf-123"
