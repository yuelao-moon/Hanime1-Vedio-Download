from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from time import time
from uuid import uuid4


class DownloadStatus(StrEnum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    DOWNLOADING = "DOWNLOADING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class DownloadRequestItem:
    title: str = ""
    pageUrl: str = ""
    downloadUrl: str = ""
    thumbnail: str = ""

    @classmethod
    def from_dict(cls, value: dict) -> "DownloadRequestItem":
        return cls(
            title=value.get("title") or "",
            pageUrl=value.get("pageUrl") or "",
            downloadUrl=value.get("downloadUrl") or "",
            thumbnail=value.get("thumbnail") or "",
        )


@dataclass
class DownloadTask:
    request: DownloadRequestItem
    status: DownloadStatus = DownloadStatus.QUEUED
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    pageUrl: str = ""
    downloadUrl: str = ""
    thumbnail: str = ""
    fileName: str = ""
    filePath: str = ""
    progressPercent: float = 0.0
    completedAmount: int = 0
    totalAmount: int = 0
    errorMessage: str | None = None
    createdAt: str = field(default_factory=lambda: iso_now())
    startedAt: str | None = None
    finishedAt: str | None = None
    gopeedTaskId: str = ""
    paused: bool = False
    cancelled: bool = False

    def __post_init__(self) -> None:
        self.title = self.title or self.request.title
        self.pageUrl = self.pageUrl or self.request.pageUrl
        self.downloadUrl = self.downloadUrl or self.request.downloadUrl
        self.thumbnail = self.thumbnail or self.request.thumbnail

    def to_view(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "pageUrl": self.pageUrl,
            "downloadUrl": self.downloadUrl,
            "thumbnail": self.thumbnail,
            "fileName": self.fileName,
            "filePath": self.filePath,
            "status": self.status.value,
            "progressPercent": self.progressPercent,
            "completedAmount": self.completedAmount,
            "totalAmount": self.totalAmount,
            "errorMessage": self.errorMessage,
            "createdAt": self.createdAt,
            "startedAt": self.startedAt,
            "finishedAt": self.finishedAt,
        }


def iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(time(), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def existing_nonempty(path: str | Path) -> bool:
    candidate = Path(path)
    return candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0
