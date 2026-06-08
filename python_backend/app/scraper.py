from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
import json
import re
import time
from typing import Any
from urllib.parse import urlparse
from urllib.parse import urlencode

import httpx
from selectolax.parser import HTMLParser

from .parser import extract_video_page, looks_like_blocked_page, parse_total_pages, parse_video_grid, parse_home_page, parse_playlist_grid, parse_subscription_creators, parse_query_creator_info
from .paths import app_home
from .settings import AppSettings
from .account import AccountSession, parse_home_user
from .chrome_cookies import cookies_for_host, load_cookies, load_user_agent


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}

HTML_CACHE_TTL_SECONDS = 20
HTTP_BLOCKED_COOLDOWN_SECONDS = 30
HOME_OPTIONAL_SECTION_TIMEOUT_SECONDS = 0.2
PROFILE_SECTION_TITLES = {
    "watchLater": "稍后观看",
    "likes": "喜欢的影片",
    "playlists": "播放清单",
    "subscriptions": "我的订阅",
    "histories": "观看历史",
}


class SessionBlockedError(RuntimeError):
    pass


class LoginError(RuntimeError):
    pass


class HanimeScraper:
    def __init__(self, client: httpx.AsyncClient | None = None, home=None, settings_provider=None, account_session: AccountSession | None = None):
        self.client = client or httpx.AsyncClient(timeout=30, follow_redirects=True, headers=DEFAULT_HEADERS)
        self._owns_client = client is None
        self.home = app_home(home)
        self.settings_provider = settings_provider or AppSettings
        self.account_session = account_session or AccountSession(self.home)
        self._html_cache: dict[tuple[str, str], tuple[float, str]] = {}
        self._http_blocked_until: dict[str, float] = {}
        self._authenticated = self.account_session.is_logged_in()
        self._cf_cookies = load_cookies(self.home)
        self._apply_login_cookies_to_client()
        self._apply_cf_cookies_to_client()

    async def parse(self, url: str) -> dict:
        video_id = extract_query_value(url, "v")
        if video_id:
            # Concurrently fetch the main page and the download page to halve latency
            async def _safe_fetch_download() -> str:
                try:
                    return await self.fetch_html(f"https://hanime1.me/download?v={video_id}", url)
                except Exception:
                    return ""

            html, download_html = await asyncio.gather(
                self.fetch_html(url, "https://hanime1.me/"),
                _safe_fetch_download(),
            )
        else:
            html = await self.fetch_html(url, "https://hanime1.me/")
            download_html = ""
        return extract_video_page(url, html, download_html)

    async def browse(self, category: str, page: int) -> dict:
        if category == "首页":
            watching_url = "https://hanime1.me/search?sort=%E4%BB%96%E5%80%91%E5%9C%A8%E7%9C%8B"

            async def _fetch_home_with_fallback() -> str:
                try:
                    return await self.fetch_html("https://hanime1.me/", "https://hanime1.me/")
                except Exception as e:
                    return await self._fallback_home_html(e)

            async def _safe_fetch_watching() -> str:
                try:
                    return await self.fetch_html(watching_url, "https://hanime1.me/")
                except Exception:
                    return ""

            html = await _fetch_home_with_fallback()
            try:
                watching_html = await asyncio.wait_for(
                    _safe_fetch_watching(),
                    timeout=HOME_OPTIONAL_SECTION_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                watching_html = ""
            parsed_home = parse_home_page(html)
            sections = list(parsed_home.get("sections") or [])
            watching_videos = parse_video_grid(watching_html) if watching_html else []
            if watching_videos:
                sections.append({
                    "sectionTitle": "他們在看",
                    "sectionLink": watching_url,
                    "videos": watching_videos[:20]
                })
            return {"isHome": True, "sections": sections, "hero": parsed_home.get("hero"), "currentPage": page, "totalPages": 1}
        if category.startswith("user:"):
            parts = category.split(":")
            user_id = parts[1]
            subpage = parts[2] if len(parts) > 2 else "home"
            sort = parts[3] if len(parts) > 3 else "latest"
            
            if subpage == "uploaded":
                url = f"https://hanime1.me/user/{user_id}/uploaded?sort={sort}&page={max(page, 1)}"
            elif subpage == "playlists":
                url = f"https://hanime1.me/user/{user_id}/playlists?sort={sort}&page={max(page, 1)}"
            else:
                url = f"https://hanime1.me/user/{user_id}?page={max(page, 1)}"
                
            html = await self.fetch_html(url, "https://hanime1.me/")
            tree = HTMLParser(html)
            
            # Extract profile info
            h1_node = tree.css_first("h1.profile-display-name")
            creator_name = h1_node.text(strip=True) if h1_node else f"用户 {user_id}"
            
            avatar_node = tree.css_first(".profile-avatar-wrapper img")
            creator_avatar = avatar_node.attributes.get("src", "") if avatar_node else ""
            
            stats_node = tree.css_first(".profile-sub-stats-new-line")
            creator_stats = stats_node.text(strip=True) if stats_node else ""
            
            if subpage == "playlists":
                videos = parse_playlist_grid(html)
            else:
                videos = parse_video_grid(html)
            
            return {
                "videos": videos,
                "currentPage": page,
                "totalPages": parse_total_pages(html, page),
                "creatorName": creator_name,
                "creatorAvatar": creator_avatar,
                "creatorId": user_id,
                "creatorStats": creator_stats,
                "isCreatorPage": True
            }

        if category.startswith("playlist:"):
            playlist_id = category.split(":", 1)[1]
            url = f"https://hanime1.me/playlist?list={playlist_id}&page={max(page, 1)}"
            html = await self.fetch_html(url, "https://hanime1.me/")
            tree = HTMLParser(html)
            
            h1_node = tree.css_first("h1")
            playlist_title = h1_node.text(strip=True) if h1_node else "播放清單"
            
            creator_node = None
            for a in tree.css("a"):
                href = a.attributes.get("href", "")
                if "/user/" in href:
                    creator_node = a
                    break
                    
            creator_name = ""
            creator_id = ""
            if creator_node:
                creator_name = creator_node.text(strip=True)
                href = creator_node.attributes.get("href", "")
                parts = href.rstrip("/").split("/")
                if parts:
                    creator_id = parts[-1]
            
            videos = parse_video_grid(html)
            
            return {
                "videos": videos,
                "currentPage": page,
                "totalPages": parse_total_pages(html, page),
                "playlistTitle": playlist_title,
                "creatorName": creator_name,
                "creatorId": creator_id,
                "isPlaylistPage": True
            }
            
        if category.startswith("query:"):
            search_query = category[6:]
            url = f"https://hanime1.me/search?{urlencode({'query': search_query, 'page': max(page, 1)})}"
            html = await self.fetch_html(url, "https://hanime1.me/")
            creator_info = parse_query_creator_info(html)
            result = {"videos": parse_video_grid(html), "currentPage": page, "totalPages": parse_total_pages(html, page)}
            if creator_info:
                result.update(creator_info)
            return result

        query = urlencode({"genre": category, "page": max(page, 1)})
        url = f"https://hanime1.me/search?{query}"
        html = await self.fetch_html(url, "https://hanime1.me/")
        return {"videos": parse_video_grid(html), "currentPage": page, "totalPages": parse_total_pages(html, page)}

    async def _fallback_home_html(self, original_error: Exception) -> str:
        import os
        candidates = [
            os.path.join("test", "Hanime1.me - H動漫_裏番_線上看.html"),
            os.path.join(os.path.dirname(__file__), "..", "..", "test", "Hanime1.me - H動漫_裏番_線上看.html"),
            os.path.join(str(self.home), "test", "Hanime1.me - H動漫_裏番_線上看.html"),
            os.path.join(str(self.home), "..", "test", "Hanime1.me - H動漫_裏番_線上看.html"),
        ]
        for path in candidates:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
        raise original_error


    async def search(self, **kwargs) -> dict:
        page = int(kwargs.get("page") or 1)
        params: list[tuple[str, str]] = [
            ("query", kwargs.get("query") or ""),
            ("type", kwargs.get("type") or ""),
            ("genre", kwargs.get("genre") or ""),
            ("sort", kwargs.get("sort") or ""),
            ("date", kwargs.get("date") or ""),
            ("duration", kwargs.get("duration") or ""),
            ("page", str(max(page, 1))),
        ]
        for tag in kwargs.get("tags") or []:
            if tag:
                params.append(("tags[]", tag))
        html = await self.fetch_html(f"https://hanime1.me/search?{urlencode(params)}", "https://hanime1.me/search")
        return {"videos": parse_video_grid(html), "currentPage": page, "totalPages": parse_total_pages(html, page)}

    async def comments(self, video_id: str) -> list[dict]:
        data = await self.comments_context(video_id)
        return data["comments"]

    async def comments_context(self, video_id: str) -> dict:
        url = f"https://hanime1.me/loadComment?id={video_id}&type=video&content=comment-tablink"
        data = await self.fetch_json(url, "https://hanime1.me/")
        html = data.get("comments", "")
        return parse_comment_context(html, video_id)

    async def replies(self, comment_id: str) -> list[dict]:
        data = await self.fetch_json(f"https://hanime1.me/loadReplies?id={comment_id}", "https://hanime1.me/")
        return parse_comments(data.get("replies", ""))

    async def post_form(self, url: str, data: dict, referer: str = "https://hanime1.me") -> dict:
        headers = referer_header(referer)
        headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        })
        token = str(data.get("_token") or "")
        if token:
            headers["X-CSRF-TOKEN"] = token
        response = await self._request_http("POST", url, headers=headers, data=data)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            return response.json()
        try:
            return response.json()
        except Exception:
            return {"ok": True, "text": response.text}

    async def profile_section(self, section: str, user_id: str, page: int = 1) -> dict:
        page = max(int(page or 1), 1)
        paths = {
            "watchLater": f"https://hanime1.me/user/{user_id}/saves?page={page}",
            "likes": f"https://hanime1.me/user/{user_id}/likes?page={page}",
            "playlists": f"https://hanime1.me/user/{user_id}/playlists?page={page}",
            "histories": f"https://hanime1.me/user/{user_id}/histories?sort=latest&page={page}",
            "subscriptions": f"https://hanime1.me/subscriptions?page={page}",
        }
        if section not in paths:
            raise ValueError("未知个人主页板块")
        html = await self.fetch_html(paths[section], "https://hanime1.me/")
        if section == "playlists":
            items = parse_playlist_grid(html)
        elif section == "subscriptions":
            items = parse_subscription_creators(html)
        else:
            items = parse_video_grid(html)
        return {
            "section": section,
            "title": PROFILE_SECTION_TITLES.get(section, section),
            "items": items,
            "currentPage": page,
            "totalPages": parse_total_pages(html, page),
        }

    async def fetch_html(self, url: str, referer: str = "") -> str:
        cached = self._get_cached_html(url, referer)
        if cached is not None:
            return cached
        max_attempts = 3
        last_error: Exception | None = None
        for attempt in range(max_attempts):
            if attempt > 0:
                await asyncio.sleep(2)
            if self._should_skip_http(url):
                last_error = SessionBlockedError("HTTP 请求暂时被阻断，请刷新 Cookie 后重试")
                continue
            try:
                response = await self._request_http("GET", url, headers=referer_header(referer))
                if usable_response(response) and looks_like_hanime_content(response.text) and not looks_like_blocked_page(response.text):
                    self._set_cached_html(url, referer, response.text)
                    return response.text
                if response.status_code == 429:
                    # 限流才封锁域名，401/403 是认证问题不应阻断后续请求
                    self._mark_http_blocked(url)
                if looks_like_blocked_page(response.text):
                    raise SessionBlockedError("HTTP 请求被 Cloudflare 拦截，请先刷新可用 Cookie 后重试")
                last_error = SessionBlockedError(f"HTTP 请求失败（HTTP {response.status_code}）")
            except SessionBlockedError:
                raise
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error if isinstance(last_error, SessionBlockedError) else SessionBlockedError(f"HTTP 请求失败: {last_error}") from last_error
        raise SessionBlockedError("HTTP 请求失败")

    async def fetch_json(self, url: str, referer: str = "") -> dict:
        headers = referer_header(referer)
        headers.update({"X-Requested-With": "XMLHttpRequest", "Accept": "application/json, text/javascript, */*; q=0.01"})
        try:
            response = await self._request_http("GET", url, headers=headers)
            if usable_response(response):
                return response.json()
            if response.status_code in {401, 403, 429}:
                raise SessionBlockedError("HTTP JSON 请求被拦截，请刷新 Cookie 后重试")
            raise SessionBlockedError(f"HTTP JSON 请求失败（HTTP {response.status_code}）")
        except SessionBlockedError:
            raise
        except Exception as exc:
            raise SessionBlockedError(f"HTTP JSON 请求失败: {exc}") from exc

    async def fetch_bytes(self, url: str, referer: str = "") -> tuple[bytes, str]:
        response = await self._request_http("GET", url, headers=referer_header(referer))
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "application/octet-stream")

    async def stream_bytes(
        self,
        url: str,
        referer: str = "",
        range_header: str | None = None,
    ) -> tuple[AsyncIterator[bytes], int, str, dict[str, str]]:
        headers = referer_header(referer)
        if range_header:
            headers["Range"] = range_header
        request = self.client.build_request("GET", url, headers=headers)
        response = await self.client.send(request, stream=True, follow_redirects=True)

        async def body() -> AsyncIterator[bytes]:
            try:
                async for chunk in response.aiter_bytes():
                    yield chunk
            finally:
                await response.aclose()

        response_headers = {}
        for key in ("content-range", "accept-ranges", "content-length"):
            if response.headers.get(key):
                response_headers[key] = response.headers[key]
        return body(), response.status_code, response.headers.get("content-type", "application/octet-stream"), response_headers

    def _get_cached_html(self, url: str, referer: str) -> str | None:
        cached = self._html_cache.get((url, referer))
        if not cached:
            return None
        expires_at, html = cached
        if time.monotonic() >= expires_at:
            self._html_cache.pop((url, referer), None)
            return None
        return html

    def _set_cached_html(self, url: str, referer: str, html: str) -> None:
        self._html_cache[(url, referer)] = (time.monotonic() + HTML_CACHE_TTL_SECONDS, html)

    def _should_skip_http(self, url: str) -> bool:
        host = urlparse(url).netloc
        return bool(host and time.monotonic() < self._http_blocked_until.get(host, 0))

    def _mark_http_blocked(self, url: str) -> None:
        host = urlparse(url).netloc
        if host:
            self._http_blocked_until[host] = time.monotonic() + HTTP_BLOCKED_COOLDOWN_SECONDS

    async def _request_http(self, method: str, url: str, headers: dict | None = None, data: Any | None = None):
        if not self._owns_client:
            return await self.client.request(method, url, headers=headers, data=data)
        try:
            from curl_cffi.requests import AsyncSession as CurlSession
        except ImportError:
            return await self.client.request(method, url, headers=headers, data=data)

        merged_headers = dict(self.client.headers)
        if headers:
            merged_headers.update(headers)
        cookies = self._cookies_for_request(url)
        async with CurlSession(impersonate="chrome124", timeout=30) as curl:
            response = await curl.request(
                method,
                url,
                headers=merged_headers,
                cookies=cookies,
                data=data,
                allow_redirects=True,
            )
            self._persist_response_cookies(url, response)
            return response

    def _cookies_for_request(self, url: str) -> dict[str, str]:
        host = urlparse(url).hostname or ""
        cookies: dict[str, str] = {}
        if "hanime1.me" in host:
            for cookie in cookies_for_host(self._cf_cookies, host):
                name = cookie.get("name")
                value = cookie.get("value")
                if name and value:
                    cookies[str(name)] = str(value)
            cookies.update(self.account_session.load_login_cookies())
        else:
            for cookie in self.client.cookies.jar:
                if cookie.name and cookie.value:
                    cookies[cookie.name] = cookie.value
        return cookies

    def _persist_response_cookies(self, url: str, response) -> None:
        host = urlparse(url).hostname or ""
        if "hanime1.me" not in host:
            return
        cookies = getattr(response, "cookies", None)
        if not cookies:
            return
        values = dict(cookies)
        session_values = {
            name: value
            for name, value in values.items()
            if name == "hanime1_session" or name == "XSRF-TOKEN" or name.startswith("remember_web")
        }
        if session_values:
            self.account_session.save_login_cookies_dict(session_values)
            self._apply_login_cookies_to_client()

    async def login(self, email: str, password: str) -> dict:
        """Log in to hanime1.me using HTTP (curl_cffi) with stored CF clearance cookies."""
        cf_data = self._load_cf_cookies()
        if not cf_data:
            raise LoginError(
                "未找到 Cloudflare 通行证 (cf_clearance)。\n"
                "请先刷新可用的 HTTP Cookie 后再尝试登录。"
            )

        cookies = {c["name"]: c["value"] for c in cf_data.get("cookies", []) if c.get("domain", "").endswith("hanime1.me")}
        ua = cf_data.get("user_agent") or DEFAULT_HEADERS["User-Agent"]

        try:
            from curl_cffi.requests import AsyncSession as CurlSession
        except ImportError:
            raise LoginError("curl_cffi 未安装，请联系开发者")

        async with CurlSession(impersonate="chrome124", timeout=30) as curl:
            # Step 1: GET login page to extract CSRF token
            r1 = await curl.get(
                "https://hanime1.me/login",
                cookies=cookies,
                headers={"User-Agent": ua, "Referer": "https://hanime1.me/"},
                allow_redirects=True,
            )
            if r1.status_code != 200:
                raise LoginError(f"无法访问登录页（HTTP {r1.status_code}），请先刷新 Cloudflare 通行证")

            # Extract CSRF token
            from selectolax.parser import HTMLParser
            tree = HTMLParser(r1.text)
            token_node = tree.css_first("input[name='_token']")
            token = token_node.attributes.get("value", "") if token_node else ""
            if not token:
                meta = tree.css_first("meta[name='csrf-token']")
                token = meta.attributes.get("content", "") if meta else ""
            if not token:
                raise LoginError("无法提取登录页 CSRF token，页面可能已被 Cloudflare 拦截")

            # Step 2: POST login form
            r2 = await curl.post(
                "https://hanime1.me/login",
                data={"_token": token, "email": email, "password": password},
                cookies=cookies,
                headers={
                    "User-Agent": ua,
                    "Referer": "https://hanime1.me/login",
                    "X-CSRF-TOKEN": token,
                    "Origin": "https://hanime1.me",
                },
                allow_redirects=False,
            )

            # Session cookie indicates success
            session_val = curl.cookies.get("hanime1_session")
            if not session_val:
                # Try extracting from Set-Cookie header
                set_cookie = r2.headers.get("set-cookie", "")
                import re as _re
                m = _re.search(r"hanime1_session=([^;]+)", set_cookie)
                session_val = m.group(1) if m else ""

            if not session_val:
                # Login failed — check error message
                if r2.status_code == 302:
                    loc = r2.headers.get("location", "")
                    if "/login" in loc:
                        raise LoginError("账号或密码错误，请重新检查")
                    raise LoginError(f"登录后跳转到意外页面: {loc}")
                tree2 = HTMLParser(r2.text)
                err_node = tree2.css_first(".alert-danger, .invalid-feedback, .error-message")
                err_msg = err_node.text(strip=True) if err_node else ""
                raise LoginError(err_msg or f"登录失败（HTTP {r2.status_code}）")

            # Apply session cookie to httpx client for all subsequent requests
            all_new = dict(curl.cookies)
            for name, val in all_new.items():
                self.client.cookies.set(name, val, domain=".hanime1.me")
            # Ensure key cookies are set explicitly
            self.client.cookies.set("hanime1_session", session_val, domain=".hanime1.me")
            if "cf_clearance" in cookies:
                self.client.cookies.set("cf_clearance", cookies["cf_clearance"], domain=".hanime1.me")
            self.client.headers["User-Agent"] = ua
            login_cookies = {"hanime1_session": session_val}
            for name, val in all_new.items():
                if name.startswith("remember_web"):
                    login_cookies[name] = val
            self.account_session.save_login_cookies_dict(login_cookies)
            self._apply_login_cookies_to_client()
            self._authenticated = True
            return {"success": True, "message": "登录成功", "loggedIn": True}

    def _load_cf_cookies(self) -> dict | None:
        cf_file = self.home / "cf_cookies.json"
        if not cf_file.exists():
            return None
        try:
            import json as _json
            return _json.loads(cf_file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _is_logged_in_html(self, html: str) -> bool:
        lower = (html or "").lower()
        return any(marker in lower for marker in (
            "logout", "log-out", "signout", "sign-out",
            "登出", "登出帳號", "我的帳號", "我的账号",
            "profile", "avatar", "user-avatar",
        ))

    async def get_login_status(self) -> dict:
        """Check whether the current session is authenticated."""
        if not self._authenticated:
            return {"loggedIn": False, "username": "", "avatarUrl": "", "userId": ""}
        try:
            html = await self.fetch_html("https://hanime1.me/", "https://hanime1.me/")
            user = parse_home_user(html)
            if user.get("loggedIn"):
                return user
        except Exception:
            pass
        return {"loggedIn": True, "username": "", "avatarUrl": "", "userId": ""}

    async def logout(self) -> dict:
        """Log out of hanime1.me by clearing session cookies."""
        for name in ("hanime1_session", "remember_web_*", "XSRF-TOKEN"):
            self.client.cookies.delete(name, domain=".hanime1.me")
        self.client.cookies.clear()
        self.account_session.clear()
        self._authenticated = False
        return {"success": True, "message": "已登出", "loggedIn": False}

    def _apply_login_cookies_to_client(self) -> None:
        for name, value in self.account_session.load_login_cookies().items():
            if value:
                self.client.cookies.set(name, value)

    def _apply_cf_cookies_to_client(self) -> None:
        ua = load_user_agent(self.home)
        if ua:
            self.client.headers["User-Agent"] = ua
        for cookie in cookies_for_host(self._cf_cookies, "hanime1.me"):
            name = cookie.get("name")
            value = cookie.get("value")
            if name and value:
                self.client.cookies.set(
                    name,
                    value,
                    domain=cookie.get("domain") or ".hanime1.me",
                    path=cookie.get("path") or "/",
                )

    def reload_cookie_session(self) -> None:
        self._cf_cookies = load_cookies(self.home)
        self._apply_cf_cookies_to_client()
        self._html_cache.clear()
        self._http_blocked_until.clear()

    async def validate_cookie_session(self) -> bool:
        try:
            response = await self._request_http("GET", "https://hanime1.me/", headers=referer_header("https://hanime1.me/"))
            if response.status_code in {401, 403}:
                return False
            if looks_like_blocked_page(response.text):
                return False
            return usable_response(response) and looks_like_hanime_content(response.text)
        except Exception as exc:
            # 网络错误不代表 cookie 失效，保守地认为仍然有效，避免不必要的浏览器刷新
            import logging
            logging.getLogger(__name__).debug("Cookie 验证请求失败（按有效处理）: %s", exc)
            return True

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()


def parse_comments(html: str) -> list[dict]:
    tree = HTMLParser(html or "")
    comments: list[dict] = []
    for wrapper in tree.css(".report-btn-wrapper"):
        report = wrapper.css_first(".report-btn[data-reportable-id]")
        text_blocks = wrapper.css(".comment-index-text")
        if not report or len(text_blocks) < 2:
            continue
        user_block = text_blocks[0]
        content_block = text_blocks[1]
        time_node = user_block.css_first("span")
        time_text = time_node.text(strip=True) if time_node else ""
        user_name = user_block.text(strip=True).replace(time_text, "").strip()
        content = content_block.text(strip=True)
        if not content:
            continue
        action_scope = find_comment_action_scope(wrapper)
        like_count = int_attr(find_in_comment_scope(wrapper, action_scope, "input[name='comment-likes-sum']"), "value")
        like_total = int_attr(find_in_comment_scope(wrapper, action_scope, "input[name='comment-likes-count']"), "value")
        like_form = find_in_comment_scope(wrapper, action_scope, ".comment-like-form")
        like_status = attr_from(like_form, "input[name='like-comment-status']", "value")
        unlike_status = attr_from(like_form, "input[name='unlike-comment-status']", "value")
        like_user_id = attr_from(like_form, "input[name='comment-like-user-id']", "value")
        foreign_type = attr_from(like_form, "input[name='foreign_type']", "value")
        foreign_id = attr_from(like_form, "input[name='foreign_id']", "value")
        replies_button = find_in_comment_scope(wrapper, action_scope, ".load-replies-btn[data-commentid], .load-replies-btn")
        reply_count = extract_first_int(replies_button.text(strip=True) if replies_button else "")
        comments.append({
            "commentId": report.attributes.get("data-reportable-id", ""),
            "userName": user_name,
            "avatarUrl": find_comment_avatar_url(wrapper),
            "content": content,
            "timeText": time_text,
            "likeCount": like_count,
            "likeTotal": like_total,
            "likeStatus": like_status,
            "unlikeStatus": unlike_status,
            "likeUserId": like_user_id,
            "foreignType": foreign_type or "comment",
            "foreignId": foreign_id or report.attributes.get("data-reportable-id", ""),
            "hasReplies": bool(replies_button and reply_count > 0),
            "replyCount": reply_count,
        })
    return comments


def parse_comment_context(html: str, video_id: str = "") -> dict:
    tree = HTMLParser(html or "")
    form = tree.css_first("#comment-create-form")
    token = ""
    user_id = ""
    avatar_url = ""
    if form:
        token_node = form.css_first("input[name='_token'], input[name=_token]")
        user_node = form.css_first("input[name='comment-user-id'], input[name=comment-user-id]")
        avatar_node = form.css_first("img")
        token = token_node.attributes.get("value", "") if token_node else ""
        user_id = user_node.attributes.get("value", "") if user_node else ""
        if avatar_node:
            avatar_url = avatar_node.attributes.get("src") or avatar_node.attributes.get("data-src") or ""
    return {
        "comments": parse_comments(html),
        "csrfToken": token,
        "currentUserId": user_id,
        "avatarUrl": avatar_url,
        "videoId": video_id,
    }


def int_attr(node, attr: str, default: int = 0) -> int:
    if not node:
        return default
    return extract_first_int(node.attributes.get(attr, ""), default)


def attr_from(scope, selector: str, attr: str, default: str = "") -> str:
    if not scope:
        return default
    node = scope.css_first(selector)
    if not node:
        return default
    return str(node.attributes.get(attr, default) or default)


def extract_first_int(value: str, default: int = 0) -> int:
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else default


def find_comment_avatar_url(wrapper) -> str | None:
    img = wrapper.css_first("img.img-circle, img")
    if img:
        src = img.attributes.get("src") or img.attributes.get("data-src") or ""
        if src:
            return src
    origin = wrapper
    while origin:
        current = origin.prev
        while current:
            img = current.css_first("img.img-circle, img")
            if img:
                src = img.attributes.get("src") or img.attributes.get("data-src") or ""
                if src:
                    return src
            current = current.prev
        origin = origin.parent
    return None


def find_comment_action_scope(wrapper):
    current = wrapper.next
    while current:
        if "report-btn-wrapper" in (current.attributes.get("class") or ""):
            return None
        if (
            current.css_first("input[name='comment-likes-sum']")
            or current.css_first(".load-replies-btn[data-commentid], .load-replies-btn")
        ):
            return current
        current = current.next
    return None


def find_in_comment_scope(wrapper, action_scope, selector: str):
    return wrapper.css_first(selector) or (action_scope.css_first(selector) if action_scope else None)


def referer_header(referer: str) -> dict:
    return {"Referer": referer} if referer else {}


def usable_response(response: httpx.Response) -> bool:
    if response.status_code in {401, 403, 429} or response.status_code >= 500:
        return False
    text = response.text
    return bool(text.strip()) and not looks_like_blocked_page(text)


def looks_like_hanime_content(html: str) -> bool:
    lower = (html or "").lower()
    return any(
        marker in lower
        for marker in (
            "watch?v=",
            "download-table",
            "video-details-wrapper",
            "related-tabcontent",
            "loadcomment",
            "hanime1.me",
            # 个人主页相关页面
            "user-profile",
            "profile-header",
            "/user/",
            "subscriptions",
            "watch-later",
        )
    )


def extract_query_value(url: str, key: str) -> str:
    from urllib.parse import parse_qs, urlparse

    return parse_qs(urlparse(url).query).get(key, [""])[0]
