from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
import json
import re
import time
from urllib.parse import urlparse
from urllib.parse import urlencode

import httpx
from selectolax.parser import HTMLParser

from .parser import extract_video_page, looks_like_blocked_page, parse_total_pages, parse_video_grid, parse_home_page, parse_playlist_grid
from .paths import app_home
from .settings import AppSettings
from .browsers import detect_browsers


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}

HTML_CACHE_TTL_SECONDS = 20
HTTP_BLOCKED_COOLDOWN_SECONDS = 30
HOME_OPTIONAL_SECTION_TIMEOUT_SECONDS = 0.2


class SessionBlockedError(RuntimeError):
    pass


class HanimeScraper:
    def __init__(self, client: httpx.AsyncClient | None = None, home=None, settings_provider=None):
        self.client = client or httpx.AsyncClient(timeout=30, follow_redirects=True, headers=DEFAULT_HEADERS)
        self._owns_client = client is None
        self.home = app_home(home)
        self.settings_provider = settings_provider or AppSettings
        self._browser_lock = asyncio.Lock()
        self._playwright = None
        self._context = None
        self._session_page = None
        self._html_cache: dict[tuple[str, str], tuple[float, str]] = {}
        self._http_blocked_until: dict[str, float] = {}

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
                except (Exception, asyncio.CancelledError):
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
                    os.path.join(str(self.home), "..", "test", "Hanime1.me - H動漫_裏番_線上看.html")
                ]
                html = None
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
        url = f"https://hanime1.me/loadComment?id={video_id}&type=video&content=comment-tablink"
        data = await self.fetch_json(url, "https://hanime1.me/")
        return parse_comments(data.get("comments", ""))

    async def replies(self, comment_id: str) -> list[dict]:
        data = await self.fetch_json(f"https://hanime1.me/loadReplies?id={comment_id}", "https://hanime1.me/")
        return parse_comments(data.get("replies", ""))

    async def fetch_html(self, url: str, referer: str = "") -> str:
        cached = self._get_cached_html(url, referer)
        if cached is not None:
            return cached
        if not self._should_skip_http(url):
            try:
                response = await self.client.get(url, headers=referer_header(referer))
                if usable_response(response):
                    self._set_cached_html(url, referer, response.text)
                    return response.text
                if response.status_code in {401, 403, 429}:
                    self._mark_http_blocked(url)
            except Exception:
                pass
        html = await self.fetch_with_playwright(url)
        if looks_like_blocked_page(html) or not looks_like_hanime_content(html):
            raise SessionBlockedError("HTTP 会话被 Cloudflare 拦截，请在打开的浏览器窗口完成验证后重试")
        self._set_cached_html(url, referer, html)
        return html

    async def fetch_json(self, url: str, referer: str = "") -> dict:
        headers = referer_header(referer)
        headers.update({"X-Requested-With": "XMLHttpRequest", "Accept": "application/json, text/javascript, */*; q=0.01"})
        try:
            response = await self.client.get(url, headers=headers)
            if usable_response(response):
                return response.json()
        except Exception:
            pass
        text = await self.fetch_with_playwright_fetch(url)
        return json.loads(text or "{}")

    async def fetch_bytes(self, url: str, referer: str = "") -> tuple[bytes, str]:
        response = await self.client.get(url, headers=referer_header(referer))
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

    async def sync_cookies_to_client(self) -> None:
        if not self._context or not self._session_page:
            return
        try:
            ua = await self._session_page.evaluate("navigator.userAgent")
            if ua:
                self.client.headers["User-Agent"] = ua
        except Exception:
            pass
        try:
            cookies = await self._context.cookies()
            for cookie in cookies:
                self.client.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie["domain"],
                    path=cookie["path"]
                )
        except Exception:
            pass

    async def fetch_with_playwright(self, url: str) -> str:
        """Navigate to url using Playwright and return the page HTML.

        If the browser/page has been closed unexpectedly (user closed the window,
        OS killed the process, etc.) the method automatically recovers by tearing
        down the stale session, launching a fresh browser window, and retrying
        the navigation once.
        """
        async with self._browser_lock:
            return await self._fetch_with_playwright_locked(url)

    async def _fetch_with_playwright_locked(self, url: str, _retried: bool = False) -> str:
        """Inner implementation – must be called while _browser_lock is held."""
        settings = self.settings_provider()
        try:
            await self.ensure_browser()
            page = self._session_page
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            deadline = time.monotonic() + settings.browserVerificationTimeoutSeconds

            async def safe_content() -> str:
                for _ in range(5):
                    try:
                        return await page.content()
                    except Exception:
                        await asyncio.sleep(1)
                return await page.content()

            html = await safe_content()
            while looks_like_blocked_page(html) and time.monotonic() < deadline:
                await asyncio.sleep(2)
                html = await safe_content()
            if not looks_like_blocked_page(html) and looks_like_hanime_content(html):
                await self.sync_cookies_to_client()
            return html

        except Exception as exc:
            if not _retried and is_browser_closed_error(exc):
                # Browser or page was closed externally – recover automatically.
                import logging
                logging.getLogger(__name__).warning(
                    "抓取浏览器意外关闭，正在自动重新启动浏览器会话… (%s)", exc
                )
                await self._reset_browser_locked()
                return await self._fetch_with_playwright_locked(url, _retried=True)
            raise

    async def fetch_with_playwright_fetch(self, url: str) -> str:
        """Use the browser's built-in fetch() to retrieve *url*.

        Same auto-recovery behaviour as fetch_with_playwright.
        """
        async with self._browser_lock:
            return await self._fetch_with_playwright_fetch_locked(url)

    async def _fetch_with_playwright_fetch_locked(self, url: str, _retried: bool = False) -> str:
        """Inner implementation – must be called while _browser_lock is held."""
        try:
            await self.ensure_browser()
            return await self._session_page.evaluate(
                """async (url) => {
                    const r = await fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}});
                    return await r.text();
                }""",
                url,
            )
        except Exception as exc:
            if not _retried and is_browser_closed_error(exc):
                import logging
                logging.getLogger(__name__).warning(
                    "抓取浏览器意外关闭，正在自动重新启动浏览器会话… (%s)", exc
                )
                await self._reset_browser_locked()
                return await self._fetch_with_playwright_fetch_locked(url, _retried=True)
            raise

    async def _reset_browser_locked(self) -> None:
        """Tear down the current (dead) browser session without holding any extra lock.

        Must be called while _browser_lock is already held.
        """
        # Graceful cleanup – ignore errors since the browser is already gone.
        try:
            if self._context:
                await self._context.close()
        except Exception:
            pass
        self._context = None
        self._session_page = None
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        self._playwright = None

    async def ensure_browser(self) -> None:
        if self._context:
            return
        self._playwright = await start_playwright()
        data_dir = self.home / ".playwright_data"
        selected_channel = self.settings_provider().browserChannel
        last_error = None
        for channel in launch_channel_order(selected_channel):
            try:
                self._context = await self._playwright.chromium.launch_persistent_context(
                    str(data_dir),
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled", "--start-minimized"],
                    **channel_kwargs(channel),
                )
                break
            except Exception as exc:
                last_error = exc
        if self._context is None and last_error is not None:
            raise last_error

        if self._context.pages:
            self._session_page = self._context.pages[0]
        else:
            self._session_page = await self._context.new_page()
        await self._session_page.goto("https://hanime1.me/", wait_until="domcontentloaded", timeout=60000)
        await self.sync_cookies_to_client()

    async def close(self) -> None:
        await self.close_browser()
        if self._owns_client:
            await self.client.aclose()

    async def close_browser(self) -> None:
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None
            self._session_page = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None


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
            "hasReplies": bool(replies_button and reply_count > 0),
            "replyCount": reply_count,
        })
    return comments


