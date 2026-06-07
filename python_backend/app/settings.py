from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .local_db import LocalStore


@dataclass
class AppSettings:
    downloadDirectory: str | None = None
    maxConcurrentDownloads: int = 3
    gopeedHost: str = "127.0.0.1"
    gopeedPort: int = 9999
    gopeedToken: str = ""
    gopeedConnections: int = 16
    pageCacheLimit: int = 20
    shortcutBack: str = "Alt+ArrowLeft"
    shortcutForward: str = "Alt+ArrowRight"

    def __post_init__(self) -> None:
        if not self.downloadDirectory:
            self.downloadDirectory = str(Path.home() / "Downloads" / "Hanime")
        self.maxConcurrentDownloads = clamp(self.maxConcurrentDownloads, 1, 12, 3)
        self.gopeedPort = clamp(self.gopeedPort, 1, 65535, 9999)
        self.gopeedConnections = clamp(self.gopeedConnections, 1, 128, 16)
        self.gopeedHost = (self.gopeedHost or "127.0.0.1").strip() or "127.0.0.1"
        self.gopeedToken = (self.gopeedToken or "").strip()
        self.pageCacheLimit = clamp(self.pageCacheLimit, 1, 200, 20)
        self.shortcutBack = normalize_shortcut(self.shortcutBack, "Alt+ArrowLeft")
        self.shortcutForward = normalize_shortcut(self.shortcutForward, "Alt+ArrowRight")

    @classmethod
    def from_dict(cls, value: dict) -> "AppSettings":
        return cls(
            downloadDirectory=value.get("downloadDirectory"),
            maxConcurrentDownloads=value.get("maxConcurrentDownloads", 3),
            gopeedHost=value.get("gopeedHost", "127.0.0.1"),
            gopeedPort=value.get("gopeedPort", 9999),
            gopeedToken=value.get("gopeedToken", ""),
            gopeedConnections=value.get("gopeedConnections", 16),
            pageCacheLimit=value.get("pageCacheLimit", 20),
            shortcutBack=value.get("shortcutBack", "Alt+ArrowLeft"),
            shortcutForward=value.get("shortcutForward", "Alt+ArrowRight"),
        )

    def to_dict(self) -> dict:
        return asdict(self)


class SettingsStore:
    def __init__(self, home: Path):
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.home / "settings.json"
        self.history_file = self.home / "download-history.json"
        self.local_store = LocalStore(self.home)

    def load(self) -> AppSettings:
        if self.settings_file.exists():
            try:
                return AppSettings.from_dict(json.loads(self.settings_file.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
        settings = AppSettings()
        self.save(settings)
        return settings

    def save(self, settings: AppSettings) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        self.settings_file.write_text(json.dumps(settings.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def load_history(self) -> list[dict]:
        stored = self.local_store.load_download_history()
        if stored:
            return stored
        if not self.history_file.exists():
            return []
        try:
            value = json.loads(self.history_file.read_text(encoding="utf-8"))
            history = value if isinstance(value, list) else []
            if history:
                self.local_store.save_download_history(history)
            return history
        except json.JSONDecodeError:
            return []

    def save_history(self, history: list[dict]) -> None:
        self.local_store.save_download_history(history)


def clamp(value: int, minimum: int, maximum: int, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    if parsed < minimum or parsed > maximum:
        return fallback if parsed < minimum or parsed > maximum and maximum == 65535 else min(max(parsed, minimum), maximum)
    return parsed


def normalize_shortcut(value: str, fallback: str) -> str:
    value = str(value or "").strip()
    return value if value else fallback
