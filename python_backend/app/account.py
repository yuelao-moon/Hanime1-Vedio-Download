from __future__ import annotations

import json
import re
import time
from http.cookies import SimpleCookie
from pathlib import Path

from selectolax.parser import HTMLParser

from .chrome_cookies import load_cookies, cookies_for_host, load_user_agent

try:
    from curl_cffi.requests import AsyncSession as CurlSession
except ImportError:
    CurlSession = None  # type: ignore[assignment,misc]


HANIME_ORIGIN = "https://hanime1.me"
_HANIME_HOST = "hanime1.me"
LOGIN_COOKIE_NAMES = ("hanime1_session", "remember_web", "XSRF-TOKEN")


# ── helpers ───────────────────────────────────────────────────────────────────

def _cf_cookies_dict(home: Path) -> dict[str, str]:
    """读取 cf_cookies.json 里 hanime1.me 的 CF clearance cookies。"""
    all_cookies = load_cookies(home)
    host_cookies = cookies_for_host(all_cookies, _HANIME_HOST)
    return {c["name"]: c["value"] for c in host_cookies if c.get("value")}


def _impersonate_from_home(home: Path) -> str:
    """根据保存的 User-Agent 决定 curl_cffi impersonate 版本。"""
    ua = load_user_agent(home) or ""
    match = re.search(r"(?:Chrome|Edg)/(\d+)", ua)
    major = int(match.group(1)) if match else 124
    if major >= 136:
        return "chrome136"
    if major >= 131:
        return "chrome131"
    if major >= 124:
        return "chrome124"
    if major >= 120:
        return "chrome120"
    return "chrome107"


# ── AccountSession ─────────────────────────────────────────────────────────────

