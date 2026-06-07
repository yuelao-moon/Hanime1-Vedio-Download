from __future__ import annotations

import httpx
import pytest

from python_backend.app.main import create_app


@pytest.mark.asyncio
async def test_cache_clear_routes_do_not_clear_download_history(tmp_path):
    app = create_app(tmp_path, scraper=object(), account_client=object())
    store = app.state.local_store
    store.set_page_cache("browse:home", {"ok": True})
    store.save_download_history([{"id": "download-1"}])

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        page = await client.post("/api/settings/clear-page-cache")
        store.set_page_cache("browse:home", {"ok": True})
        local = await client.post("/api/settings/clear-cache")

    assert page.status_code == 200
    assert local.status_code == 200
    assert store.get_page_cache("browse:home") is None
    assert store.load_download_history() == [{"id": "download-1"}]
