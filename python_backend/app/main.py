from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .downloads import DownloadManager
from .browsers import default_browser_channel, detect_browsers
from .models import DownloadRequestItem
from .paths import app_home as resolve_app_home, static_dir
from .scraper import HanimeScraper, SessionBlockedError
from .settings import AppSettings, SettingsStore


def create_app(app_home: str | Path | None = None, scraper=None) -> FastAPI:
    home = resolve_app_home(app_home)
    settings_store = SettingsStore(home)
    scraper = scraper or HanimeScraper(home=home, settings_provider=settings_store.load)
    download_manager = DownloadManager(settings_store, resolver=lambda item: scraper.parse(item.pageUrl))

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            await download_manager.close()
            close = getattr(scraper, "close", None)
            if close:
                await close()

    app = FastAPI(title="Hanime Media Center Python Backend", lifespan=lifespan)
    app.state.settings_store = settings_store
    app.state.scraper = scraper
    app.state.download_manager = download_manager

    @app.exception_handler(SessionBlockedError)
    async def session_blocked_handler(_request: Request, exc: SessionBlockedError):
        return PlainTextResponse(str(exc), status_code=503)

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

    @app.get("/api/browsers")
    async def browsers():
        return {
            "defaultChannel": default_browser_channel(),
            "choices": [choice.to_dict() for choice in detect_browsers()],
        }

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

    @app.post("/api/settings/clear-cache")
    async def clear_cache():
        return await download_manager.clear_history()

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