class AccountSession:
    def __init__(self, home: str | Path):
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        self.path = self.home / "account_cookies.json"

    def load_login_cookies(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        cookies = payload.get("cookies")
        return cookies if isinstance(cookies, dict) else {}

    def save_login_cookies(self, set_cookie_headers: list[str]) -> None:
        cookies = self.load_login_cookies()
        for header in set_cookie_headers:
            parsed = SimpleCookie()
            parsed.load(header)
            for name, morsel in parsed.items():
                if any(name == cookie_name or name.startswith(f"{cookie_name}_") for cookie_name in LOGIN_COOKIE_NAMES):
                    cookies[name] = morsel.value
        self._write(cookies)

    def save_login_cookies_dict(self, new_cookies: dict[str, str]) -> None:
        cookies = self.load_login_cookies()
        cookies.update(new_cookies)
        self._write(cookies)

    def _write(self, cookies: dict[str, str]) -> None:
        self.path.write_text(
            json.dumps({"savedAt": time.time(), "cookies": cookies}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def cookies_for_request(self, base_cookies: list[dict] | None = None) -> dict[str, str]:
        merged: dict[str, str] = {}
        for cookie in base_cookies or []:
            name = cookie.get("name")
            value = cookie.get("value")
            if name and value:
                merged[name] = value
        merged.update(self.load_login_cookies())
        return merged

    def cookie_header(self, base_cookies: list[dict] | None = None) -> str:
        return "; ".join(
            f"{name}={value}"
            for name, value in self.cookies_for_request(base_cookies).items()
        )

    def is_logged_in(self) -> bool:
        return "hanime1_session" in self.load_login_cookies()


# ── HanimeAccountClient ────────────────────────────────────────────────────────

class HanimeAccountClient:
    """
    用 curl_cffi（Chrome TLS 指纹）+ CF clearance cookies 绕过 Cloudflare 保护，
    实现 hanime1.me 账号登录 / 状态查询。
    """

    def __init__(self, session: AccountSession, client=None):
        self.session = session
        self.client = client

    # ── internal ──────────────────────────────────────────────────────────────

    def _build_cf_cookies(self) -> dict[str, str]:
        return _cf_cookies_dict(self.session.home)

    def _impersonate(self) -> str:
        return _impersonate_from_home(self.session.home)

    # ── public API ────────────────────────────────────────────────────────────

    async def login(self, email: str, password: str) -> dict:
        if self.client is not None:
            return await self._login_with_client(email, password)

        if CurlSession is None:
            raise ValueError("curl_cffi 未安装，请先安装后再登录")

        cf_cookies = self._build_cf_cookies()
        ua = load_user_agent(self.session.home) or ""
        impersonate = "chrome124"

        async with CurlSession(impersonate=impersonate, timeout=30) as client:
            # 步骤 1：GET /login，带 CF cookies，让 curl_cffi 用 Chrome TLS 指纹
            login_page = await client.get(
                HANIME_ORIGIN + "/login",
                cookies=cf_cookies,
                headers={"User-Agent": ua, "Referer": HANIME_ORIGIN + "/"},
                allow_redirects=True,
            )
            if login_page.status_code != 200:
                raise ValueError(
                    f"无法访问登录页（HTTP {login_page.status_code}）"
                    "，请先在「设置」中刷新 Cloudflare Cookie 后再登录"
                )

            token = extract_csrf_token(login_page.text)

            # 步骤 2：POST 登录表单
            # 此时 client 内部 cookie jar 已包含 CF cookies（来自步骤 1 的响应）
            response = await client.post(
                HANIME_ORIGIN + "/login",
                data={"_token": token, "email": email, "password": password},
                cookies=cf_cookies,
                headers={
                    "User-Agent": ua,
                    "X-CSRF-TOKEN": token,
                    "Referer": HANIME_ORIGIN + "/login",
                    "Origin": HANIME_ORIGIN,
                },
                allow_redirects=False,
            )

            # 步骤 3：从 cookie jar 里取 hanime1_session
            session_val = client.cookies.get("hanime1_session")
            if not session_val:
                raise ValueError("账号或密码错误")

            login_cookies: dict[str, str] = {"hanime1_session": session_val}
            for name, value in dict(client.cookies).items():
                if name.startswith("remember_web"):
                    login_cookies[name] = value

            self.session.save_login_cookies_dict(login_cookies)
            return {"loggedIn": True}

    async def _login_with_client(self, email: str, password: str) -> dict:
        login_page = await self.client.get(HANIME_ORIGIN + "/login")
        if login_page.status_code != 200:
            raise ValueError(f"无法访问登录页（HTTP {login_page.status_code}）")
        token = extract_csrf_token(login_page.text)
        response = await self.client.post(
            HANIME_ORIGIN + "/login",
            data={"_token": token, "email": email, "password": password},
            headers={"X-CSRF-TOKEN": token, "Referer": HANIME_ORIGIN + "/login"},
        )
        set_cookies = response.headers.get_list("set-cookie") if hasattr(response.headers, "get_list") else []
        self.session.save_login_cookies(set_cookies)
        if not self.session.is_logged_in():
            raise ValueError("账号或密码错误")
        return {"loggedIn": True}

    async def me(self) -> dict:
        if not self.session.is_logged_in():
            return {"loggedIn": False, "username": "", "avatarUrl": "", "userId": ""}
        if CurlSession is None:
            return {"loggedIn": True, "username": "", "avatarUrl": "", "userId": ""}

        cf_cookies = self._build_cf_cookies()
        login_cookies = self.session.load_login_cookies()
        all_cookies = {**cf_cookies, **login_cookies}
        ua = load_user_agent(self.session.home) or ""
        impersonate = "chrome124"

        async with CurlSession(impersonate=impersonate, timeout=30) as client:
            response = await client.get(
                HANIME_ORIGIN + "/",
                cookies=all_cookies,
                headers={"User-Agent": ua, "Referer": HANIME_ORIGIN + "/"},
            )
            response.raise_for_status()
            return parse_home_user(response.text)

    async def logout(self) -> dict:
        self.session.clear()
        return {"loggedIn": False, "username": "", "avatarUrl": "", "userId": ""}

    async def close(self) -> None:
        pass  # 每次请求用 async with，无需手动 close


# ── HTML parsers ──────────────────────────────────────────────────────────────

def extract_csrf_token(html: str) -> str:
    tree = HTMLParser(html or "")
    # 优先找 <input name="_token">（Laravel 表单标准）
    token_node = tree.css_first("input[name='_token'], input[name=_token]")
    value = token_node.attributes.get("value") if token_node else ""
    # 兜底：<meta name="csrf-token">
    if not value:
        meta = tree.css_first("meta[name='csrf-token']")
        value = meta.attributes.get("content", "") if meta else ""
    if not value:
        raise ValueError("无法从登录页读取 CSRF token")
    return value


def parse_home_user(html: str) -> dict:
    tree = HTMLParser(html or "")
    trigger = tree.css_first("#user-modal-trigger")
    link = trigger.attributes.get("href", "") if trigger else ""
    name_node = tree.css_first("#user-modal-name")
    username = name_node.text(strip=True) if name_node else ""
    avatar_node = tree.css_first("#user-modal-dp-wrapper img")
    avatar = avatar_node.attributes.get("src", "") if avatar_node else ""
    user_id = ""
    if "/user/" in link:
        user_id = link.rstrip("/").rsplit("/", 1)[-1]
    logged_in = bool(username and user_id and "/login" not in link)
    return {
        "loggedIn": logged_in,
        "username": username if logged_in else "",
        "avatarUrl": avatar if logged_in else "",
        "userId": user_id if logged_in else "",
    }
