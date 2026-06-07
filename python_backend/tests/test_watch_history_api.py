from __future__ import annotations

import httpx
import pytest

from python_backend.app.main import create_app


@pytest.mark.asyncio
async def test_watch_history_record_and_list(tmp_path):
    app = create_app(tmp_path, scraper=object(), account_client=object())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        recorded = await client.post("/api/watch-history/record", json={
            "videoId": "123",
            "title": "Watched",
            "pageUrl": "https://hanime1.me/watch?v=123",
            "thumbnail": "cover.jpg",
        })
        listed = await client.get("/api/watch-history")

    assert recorded.status_code == 200
    assert listed.status_code == 200
    assert listed.json()[0]["videoId"] == "123"
    assert listed.json()[0]["title"] == "Watched"
