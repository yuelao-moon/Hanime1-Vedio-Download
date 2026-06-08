from __future__ import annotations

import json

import httpx
import pytest

from python_backend.app.account import AccountSession, HanimeAccountClient
from python_backend.app.local_db import LocalStore


def test_account_session_merges_login_and_cloudflare_cookies(tmp_path):
    session = AccountSession(tmp_path)
    session.save_login_cookies([
        "hanime1_session=abc; Path=/; HttpOnly",
        "remember_web_123=def; Path=/; HttpOnly",
    ])

    merged = session.cookies_for_request([
        {"name": "cf_clearance", "value": "cf-token", "domain": ".hanime1.me"},
        {"name": "hanime1_session", "value": "old", "domain": ".hanime1.me"},
    ])

    assert merged["cf_clearance"] == "cf-token"
    assert merged["hanime1_session"] == "abc"
    assert merged["remember_web_123"] == "def"


def test_local_store_preserves_download_history_when_clearing_page_cache(tmp_path):
    store = LocalStore(tmp_path)
    store.set_page_cache("browse:home", {"title": "cached"}, scroll_y=42)
    store.save_download_history([{"id": "task-1", "title": "downloaded"}])

    assert store.get_page_cache("browse:home")["data"]["title"] == "cached"

    store.clear_page_cache()

    assert store.get_page_cache("browse:home") is None
    assert store.load_download_history() == [{"id": "task-1", "title": "downloaded"}]


@pytest.mark.asyncio
async def test_login_posts_token_and_persists_login_cookies(tmp_path):
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET" and request.url.path == "/login" and len(requests) == 1:
            return httpx.Response(200, text='<input name="_token" value="csrf-123">')
        if request.method == "POST" and request.url.path == "/login":
            assert b"_token=csrf-123" in request.content
            assert b"email=user%40example.com" in request.content
            return httpx.Response(
                302,
                headers=[
                    ("set-cookie", "hanime1_session=session-123; Path=/; HttpOnly"),
                    ("set-cookie", "remember_web_abc=remember-123; Path=/; HttpOnly"),
                ],
            )
        if request.method == "GET" and request.url.path == "/login":
            return httpx.Response(404, text="not found")
        return httpx.Response(500, text="unexpected")

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://hanime1.me",
        follow_redirects=False,
    )
    session = AccountSession(tmp_path)
    account = HanimeAccountClient(session, client=client)

    result = await account.login("user@example.com", "secret")

    assert result["loggedIn"] is True
    assert session.cookies_for_request()["hanime1_session"] == "session-123"
    assert session.cookies_for_request()["remember_web_abc"] == "remember-123"
