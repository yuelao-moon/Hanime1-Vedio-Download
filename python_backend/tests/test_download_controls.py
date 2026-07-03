from __future__ import annotations

import pytest

from python_backend.app.downloads import DownloadManager
from python_backend.app.models import DownloadRequestItem, DownloadStatus, DownloadTask
from python_backend.app.settings import SettingsStore


class FakeGopeed:
    def __init__(self):
        self.stopped: list[str] = []
        self.paused: list[str] = []
        self.resumed: list[str] = []

    async def stop_task(self, task_id: str) -> None:
        self.stopped.append(task_id)

    async def pause_task(self, task_id: str) -> None:
        self.paused.append(task_id)

    async def resume_task(self, task_id: str) -> None:
        self.resumed.append(task_id)

    async def close(self) -> None:
        pass


def active_task() -> DownloadTask:
    task = DownloadTask(request=DownloadRequestItem(title="video"))
    task.status = DownloadStatus.DOWNLOADING
    task.gopeedTaskId = "gopeed-1"
    return task


@pytest.mark.asyncio
async def test_pause_uses_the_remote_gopeed_pause_action(tmp_path):
    gopeed = FakeGopeed()
    manager = DownloadManager(SettingsStore(tmp_path), gopeed_client=gopeed)
    task = active_task()
    manager.tasks.append(task)

    await manager.pause_task(task.id)

    assert gopeed.paused == ["gopeed-1"]
    assert gopeed.stopped == []
    assert task.status is DownloadStatus.PAUSED
    assert task.gopeedTaskId == "gopeed-1"


@pytest.mark.asyncio
async def test_resume_uses_the_same_remote_gopeed_task(tmp_path):
    gopeed = FakeGopeed()
    manager = DownloadManager(SettingsStore(tmp_path), gopeed_client=gopeed)
    task = active_task()
    task.paused = True
    task.status = DownloadStatus.PAUSED
    manager.tasks.append(task)

    await manager.resume_task(task.id)

    assert gopeed.resumed == ["gopeed-1"]
    assert task.gopeedTaskId == "gopeed-1"
    assert task.status is DownloadStatus.QUEUED


@pytest.mark.asyncio
async def test_cancel_stops_remote_task_before_recording_history(tmp_path):
    gopeed = FakeGopeed()
    manager = DownloadManager(SettingsStore(tmp_path), gopeed_client=gopeed)
    task = active_task()
    manager.tasks.append(task)

    await manager.cancel_task(task.id)

    assert gopeed.stopped == ["gopeed-1"]
    assert manager.tasks == []
    assert manager.history[0]["status"] == DownloadStatus.CANCELLED.value
