from __future__ import annotations

import httpx
import pytest
from types import SimpleNamespace

from python_backend.app.account import AccountSession
from python_backend.app.chrome_cookies import save_cookies
from python_backend.app.main import create_app


class FakeCookieManager:
    def __init__(self):
        self.refreshed = False

    def status(self):
        return {"cookieCount": 1, "hasCfClearance": True}

    async def refresh(self):
        self.refreshed = True
        return {"ok": True, "valid": True}

    async def ensure_valid(self):
        return {"valid": True, "refreshed": False}


@pytest.mark.asyncio
async def test_cookie_status_and_refresh_routes(tmp_path):
    manager = FakeCookieManager()
    app = create_app(tmp_path, scraper=object(), account_client=object(), cookie_manager=manager)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        status = await client.get("/api/cookies/status")
        refresh = await client.post("/api/cookies/refresh")

    assert status.status_code == 200
    assert status.json()["hasCfClearance"] is True
    assert refresh.status_code == 200
    assert refresh.json()["valid"] is True
    assert manager.refreshed is True


@pytest.mark.asyncio
async def test_cookie_export_returns_terminal_header_with_merged_hanime_cookies(tmp_path):
    save_cookies([
        {"name": "cf_clearance", "value": "clearance-value", "domain": ".hanime1.me"},
        {"name": "_ga", "value": "analytics-value", "domain": ".hanime1.me"},
        {"name": "other", "value": "ignored", "domain": ".example.com"},
    ], tmp_path)
    account_session = AccountSession(tmp_path)
    account_session.save_login_cookies_dict({"hanime1_session": "session-value"})
    scraper = SimpleNamespace(account_session=account_session)
    app = create_app(tmp_path, scraper=scraper, account_client=object(), cookie_manager=FakeCookieManager())
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/cookies/export")

    assert response.status_code == 200
    assert response.json() == {
        "cookie": "cf_clearance=clearance-value; _ga=analytics-value; hanime1_session=session-value",
        "cookieCount": 3,
    }
