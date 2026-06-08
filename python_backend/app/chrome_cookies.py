"""Cookie cache for CF clearance used by HTTP requests."""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_COOKIE_FILE = "cf_cookies.json"


def save_cookies(cookies: list[dict], home: Path, user_agent: str | None = None) -> None:
    """Persist a list of cookie dicts to disk."""
    path = home / _COOKIE_FILE
    try:
        with open(path, "w", encoding="utf-8") as f:
            payload = {"saved_at": time.time(), "cookies": cookies}
            if user_agent:
                payload["user_agent"] = user_agent
            json.dump(payload, f)
        cf_count = sum(1 for c in cookies if c.get("name") == "cf_clearance")
        log.info("已保存 %d 个 cookies（cf_clearance: %d）到 %s", len(cookies), cf_count, path)
    except Exception as exc:
        log.warning("无法保存 cookies: %s", exc)


def load_cookie_cache(home: Path) -> dict:
    path = home / _COOKIE_FILE
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log.debug("读取 cookie 缓存失败: %s", exc)
        return {}


def load_cookies(home: Path) -> list[dict]:
    """
    Load cookies from the on-disk cache.
    Returns valid (non-expired) cookies, or empty list if cache is missing.
    Relies on individual cookie `expires` timestamps rather than a hard file-age limit.
    """
    path = home / _COOKIE_FILE
    if not path.exists():
        return []
    try:
        data = load_cookie_cache(home)
        cookies = data.get("cookies", [])
        now = time.time()
        # Filter out cookies with a past expiry; keep session cookies (expires == -1 or 0).
        valid = [c for c in cookies
                 if not c.get("expires") or c["expires"] == -1 or c["expires"] > now]
        cf_count = sum(1 for c in valid if c.get("name") == "cf_clearance")
        if cf_count == 0:
            log.debug("Cookie 缓存中没有有效的 cf_clearance（共 %d 个有效 cookies）", len(valid))
        else:
            log.debug("从缓存加载了 %d 个 cookies（cf_clearance: %d）", len(valid), cf_count)
        return valid
    except Exception as exc:
        log.debug("读取 cookie 缓存失败: %s", exc)
        return []


def load_user_agent(home: Path) -> str:
    data = load_cookie_cache(home)
    return str(data.get("user_agent") or "")


def cookies_to_jar(cookies: list[dict]) -> dict[str, str]:
    """Convert a list of cookie dicts to a {name: value} dict."""
    return {c["name"]: c["value"] for c in cookies if c.get("value")}


def cookies_for_host(cookies: list[dict], host: str) -> list[dict]:
    normalized_host = (host or "").lstrip(".").lower()
    result = []
    for cookie in cookies:
        domain = str(cookie.get("domain") or "").lstrip(".").lower()
        if not domain:
            continue
        if normalized_host == domain or normalized_host.endswith("." + domain):
            result.append(cookie)
    return result


def cookies_to_header(cookies: list[dict]) -> str:
    pairs = []
    for cookie in cookies:
        name = cookie.get("name")
        value = cookie.get("value")
        if name and value:
            pairs.append(f"{name}={value}")
    return "; ".join(pairs)
