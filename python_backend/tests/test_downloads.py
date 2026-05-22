import asyncio
from pathlib import Path

import pytest

from app.downloads import DownloadManager, GopeedClient, create_snapshot, gopeed_task_body
from app.models import DownloadRequestItem, DownloadStatus, DownloadTask
from app.settings import AppSettings, SettingsStore


def test_create_snapshot_splits_active_and_queued_tasks():
    active = DownloadTask(request=DownloadRequestItem(title="A", pageUrl="u1"), status=DownloadStatus.DOWNLOADING)
    queued = DownloadTask(request=DownloadRequestItem(title="B", pageUrl="u2"), status=DownloadStatus.QUEUED)

    snapshot = create_snapshot([active, queued], [])

    assert snapshot["activeTasks"][0]["title"] == "A"
    assert snapshot["queuedTasks"][0]["title"] == "B"
    assert snapshot["historyTasks"] == []


def test_gopeed_task_body_uses_directory_name_and_connections(tmp_path: Path):
    body = gopeed_task_body("https://cdn.test/a.mp4", tmp_path / "Video.mp4", 16)

    assert body["req"]["url"] == "https://cdn.test/a.mp4"
    assert body["opts"]["path"] == str(tmp_path)
    assert body["opts"]["name"] == "Video.mp4"
    assert body["opts"]["extra"]["connections"] == 16


@pytest.mark.asyncio
async def test_download_manager_enqueue_adds_queued_task(tmp_path: Path):
    settings_store = SettingsStore(tmp_path)
    settings = AppSettings(downloadDirectory=str(tmp_path / "downloads"))
    settings_store.save(settings)
    manager = DownloadManager(settings_store, gopeed_client=GopeedClient(settings))

    snapshot = await manager.enqueue([DownloadRequestItem(title="T", pageUrl="p", downloadUrl="https://cdn/a.mp4")])

    assert snapshot["queuedTasks"][0]["title"] == "T"
    await manager.close()
