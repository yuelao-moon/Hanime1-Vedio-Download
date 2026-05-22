from __future__ import annotations

import shutil
import os
from dataclasses import asdict, dataclass
from pathlib import Path


SUPPORTED_CHANNELS = ("msedge", "chrome", "chromium")


@dataclass(frozen=True)
class BrowserChoice:
    channel: str
    label: str
    available: bool

    def to_dict(self) -> dict:
        return asdict(self)


def detect_browsers() -> list[BrowserChoice]:
    return [
        BrowserChoice("msedge", "Microsoft Edge", executable_exists("msedge") or executable_exists("msedge.exe")),
        BrowserChoice("chrome", "Google Chrome", executable_exists("chrome") or executable_exists("chrome.exe")),
        BrowserChoice("chromium", "Bundled Chromium", True),
    ]


def default_browser_channel() -> str:
    for choice in detect_browsers():
        if choice.available:
            return choice.channel
    return "chromium"


def normalize_browser_channel(value: str | None) -> str:
    return value if value in SUPPORTED_CHANNELS else "msedge"


def executable_exists(name: str) -> bool:
    if shutil.which(name) is not None:
        return True
    executable = name if name.endswith(".exe") else f"{name}.exe"
    for root in windows_browser_roots():
        for relative in known_browser_paths(executable):
            if (root / relative).exists():
                return True
    return False


def windows_browser_roots() -> list[Path]:
    roots = []
    for key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        value = os.environ.get(key)
        if value:
            roots.append(Path(value))
    return roots


def known_browser_paths(executable: str) -> list[Path]:
    if executable == "msedge.exe":
        return [Path("Microsoft/Edge/Application/msedge.exe")]
    if executable == "chrome.exe":
        return [Path("Google/Chrome/Application/chrome.exe")]
    return [Path(executable)]
