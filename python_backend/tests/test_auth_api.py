from __future__ import annotations

import httpx
import pytest

from python_backend.app.main import create_app


class FakeAccountClient:
    def __init__(self):
        self.logged_in = False
        self.closed = False

    async def login(self, email: str, password: str) -> dict:
        self.logged_in = True
        return {"loggedIn": True, "email": email}

    async def me(self) -> dict:
        return {"loggedIn": self.logged_in, "username": "Tester" if self.logged_in else "", "avatarUrl": ""}

    async def logout(self) -> dict:
        self.logged_in = False
        return {"loggedIn": False}


@pytest.mark.asyncio
async def test_auth_routes_login_me_and_logout(tmp_path):
    account_client = FakeAccountClient()
    app = create_app(tmp_path, scraper=object(), account_client=account_client)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/auth/login", json={"email": "user@example.com", "password": "secret"})
        assert login.status_code == 200
        assert login.json()["loggedIn"] is True

        me = await client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["username"] == "Tester"

        logout = await client.post("/api/auth/logout")
        assert logout.status_code == 200
        assert logout.json()["loggedIn"] is False
