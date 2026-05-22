from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIR_NAME = "HanimeMediaCenter"


def app_home(override: str | Path | None = None) -> Path:
    if override:
        return ensure_dir(Path(override))
    env_override = os.environ.get("HANIME_APP_HOME")
    if env_override:
        return ensure_dir(Path(env_override))
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return ensure_dir(Path(local_app_data) / APP_DIR_NAME)
    return ensure_dir(Path.home() / f".{APP_DIR_NAME}")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def static_dir() -> Path:
    return project_root() / "src" / "main" / "resources" / "static"
