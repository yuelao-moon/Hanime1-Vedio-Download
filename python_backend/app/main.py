from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .downloads import DownloadManager
from .models import DownloadRequestItem
from .paths import app_home as resolve_app_home, static_dir
from .scraper import HanimeScraper, LoginError, SessionBlockedError
from .settings import AppSettings, SettingsStore
from .local_db import LocalStore
from .cookie_refresh import CookieRefreshManager


log = logging.getLogger(__name__)


def create_app(app_home: str | Path | None = None, scraper=None, account_client=None, cookie_manager=None) -> FastAPI:
    home = resolve_app_home(app_home)
    settings_store = SettingsStore(home)
    scraper = scraper or HanimeScraper(home=home, settings_provider=settings_store.load)
    if cookie_manager is None and hasattr(scraper, "validate_cookie_session") and hasattr(scraper, "reload_cookie_session"):
        cookie_manager = CookieRefreshManager(home, scraper=scraper)
    local_store = LocalStore(home)
    download_manager = DownloadManager(settings_store, resolver=lambda item: scraper.parse(item.pageUrl))

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        cookie_task = None
        try:
            if cookie_manager is not None and hasattr(cookie_manager, "ensure_valid"):
                cookie_task = asyncio.create_task(cookie_manager.ensure_valid())
                cookie_task.add_done_callback(log_cookie_task_result)
            yield
        finally:
            if cookie_task and not cookie_task.done():
                cookie_task.cancel()
            await download_manager.close()
            close = getattr(scraper, "close", None)
            if close:
                await close()
            close_account = getattr(account_client, "close", None)
            if close_account:
                await close_account()
            close_cookie = getattr(cookie_manager, "close", None)
            if close_cookie:
                await close_cookie()

    app = FastAPI(title="Hanime Media Center Python Backend", lifespan=lifespan)
    app.state.settings_store = settings_store
    app.state.scraper = scraper
    app.state.download_manager = download_manager
    app.state.local_store = local_store
    app.state.cookie_manager = cookie_manager

    @app.exception_handler(SessionBlockedError)
    async def session_blocked_handler(_request: Request, exc: SessionBlockedError):
        return PlainTextResponse(str(exc), status_code=503)

    @app.exception_handler(LoginError)
    async def login_error_handler(_request: Request, exc: LoginError):
        return PlainTextResponse(str(exc), status_code=401)

    @app.get("/")
    async def index():
        index_file = static_dir() / "index.html"
        if index_file.exists():
            return FileResponse(
                index_file,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        return {"message": "Python backend is running"}

    @app.post("/api/parse")
    async def parse_video(payload: dict):
        url = payload.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="缺少视频链接")
        return await scraper.parse(url)

    @app.get("/api/browse")
    async def browse(category: str, page: int = 1):
        if not category.strip():
            raise HTTPException(status_code=400, detail="缺少分类参数")
        return await scraper.browse(category, page)

    @app.get("/api/search")
    async def search(
        query: str = "",
        type: str = "",
        genre: str = "",
        tags: list[str] = Query(default=[], alias="tags[]"),
        sort: str = "",
        date: str = "",
        duration: str = "",
        page: int = 1,
    ):
        return await scraper.search(query=query, type=type, genre=genre, tags=tags, sort=sort, date=date, duration=duration, page=page)

    @app.get("/api/search/options")
    async def search_options():
        return default_search_options()

    @app.get("/api/cookies/status")
    async def cookie_status():
        if cookie_manager is None:
            return {"cookieCount": 0, "hasCfClearance": False}
        return cookie_manager.status()

    @app.post("/api/cookies/refresh")
    async def refresh_cookies():
        if cookie_manager is None:
            raise HTTPException(status_code=503, detail="Cookie 刷新器不可用")
        return await cookie_manager.refresh()

    @app.post("/api/login")
    async def login(payload: dict):
        email = (payload.get("email") or "").strip()
        password = payload.get("password") or ""
        if not email or not password:
            raise HTTPException(status_code=400, detail="邮箱和密码不能为空")
        return await scraper.login(email, password)

    @app.post("/api/logout")
    async def logout():
        return await scraper.logout()

    @app.get("/api/login/status")
    async def login_status():
        return await scraper.get_login_status()

    @app.post("/api/auth/login")
    async def auth_login(payload: dict):
        email = (payload.get("email") or "").strip()
        password = payload.get("password") or ""
        if not email or not password:
            raise HTTPException(status_code=400, detail="邮箱和密码不能为空")
        if account_client is not None and hasattr(account_client, "login"):
            return await account_client.login(email, password)
        return await scraper.login(email, password)

    @app.get("/api/auth/me")
    async def auth_me():
        if account_client is not None and hasattr(account_client, "me"):
            return await account_client.me()
        return await scraper.get_login_status()

    @app.post("/api/auth/logout")
    async def auth_logout():
        if account_client is not None and hasattr(account_client, "logout"):
            return await account_client.logout()
        return await scraper.logout()

    @app.get("/api/comments")
    async def comments(videoId: str):
        return await scraper.comments(videoId)

    @app.get("/api/replies")
    async def replies(commentId: str):
        return await scraper.replies(commentId)

    @app.get("/api/settings")
    async def get_settings():
        return settings_store.load().to_dict()

    @app.post("/api/settings")
    async def save_settings(payload: dict):
        settings = AppSettings.from_dict(payload)
        settings_store.save(settings)
        download_manager.settings = settings
        download_manager.gopeed_client.settings = settings
        return "Settings saved successfully."

    @app.post("/api/settings/clear-page-cache")
    async def clear_page_cache():
        local_store.clear_page_cache()
        return {"ok": True}

    @app.post("/api/settings/clear-cache")
    async def clear_cache():
        local_store.clear_local_cache()
        html_cache = getattr(scraper, "_html_cache", None)
        if isinstance(html_cache, dict):
            html_cache.clear()
        return {"ok": True}

    @app.get("/api/page-cache")
    async def get_page_cache(key: str):
        return local_store.get_page_cache(key) or {}

    @app.post("/api/page-cache")
    async def set_page_cache(payload: dict):
        key = (payload.get("key") or "").strip()
        if not key:
            raise HTTPException(status_code=400, detail="缺少缓存 key")
        local_store.set_page_cache(key, payload.get("data") or {}, int(payload.get("scrollY") or 0))
        return {"ok": True}

    @app.post("/api/watch-history/record")
    async def record_watch_history(payload: dict):
        try:
            return local_store.record_watch_history(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/watch-history")
    async def watch_history(limit: int = 100):
        return local_store.load_watch_history(limit)

    @app.post("/api/video/favorite")
    async def video_favorite(payload: dict):
        token = await resolve_token(payload, scraper)
        video_id = require_text(payload, "videoId", "缺少视频 ID")
        user_id = require_text(payload, "currentUserId", "缺少用户 ID")
        is_fav = bool(payload.get("isFav"))
        return await scraper.post_form("https://hanime1.me/like", {
            "_token": token,
            "like-foreign-id": video_id,
            "like-status": "1" if is_fav else "",
            "like-user-id": user_id,
            "like-is-positive": "1",
        })

    @app.post("/api/video/watch-later")
    async def video_watch_later(payload: dict):
        parsed = await resolve_video_payload(payload, scraper)
        token = require_text(parsed, "csrfToken", "缺少 CSRF token")
        video_id = require_text(parsed, "videoId", "缺少视频 ID")
        my_list = parsed.get("myList") or {}
        list_code = (payload.get("listCode") or my_list.get("watchLaterCode") or "").strip()
        if not list_code and payload.get("pageUrl"):
            parsed = await scraper.parse(str(payload.get("pageUrl") or f"https://hanime1.me/watch?v={video_id}"))
            my_list = parsed.get("myList") or {}
            list_code = str(my_list.get("watchLaterCode") or "").strip()
            token = str(parsed.get("csrfToken") or token).strip()
        if not list_code:
            list_code = "WL"
        if not list_code:
            raise HTTPException(status_code=400, detail="缺少稍后观看清单代码")
        return await scraper.post_form("https://hanime1.me/save", {
            "_token": token,
            "input_id": list_code,
            "video_id": video_id,
            "is_checked": "1" if payload.get("isChecked", True) else "",
            "user_id": parsed.get("currentUserId") or "",
        })

    @app.post("/api/video/my-list")
    async def video_my_list(payload: dict):
        token = await resolve_token(payload, scraper)
        return await scraper.post_form("https://hanime1.me/save", {
            "_token": token,
            "input_id": require_text(payload, "listCode", "缺少播放清单代码"),
            "video_id": require_text(payload, "videoId", "缺少视频 ID"),
            "is_checked": "1" if payload.get("isChecked", True) else "",
            "user_id": payload.get("currentUserId") or "",
        })

    @app.post("/api/creator/subscribe")
    async def creator_subscribe(payload: dict):
        token = await resolve_token(payload, scraper)
        is_subscribed = bool(payload.get("isSubscribed"))
        return await scraper.post_form("https://hanime1.me/subscribe", {
            "_token": token,
            "subscribe-user-id": require_text(payload, "userId", "缺少用户 ID"),
            "subscribe-artist-id": require_text(payload, "artistId", "缺少作者 ID"),
            "subscribe-status": "1" if is_subscribed else "",
        })

    @app.get("/api/profile/summary")
    async def profile_summary():
        user = await auth_me()
        if not user.get("loggedIn"):
            raise HTTPException(status_code=401, detail="请先登录")
        user_id = (user.get("userId") or "").strip()
        if not user_id:
            raise HTTPException(status_code=400, detail="无法读取用户 ID")
        sections = []
        for section in ("watchLater", "likes", "playlists", "subscriptions", "histories"):
            data = await scraper.profile_section(section, user_id, 1)
            preview = list(data.get("items") or [])[:6]
            data = dict(data)
            data["items"] = preview
            sections.append(data)
        return {"user": user, "sections": sections}

    @app.get("/api/profile/section/{section}")
    async def profile_section(section: str, page: int = 1):
        user = await auth_me()
        if not user.get("loggedIn"):
            raise HTTPException(status_code=401, detail="请先登录")
        user_id = (user.get("userId") or "").strip()
        if not user_id:
            raise HTTPException(status_code=400, detail="无法读取用户 ID")
        try:
            return await scraper.profile_section(section, user_id, page)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/check-update")
    async def check_update():
        return {"currentVersion": "1.0.0", "hasUpdate": False, "latestVersion": "1.0.0", "downloadUrl": "", "releaseNotes": ""}

    @app.get("/api/downloads")
    async def downloads():
        return download_manager.snapshot()

    @app.post("/api/downloads")
    async def enqueue(payload: dict):
        items = [DownloadRequestItem.from_dict(item) for item in payload.get("items", [])]
        if not items:
            raise HTTPException(status_code=400, detail="至少需要一个下载任务")
        return await download_manager.enqueue(items)

    @app.post("/api/downloads/{task_id}/pause")
    async def pause(task_id: str):
        return await call_download(lambda: download_manager.pause_task(task_id))

    @app.post("/api/downloads/{task_id}/resume")
    async def resume(task_id: str):
        return await call_download(lambda: download_manager.resume_task(task_id))

    @app.post("/api/downloads/{task_id}/cancel")
    async def cancel(task_id: str):
        return await call_download(lambda: download_manager.cancel_task(task_id))

    @app.post("/api/downloads/{task_id}/retry")
    async def retry(task_id: str):
        return await call_download(lambda: download_manager.retry_task(task_id))

    @app.post("/api/downloads/pause-all")
    async def pause_all():
        return await download_manager.pause_all()

    @app.post("/api/downloads/cancel-all")
    async def cancel_all():
        return await download_manager.cancel_all()

    @app.post("/api/downloads/retry-all-failed")
    async def retry_all_failed():
        return await call_download(download_manager.retry_all_failed)

    @app.delete("/api/downloads/history")
    @app.post("/api/downloads/history/clear")
    async def clear_history():
        return await download_manager.clear_history()

    @app.get("/api/downloads/stream")
    async def stream():
        queue = download_manager.subscribe()

        async def events():
            try:
                while True:
                    snapshot = await queue.get()
                    yield f"event: snapshot\ndata: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
            finally:
                download_manager.unsubscribe(queue)

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.get("/api/proxy/image")
    async def proxy_image(url: str):
        content, content_type = await scraper.fetch_bytes(url, "https://hanime1.me/")
        return Response(content, media_type=content_type, headers={"Cache-Control": "public, max-age=86400"})

    @app.get("/api/proxy/history-cover")
    async def proxy_history_cover(url: str, thumbnail: str = ""):
        target = thumbnail or url
        content, content_type = await scraper.fetch_bytes(target, "https://hanime1.me/")
        return Response(content, media_type=content_type, headers={"Cache-Control": "public, max-age=86400"})

    @app.get("/api/proxy/video")
    async def proxy_video(url: str, request: Request):
        body, status_code, content_type, response_headers = await scraper.stream_bytes(
            url,
            "https://hanime1.me/",
            request.headers.get("range"),
        )
        response_headers["Cache-Control"] = "public, max-age=300"
        return StreamingResponse(body, status_code=status_code, media_type=content_type, headers=response_headers)

    @app.get("/api/local-cover/{task_id}")
    async def local_cover(task_id: str):
        raise HTTPException(status_code=404, detail="local cover not found")

    static_path = static_dir()
    if static_path.exists():
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

    return app


async def call_download(factory):
    try:
        return await factory()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def log_cookie_task_result(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        log.warning("Cookie 自动刷新失败: %s", exc)


def require_text(payload: dict, key: str, message: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail=message)
    return value


async def resolve_video_payload(payload: dict, scraper) -> dict:
    parsed = dict(payload)
    if (not parsed.get("csrfToken") or not parsed.get("myList")) and parsed.get("pageUrl"):
        parsed.update(await scraper.parse(str(parsed.get("pageUrl"))))
    return parsed


async def resolve_token(payload: dict, scraper) -> str:
    parsed = await resolve_video_payload(payload, scraper)
    return require_text(parsed, "csrfToken", "缺少 CSRF token")


def default_search_options() -> dict:
    return {
        "types": ["裏番", "泡麵番", "Motion Anime", "3DCG", "2.5D", "2D動畫", "AI生成", "MMD", "Cosplay"],
        "genres": ["裏番", "泡麵番", "Motion Anime", "3DCG", "2.5D", "2D動畫", "AI生成", "MMD", "Cosplay"],
        "sorts": ["最新上市", "最新上傳", "本日排行", "本周排行", "本月排行", "觀看次數", "點讚比例", "時長最長", "他們在看"],
        "dates": ["過去 24 小時", "過去 2 天", "過去 1 周", "過去 1 個月", "過去 3 個月", "過去 1 年"],
        "durations": ["1 分鐘 +", "5 分鐘 +", "10 分鐘 +", "20 分鐘 +", "30 分鐘 +", "60 分鐘 +", "0 - 10 分鐘", "0 - 20 分鐘"],
        "tagGroups": [],
    }


app = create_app()