def int_attr(node, attr: str, default: int = 0) -> int:
    if not node:
        return default
    return extract_first_int(node.attributes.get(attr, ""), default)


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


def is_browser_closed_error(exc: BaseException) -> bool:
    """Return True when *exc* indicates the Playwright browser/page was closed.

    Playwright raises ``playwright.async_api.Error`` (or its subclasses such as
    ``TargetClosedError`` introduced in v1.42) when the browser process exits or
    the target page is destroyed.  We recognise both the typed exception and the
    legacy string-match approach so the recovery works across all supported
    Playwright versions.
    """
    # Prefer the typed exception when available (Playwright >= 1.42).
    try:
        from playwright.async_api import TargetClosedError  # type: ignore[attr-defined]
        if isinstance(exc, TargetClosedError):
            return True
    except ImportError:
        pass

    # Fallback: match the error message for older Playwright versions.
    msg = str(exc).lower()
    return any(
        phrase in msg
        for phrase in (
            "target closed",
            "browser has been closed",
            "browser closed",
            "connection closed",
            "context or browser has been closed",
            "page has been closed",
        )
    )


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
        )
    )


def extract_query_value(url: str, key: str) -> str:
    from urllib.parse import parse_qs, urlparse

    return parse_qs(urlparse(url).query).get(key, [""])[0]


async def start_playwright():
    from playwright.async_api import async_playwright

    return await async_playwright().start()


def fallback_channel(selected_channel: str) -> str:
    if selected_channel == "msedge":
        return "chrome"
    if selected_channel == "chrome":
        return "msedge"
    return "chromium"


def channel_kwargs(channel: str) -> dict:
    return {} if channel == "chromium" else {"channel": channel}


def available_browser_channels() -> list[str]:
    return [choice.channel for choice in detect_browsers() if choice.available]


def launch_channel_order(selected_channel: str) -> list[str]:
    ordered = [selected_channel]
    for channel in available_browser_channels():
        if channel not in ordered:
            ordered.append(channel)
    if "chromium" not in ordered:
        ordered.append("chromium")
    return ordered
