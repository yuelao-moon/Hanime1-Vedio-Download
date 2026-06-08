from __future__ import annotations

import httpx
import pytest

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
