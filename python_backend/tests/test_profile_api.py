from __future__ import annotations

import httpx
import pytest

from python_backend.app.main import create_app


class FakeAccount:
    async def me(self):
        return {"loggedIn": True, "userId": "42", "username": "Tester", "avatarUrl": "avatar.jpg"}


class FakeProfileScraper:
    async def profile_section(self, section: str, user_id: str, page: int = 1):
        return {
            "section": section,
            "title": section,
            "items": [{"title": f"{section}-{page}", "url": "https://hanime1.me/watch?v=1"}],
            "currentPage": page,
            "totalPages": 2,
        }


@pytest.mark.asyncio
async def test_profile_summary_and_section_routes(tmp_path):
    app = create_app(tmp_path, scraper=FakeProfileScraper(), account_client=FakeAccount())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        summary = await client.get("/api/profile/summary")
        section = await client.get("/api/profile/section/likes?page=2")

    assert summary.status_code == 200
    body = summary.json()
    assert body["user"]["username"] == "Tester"
    assert [item["section"] for item in body["sections"]] == ["watchLater", "likes", "playlists", "subscriptions", "histories"]
    assert section.status_code == 200
    assert section.json()["items"][0]["title"] == "likes-2"
