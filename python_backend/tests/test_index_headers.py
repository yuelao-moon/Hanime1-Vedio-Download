from __future__ import annotations

import httpx
import pytest

from python_backend.app.main import create_app


@pytest.mark.asyncio
async def test_index_sends_no_referrer_policy(tmp_path):
    app = create_app(tmp_path, scraper=object(), account_client=object())
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert response.headers["referrer-policy"] == "no-referrer"
