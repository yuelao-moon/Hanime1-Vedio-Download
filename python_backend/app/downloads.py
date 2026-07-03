from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Awaitable, Callable

import httpx

from .models import DownloadRequestItem, DownloadStatus, DownloadTask, iso_now
from .parser import build_file_name
from .settings import AppSettings, SettingsStore


Resolver = Callable[[DownloadRequestItem], Awaitable[dict]]


def create_snapshot(tasks: list[DownloadTask], history: list[dict]) -> dict:
    return {
        "activeTasks": [task.to_view() for task in tasks if task.status in {DownloadStatus.PREPARING, DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED}],
        "queuedTasks": [task.to_view() for task in tasks if task.status == DownloadStatus.QUEUED],
        "historyTasks": history,
    }


def gopeed_task_body(download_url: str, target_file: Path, connections: int) -> dict:
    return {
        "req": {"url": download_url},
        "opts": {
            "path": str(target_file.parent),
            "name": target_file.name,
            "extra": {"connections": connections},
        },
    }


class GopeedClient:
    def __init__(self, settings: AppSettings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self.client = client or httpx.AsyncClient(timeout=15)
        self._owns_client = client is None

    @property
    def base_url(self) -> str:
        return f"http://{self.settings.gopeedHost}:{self.settings.gopeedPort}"

    def headers(self) -> dict:
        return {"X-API-Token": self.settings.gopeedToken} if self.settings.gopeedToken else {}

    async def create_task(self, download_url: str, target_file: Path) -> str:
        body = gopeed_task_body(download_url, target_file, self.settings.gopeedConnections)
        response = await self.client.post(f"{self.base_url}/api/v1/tasks", json=body, headers=self.headers())
        response.raise_for_status()
        data = response.json()
        return find_text(data, "data") or find_text(data, "id") or find_text(data, "gid") or find_text(data, "taskId") or ""

    async def read_task(self, task_id: str) -> dict:
        response = await self.client.get(f"{self.base_url}/api/v1/tasks/{task_id}", headers=self.headers())
        response.raise_for_status()
        return response.json()

    async def stop_task(self, task_id: str) -> None:
        response = await self.client.delete(f"{self.base_url}/api/v1/tasks/{task_id}", headers=self.headers())
        # Gopeed returns 404 when a task has already finished or been removed.
        # That is equivalent to the requested terminal state for our queue.
        if response.status_code != 404:
            response.raise_for_status()

    async def pause_task(self, task_id: str) -> None:
        await self.task_action(task_id, "pause")

    async def resume_task(self, task_id: str) -> None:
        await self.task_action(task_id, "continue")

    async def task_action(self, task_id: str, action: str) -> None:
        response = await self.client.put(f"{self.base_url}/api/v1/tasks/{task_id}/{action}", headers=self.headers())
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError:
            return
        if isinstance(data, dict) and data.get("code") not in (None, 0, 200):
            raise ValueError(data.get("msg") or f"Gopeed {action} 操作失败")

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()


class DownloadManager:
    def __init__(self, settings_store: SettingsStore, resolver: Resolver | None = None, gopeed_client: GopeedClient | None = None):
        self.settings_store = settings_store
        self.settings = settings_store.load()
        self.resolver = resolver
        self.gopeed_client = gopeed_client or GopeedClient(self.settings)
        self.tasks: list[DownloadTask] = []
        self.history = settings_store.load_history()
        self.subscribers: set[asyncio.Queue] = set()
        self.worker_task: asyncio.Task | None = None
        self.closed = False

    def snapshot(self) -> dict:
        return create_snapshot(self.tasks, self.history)

    async def enqueue(self, items: list[DownloadRequestItem]) -> dict:
        for item in items:
            self.tasks.append(DownloadTask(request=item))
        self.ensure_worker()
        await self.broadcast()
        return self.snapshot()

    async def pause_task(self, task_id: str) -> dict:
        task = self.require_task(task_id)
        await self.pause_remote_task(task)
        task.paused = True
        task.status = DownloadStatus.PAUSED
        await self.broadcast()
        return self.snapshot()

    async def resume_task(self, task_id: str) -> dict:
        task = self.require_task(task_id)
        await self.resume_remote_task(task)
        task.paused = False
        if task.status == DownloadStatus.PAUSED:
            task.status = DownloadStatus.QUEUED
        self.ensure_worker()
        await self.broadcast()
        return self.snapshot()

    async def cancel_task(self, task_id: str) -> dict:
        task = self.require_task(task_id)
        await self.stop_remote_task(task)
        task.cancelled = True
        task.status = DownloadStatus.CANCELLED
        task.finishedAt = iso_now()
        self.tasks = [candidate for candidate in self.tasks if candidate.id != task_id]
        self.add_history(task)
        await self.broadcast()
        return self.snapshot()

    async def pause_all(self) -> dict:
        for task in self.tasks:
            task.paused = True
            task.status = DownloadStatus.PAUSED
        await self.broadcast()
        return self.snapshot()

    async def cancel_all(self) -> dict:
        for task in list(self.tasks):
            await self.stop_remote_task(task)
            task.cancelled = True
            task.status = DownloadStatus.CANCELLED
            task.finishedAt = iso_now()
            self.add_history(task)
        self.tasks.clear()
        await self.broadcast()
        return self.snapshot()

    async def retry_task(self, task_id: str) -> dict:
        item = next((value for value in self.history if value.get("id") == task_id), None)
        if not item:
            raise ValueError("未找到可重试的历史任务")
        self.history = [value for value in self.history if value.get("id") != task_id]
        self.settings_store.save_history(self.history)
        return await self.enqueue([DownloadRequestItem.from_dict(item)])

    async def retry_all_failed(self) -> dict:
        failed = [item for item in self.history if item.get("status") != DownloadStatus.COMPLETED.value]
        if not failed:
            raise ValueError("没有可重试的任务")
        self.history = [item for item in self.history if item not in failed]
        self.settings_store.save_history(self.history)
        return await self.enqueue([DownloadRequestItem.from_dict(item) for item in failed])

    async def clear_history(self) -> dict:
        self.history = []
        self.settings_store.save_history(self.history)
        await self.broadcast()
        return self.snapshot()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(queue)
        queue.put_nowait(self.snapshot())
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self.subscribers.discard(queue)

    def ensure_worker(self) -> None:
        if self.worker_task is None or self.worker_task.done():
            try:
                self.worker_task = asyncio.create_task(self.run_loop())
            except RuntimeError:
                pass

    async def run_loop(self) -> None:
        while not self.closed:
            queued = [task for task in self.tasks if task.status == DownloadStatus.QUEUED and not task.paused]
            active = [task for task in self.tasks if task.status in {DownloadStatus.PREPARING, DownloadStatus.DOWNLOADING}]
            if not queued or len(active) >= self.settings.maxConcurrentDownloads:
                await asyncio.sleep(0.2)
                if not self.tasks:
                    return
                continue
            asyncio.create_task(self.process(queued[0]))
            await asyncio.sleep(0)

    async def process(self, task: DownloadTask) -> None:
        try:
            task.status = DownloadStatus.PREPARING
            task.startedAt = iso_now()
            await self.broadcast()
            if not task.downloadUrl and self.resolver:
                parsed = await self.resolver(task.request)
                task.title = parsed.get("title") or task.title or "video"
                task.downloadUrl = parsed.get("videoUrl") or ""
                task.thumbnail = parsed.get("thumbnail") or task.thumbnail
            if task.cancelled:
                return
            if not task.downloadUrl:
                raise ValueError("缺少下载地址")
            task.fileName = build_file_name(task.title, task.downloadUrl)
            target = Path(self.settings.downloadDirectory or ".") / task.fileName
            target.parent.mkdir(parents=True, exist_ok=True)
            task.filePath = str(target)
            while not task.cancelled:
                if task.paused:
                    await asyncio.sleep(0.2)
                    continue
                task.status = DownloadStatus.DOWNLOADING
                await self.broadcast()
                if not task.gopeedTaskId:
                    task.gopeedTaskId = await self.gopeed_client.create_task(task.downloadUrl, target)
                # A user may pause or cancel while create_task is in flight.
                # Stop the newly-created remote task before acting on its state.
                if task.cancelled:
                    await self.stop_remote_task(task)
                    continue
                if task.paused:
                    await self.pause_remote_task(task)
                    continue
                completed = await self.poll_gopeed(task, target)
                if completed:
                    break
            if task.cancelled:
                return
            task.status = DownloadStatus.COMPLETED
            task.progressPercent = 100
            task.finishedAt = iso_now()
        except Exception as exc:
            task.status = DownloadStatus.FAILED
            task.errorMessage = str(exc)
            task.finishedAt = iso_now()
        finally:
            # cancel_task/cancel_all may already have moved this task to history
            # while its background coroutine was awaiting Gopeed.
            if any(candidate.id == task.id for candidate in self.tasks):
                self.tasks = [candidate for candidate in self.tasks if candidate.id != task.id]
                self.add_history(task)
            await self.broadcast()

    async def poll_gopeed(self, task: DownloadTask, target: Path) -> bool:
        while not task.cancelled and not task.paused:
            data = await self.gopeed_client.read_task(task.gopeedTaskId)
            task.completedAmount = find_int(data, "downloaded") or find_int(data, "downloadedSize") or find_int(data, "completed") or 0
            task.totalAmount = find_int(data, "total") or find_int(data, "totalSize") or find_int(data, "size") or 0
            task.progressPercent = (task.completedAmount * 100 / task.totalAmount) if task.totalAmount else 0
            state = (find_text(data, "status") or find_text(data, "state") or "").lower()
            if any(word in state for word in ("done", "complete", "finish", "success")):
                return True
            if any(word in state for word in ("fail", "error")):
                raise ValueError(find_text(data, "error") or find_text(data, "message") or "Gopeed 下载失败")
            await self.broadcast()
            await asyncio.sleep(1)
        return False

    async def stop_remote_task(self, task: DownloadTask) -> None:
        if not task.gopeedTaskId:
            return
        await self.gopeed_client.stop_task(task.gopeedTaskId)
        # A deleted Gopeed task cannot be polled or resumed.  Resume creates a
        # fresh task for the same destination (Gopeed can reuse partial data).
        task.gopeedTaskId = ""

    async def pause_remote_task(self, task: DownloadTask) -> None:
        if task.gopeedTaskId:
            await self.gopeed_client.pause_task(task.gopeedTaskId)

    async def resume_remote_task(self, task: DownloadTask) -> None:
        if task.gopeedTaskId:
            await self.gopeed_client.resume_task(task.gopeedTaskId)

    def add_history(self, task: DownloadTask) -> None:
        view = task.to_view()
        self.history = [item for item in self.history if item.get("title") != view.get("title")]
        self.history.insert(0, view)
        self.history = self.history[:50]
        self.settings_store.save_history(self.history)

    def require_task(self, task_id: str) -> DownloadTask:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise ValueError("任务不存在或已结束")

    async def broadcast(self) -> None:
        snapshot = self.snapshot()
        for queue in list(self.subscribers):
            await queue.put(snapshot)

    async def close(self) -> None:
        self.closed = True
        if self.worker_task:
            self.worker_task.cancel()
        await self.gopeed_client.close()


def find_text(value, key: str) -> str:
    found = find_value(value, key)
    return str(found) if found not in (None, "") else ""


def find_int(value, key: str) -> int:
    found = find_value(value, key)
    try:
        return int(found)
    except (TypeError, ValueError):
        return 0


def find_value(value, key: str):
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = find_value(child, key)
            if found not in (None, ""):
                return found
    if isinstance(value, list):
        for child in value:
            found = find_value(child, key)
            if found not in (None, ""):
                return found
    return None


class contextlib_suppress:
    def __enter__(self):
        return None

    def __exit__(self, *_exc):
        return True
