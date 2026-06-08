from __future__ import annotations

import httpx
import pytest

from python_backend.app.main import create_app


@pytest.mark.asyncio
async def test_image_proxy_routes_are_not_registered(tmp_path):
    app = create_app(tmp_path, scraper=object(), account_client=object())
    route_paths = {getattr(route, "path", "") for route in app.routes}

    assert "/api/proxy/image" not in route_paths
    assert "/api/proxy/images/preload" not in route_paths
    assert "/api/proxy/history-cover" not in route_paths

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        image = await client.get("/api/proxy/image", params={"url": "https://img.test/a.jpg"})
        preload = await client.post("/api/proxy/images/preload", json={"urls": ["https://img.test/a.jpg"]})
        history = await client.get("/api/proxy/history-cover", params={"thumbnail": "https://img.test/a.jpg"})

    assert image.status_code != 200
    assert preload.status_code != 200
    assert history.status_code != 200


@pytest.mark.asyncio
async def test_clear_cache_removes_legacy_image_cache_directory(tmp_path):
    app = create_app(tmp_path, scraper=object(), account_client=object())
    img_cache = tmp_path / "img_cache" / "aa"
    img_cache.mkdir(parents=True)
    (img_cache / "legacy.bin").write_bytes(b"old")
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        clear = await client.post("/api/settings/clear-cache")

    assert clear.status_code == 200
    assert not (tmp_path / "img_cache").exists()
