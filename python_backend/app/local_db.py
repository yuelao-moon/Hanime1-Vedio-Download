from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class LocalStore:
    def __init__(self, home: str | Path):
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        self.path = self.home / "hanime_media_center.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS page_cache (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    scroll_y INTEGER NOT NULL DEFAULT 0,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS download_history (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS watch_history (
                    video_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    watched_at INTEGER NOT NULL
                )
                """
            )

    def set_page_cache(self, key: str, data: Any, scroll_y: int = 0) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO page_cache(key, data, scroll_y, updated_at)
                VALUES(?, ?, ?, unixepoch())
                ON CONFLICT(key) DO UPDATE SET
                    data=excluded.data,
                    scroll_y=excluded.scroll_y,
                    updated_at=excluded.updated_at
                """,
                (key, json.dumps(data, ensure_ascii=False), int(scroll_y or 0)),
            )

    def get_page_cache(self, key: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT data, scroll_y, updated_at FROM page_cache WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        return {
            "data": json.loads(row["data"]),
            "scrollY": row["scroll_y"],
            "updatedAt": row["updated_at"],
        }

    def clear_page_cache(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM page_cache")

    def save_download_history(self, history: list[dict]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM download_history")
            for index, item in enumerate(history):
                item_id = str(item.get("id") or item.get("title") or index)
                conn.execute(
                    "INSERT INTO download_history(id, data, created_at) VALUES(?, ?, ?)",
                    (item_id, json.dumps(item, ensure_ascii=False), index),
                )

    def load_download_history(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM download_history ORDER BY created_at").fetchall()
        return [json.loads(row["data"]) for row in rows]

    def clear_local_cache(self) -> None:
        self.clear_page_cache()

    def record_watch_history(self, item: dict) -> dict:
        video_id = str(item.get("videoId") or "").strip()
        if not video_id:
            raise ValueError("缺少视频 ID")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO watch_history(video_id, data, watched_at)
                VALUES(?, ?, unixepoch())
                ON CONFLICT(video_id) DO UPDATE SET
                    data=excluded.data,
                    watched_at=excluded.watched_at
                """,
                (video_id, json.dumps(item, ensure_ascii=False)),
            )
        return item

    def load_watch_history(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT data FROM watch_history ORDER BY watched_at DESC LIMIT ?",
                (int(limit or 100),),
            ).fetchall()
        return [json.loads(row["data"]) for row in rows]
