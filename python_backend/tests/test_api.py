from fastapi.testclient import TestClient

from app.main import create_app
from app.scraper import SessionBlockedError


class FakeScraper:
    async def parse(self, url: str):
        return {"title": "Parsed", "videoUrl": "https://cdn/video.mp4", "thumbnail": "", "videoId": "v"}

    async def browse(self, category: str, page: int):
        return {"videos": [{"title": category, "url": "u", "thumbnail": "t"}], "currentPage": page, "totalPages": 1}

    async def search(self, **kwargs):
        return {"videos": [], "currentPage": kwargs["page"], "totalPages": 1}

    async def comments(self, video_id: str):
        return [{"commentId": "c1", "content": "hello"}]

    async def replies(self, comment_id: str):
        return [{"commentId": "r1", "content": "reply"}]

    async def fetch_bytes(self, url: str, referer: str = ""):
        return b"image", "image/jpeg"

    async def stream_bytes(self, url: str, referer: str = "", range_header: str | None = None):
        async def body():
            yield b"chunk-1"
            yield b"chunk-2"

        return body(), 206, "video/mp4", {"content-range": "bytes 0-13/14", "accept-ranges": "bytes"}


def test_api_settings_and_parse(tmp_path):
    app = create_app(app_home=tmp_path, scraper=FakeScraper())
    client = TestClient(app)

    settings = client.get("/api/settings")
    assert settings.status_code == 200
    assert "downloadDirectory" in settings.json()

    parsed = client.post("/api/parse", json={"url": "https://hanime1.me/watch?v=v"})
    assert parsed.status_code == 200
    assert parsed.json()["title"] == "Parsed"


def test_api_browse_uses_scraper(tmp_path):
    app = create_app(app_home=tmp_path, scraper=FakeScraper())
    client = TestClient(app)

    response = client.get("/api/browse?category=裏番&page=2")

    assert response.status_code == 200
    assert response.json()["currentPage"] == 2


def test_api_returns_service_unavailable_when_session_is_blocked(tmp_path):
    class BlockedScraper(FakeScraper):
        async def browse(self, category: str, page: int):
            raise SessionBlockedError("HTTP 会话被 Cloudflare 拦截")

    app = create_app(app_home=tmp_path, scraper=BlockedScraper())
    client = TestClient(app)

    response = client.get("/api/browse?category=x&page=1")

    assert response.status_code == 503
    assert "Cloudflare" in response.text


def test_video_proxy_streams_upstream_response(tmp_path):
    app = create_app(app_home=tmp_path, scraper=FakeScraper())
    client = TestClient(app)

    response = client.get(
        "/api/proxy/video?url=https%3A%2F%2Fcdn%2Fvideo.mp4",
        headers={"Range": "bytes=0-13"},
    )

    assert response.status_code == 206
    assert response.content == b"chunk-1chunk-2"
    assert response.headers["content-range"] == "bytes 0-13/14"
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["cache-control"] == "public, max-age=300"


def test_image_proxy_is_browser_cacheable(tmp_path):
    app = create_app(app_home=tmp_path, scraper=FakeScraper())
    client = TestClient(app)

    response = client.get("/api/proxy/image?url=https%3A%2F%2Fcdn%2Fcover.jpg")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=86400"


def test_comment_and_reply_endpoints_use_scraper(tmp_path):
    app = create_app(app_home=tmp_path, scraper=FakeScraper())
    client = TestClient(app)

    comments = client.get("/api/comments?videoId=v")
    replies = client.get("/api/replies?commentId=c1")

    assert comments.status_code == 200
    assert comments.json()[0]["commentId"] == "c1"
    assert replies.status_code == 200
    assert replies.json()[0]["commentId"] == "r1"


def test_history_cover_proxy_is_browser_cacheable(tmp_path):
    app = create_app(app_home=tmp_path, scraper=FakeScraper())
    client = TestClient(app)

    response = client.get(
        "/api/proxy/history-cover?url=https%3A%2F%2Fpage.example%2Fwatch%3Fv%3D1&thumbnail=https%3A%2F%2Fcdn%2Fcover.jpg"
    )

    assert response.status_code == 200
    assert response.content == b"image"
    assert response.headers["cache-control"] == "public, max-age=86400"
