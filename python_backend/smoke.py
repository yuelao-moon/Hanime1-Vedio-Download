from __future__ import annotations

import json
import tempfile

from fastapi.testclient import TestClient

from app.main import create_app


class SmokeScraper:
    async def parse(self, url: str):
        return {
            "title": "Smoke Video",
            "videoUrl": "https://example.com/video.mp4",
            "thumbnail": "",
            "videoId": "smoke",
            "playlist": [],
            "relatedVideos": [],
        }

    async def browse(self, category: str, page: int):
        return {
            "videos": [{"title": category, "url": "https://hanime1.me/watch?v=smoke", "thumbnail": ""}],
            "currentPage": page,
            "totalPages": 1,
        }

    async def search(self, **kwargs):
        return {"videos": [], "currentPage": kwargs["page"], "totalPages": 1}

    async def comments(self, video_id: str):
        return [{"commentId": "smoke-comment", "content": "Smoke comment"}]

    async def replies(self, comment_id: str):
        return [{"commentId": "smoke-reply", "content": "Smoke reply"}]

    async def fetch_bytes(self, url: str, referer: str = ""):
        return b"smoke-image", "image/jpeg"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="hanime-python-smoke-") as tmp:
        with TestClient(create_app(app_home=tmp, scraper=SmokeScraper())) as client:
            checks = [
                ("GET", "/", None, 200),
                ("GET", "/api/settings", None, 200),
                ("GET", "/api/browsers", None, 200),
                ("GET", "/api/search/options", None, 200),
                ("GET", "/api/browse?category=Smoke&page=1", None, 200),
                ("POST", "/api/parse", {"url": "https://hanime1.me/watch?v=smoke"}, 200),
                ("GET", "/api/comments?videoId=smoke", None, 200),
                ("GET", "/api/replies?commentId=smoke-comment", None, 200),
                ("GET", "/api/proxy/history-cover?url=https%3A%2F%2Fhanime1.me%2Fwatch%3Fv%3Dsmoke&thumbnail=https%3A%2F%2Fexample.com%2Fcover.jpg", None, 200),
                ("GET", "/api/downloads", None, 200),
            ]
            for method, path, payload, expected in checks:
                response = client.request(method, path, json=payload)
                print(method, path, response.status_code)
                if response.status_code != expected:
                    raise SystemExit(response.text)

            response = client.post(
                "/api/downloads",
                json={"items": [{"title": "Smoke", "pageUrl": "", "downloadUrl": "https://example.com/video.mp4", "thumbnail": ""}]},
            )
            print("POST /api/downloads", response.status_code)
            if response.status_code != 200:
                raise SystemExit(response.text)

            snapshot = response.json()
            print(json.dumps({"queued": len(snapshot["queuedTasks"]), "history": len(snapshot["historyTasks"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
