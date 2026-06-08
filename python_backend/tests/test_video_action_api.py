from __future__ import annotations

import httpx
import pytest

from python_backend.app.main import create_app


class FakeScraper:
    def __init__(self):
        self.posts = []
        self._html_cache = {}

    async def parse(self, url: str):
        return {
            "videoId": "123",
            "csrfToken": "csrf-from-parse",
            "currentUserId": "42",
            "myList": {"watchLaterCode": "WL-from-parse", "isWatchLater": False, "items": []},
        }

    async def post_form(self, url: str, data: dict, referer: str = "https://hanime1.me"):
        self.posts.append((url, data, referer))
        return {"ok": True}


@pytest.mark.asyncio
async def test_video_action_routes_post_expected_forms(tmp_path):
    scraper = FakeScraper()
    app = create_app(tmp_path, scraper=scraper, account_client=object())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        fav = await client.post("/api/video/favorite", json={
            "videoId": "123",
            "csrfToken": "csrf",
            "currentUserId": "42",
            "isFav": False,
        })
        watch_later = await client.post("/api/video/watch-later", json={
            "videoId": "123",
            "csrfToken": "csrf",
            "currentUserId": "42",
            "isChecked": True,
        })
        playlist = await client.post("/api/video/my-list", json={
            "videoId": "123",
            "csrfToken": "csrf",
            "listCode": "playlist-7",
            "isChecked": True,
        })
        subscribe = await client.post("/api/creator/subscribe", json={
            "csrfToken": "csrf",
            "userId": "42",
            "artistId": "99",
            "isSubscribed": False,
        })
        reply = await client.post("/api/replies/create", json={
            "commentId": "406416",
            "csrfToken": "csrf",
            "text": "回复内容",
        })
        comment = await client.post("/api/comments/create", json={
            "videoId": "123",
            "currentUserId": "42",
            "csrfToken": "comment-csrf",
            "text": "评论内容",
        })
        comment_like = await client.post("/api/comments/like", json={
            "foreignType": "comment",
            "foreignId": "406416",
            "csrfToken": "comment-csrf",
            "isPositive": "1",
            "likeUserId": "42",
            "likeStatus": "0",
            "likeCount": "13",
            "likeTotal": "13",
            "unlikeStatus": "0",
        })

    assert fav.status_code == 200
    assert watch_later.status_code == 200
    assert playlist.status_code == 200
    assert subscribe.status_code == 200
    assert reply.status_code == 200
    assert comment.status_code == 200
    assert comment_like.status_code == 200
    assert scraper.posts[0][0].endswith("/like")
    assert scraper.posts[0][1]["like-status"] == ""
    assert scraper.posts[1][0].endswith("/save")
    assert scraper.posts[1][1]["input_id"] == "WL"
    assert scraper.posts[1][1]["is_checked"] == "true"
    assert scraper.posts[2][1]["input_id"] == "playlist-7"
    assert scraper.posts[2][1]["is_checked"] == "true"
    assert scraper.posts[3][0].endswith("/subscribe")
    assert scraper.posts[3][1]["subscribe-status"] == ""
    assert scraper.posts[4][0].endswith("/replyComment")
    assert scraper.posts[4][1] == {
        "_token": "csrf",
        "reply-comment-id": "406416",
        "reply-comment-text": "回复内容",
    }
    assert scraper.posts[5][0].endswith("/createComment")
    assert scraper.posts[5][1] == {
        "_token": "comment-csrf",
        "comment-user-id": "42",
        "comment-type": "video",
        "comment-foreign-id": "123",
        "comment-count": "0",
        "comment-text": "评论内容",
    }
    assert scraper.posts[6][0].endswith("/commentLike")
    assert scraper.posts[6][1] == {
        "_token": "comment-csrf",
        "foreign_type": "comment",
        "foreign_id": "406416",
        "is_positive": "1",
        "comment-like-user-id": "42",
        "like-comment-status": "0",
        "comment-likes-count": "13",
        "comment-likes-sum": "13",
        "unlike-comment-status": "0",
    }


@pytest.mark.asyncio
async def test_watch_later_route_resolves_missing_token_from_page_url(tmp_path):
    scraper = FakeScraper()
    scraper._html_cache[("https://hanime1.me/watch?v=123", "https://hanime1.me/")] = (999999999, "<html>stale</html>")
    app = create_app(tmp_path, scraper=scraper, account_client=object())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/video/watch-later", json={
            "videoId": "123",
            "pageUrl": "https://hanime1.me/watch?v=123",
            "isChecked": True,
        })

    assert response.status_code == 200
    assert scraper.posts[0][1]["_token"] == "csrf-from-parse"
    assert scraper.posts[0][1]["input_id"] == "WL-from-parse"
    assert scraper.posts[0][1]["is_checked"] == "true"
    assert ("https://hanime1.me/watch?v=123", "https://hanime1.me/") not in scraper._html_cache
