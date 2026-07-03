from __future__ import annotations

import httpx
import pytest

from python_backend.app.main import create_app
from python_backend.app.scraper import HanimeScraper, is_trusted_media_host, parse_media_url


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "http://127.0.0.1:58080/private",
    "http://[::1]/private",
    "http://user:password@example.com/video.mp4",
])
def test_media_proxy_rejects_non_public_or_credentialed_urls(url):
    with pytest.raises(ValueError):
        parse_media_url(url)


def test_known_video_cdn_is_the_only_private_range_exception():
    assert is_trusted_media_host("vdownload.hembed.com")
    assert not is_trusted_media_host("hembed.com.example.test")


class RejectingScraper:
    async def stream_bytes(self, *_args):
        raise ValueError("视频代理不允许访问本地或私有网络地址")


@pytest.mark.asyncio
async def test_proxy_route_returns_bad_request_for_rejected_target(tmp_path):
    app = create_app(tmp_path, scraper=RejectingScraper(), account_client=object())
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/proxy/video", params={"url": "http://127.0.0.1:58080"})

    assert response.status_code == 400
    assert "私有网络" in response.json()["detail"]


@pytest.mark.asyncio
async def test_media_proxy_uses_cookie_free_client(tmp_path, monkeypatch):
    seen_headers = {}

    async def handler(request: httpx.Request):
        seen_headers.update(request.headers)
        return httpx.Response(200, content=b"video", headers={"content-type": "video/mp4"})

    app_client = httpx.AsyncClient()
    app_client.cookies.set("hanime1_session", "secret")
    media_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    scraper = HanimeScraper(client=app_client, media_client=media_client, home=tmp_path)

    async def allow_for_test(_url: str) -> None:
        pass

    monkeypatch.setattr("python_backend.app.scraper.validate_public_media_url", allow_for_test)
    try:
        body, status, content_type, _headers = await scraper.stream_bytes("https://media.example/video.mp4")
        received = b"".join([chunk async for chunk in body])
    finally:
        await app_client.aclose()
        await media_client.aclose()

    assert status == 200
    assert content_type == "video/mp4"
    assert received == b"video"
    assert "cookie" not in seen_headers
