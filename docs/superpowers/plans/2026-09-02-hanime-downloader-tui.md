# Hanime Downloader Linux Terminal App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent `uv`-managed, browser-free terminal application that saves Hanime1 cookies and settings, then downloads one video, comma-separated videos, or a page-defined series on Linux.

**Architecture:** Create a self-contained project under `hanime_downloader_cli/` and leave the existing FastAPI desktop application unchanged. Separate settings, cookie storage, site requests, pure HTML parsing, HTTP/FFmpeg download backends, concurrent orchestration, and the interactive terminal menu behind explicit typed interfaces.

**Tech Stack:** Python 3.11+, uv, curl-cffi, selectolax, httpx, Rich, pytest, pytest-asyncio, system FFmpeg for M3U8 only.

**Spec:** `docs/superpowers/specs/2026-09-02-hanime-downloader-tui-design.md`

## Global Constraints

- The new project lives at `hanime_downloader_cli/` and must not replace or refactor the existing Windows desktop app.
- Runtime requires Python 3.11 or newer and is managed by `uv` with a committed `uv.lock`.
- There is one interactive entry point: `uv run hanime-downloader`.
- The program accepts only HTTP(S) Hanime1 video page URLs in the first release.
- No FastAPI, HTML/JavaScript/CSS frontend, Playwright, Chromium, browser automation, Gopeed, account features, or comment features.
- Download concurrency means simultaneous video tasks, must default to `3`, and must be constrained to `1` through `16`.
- HTTP/HTTPS proxies are supported; SOCKS proxies are not supported.
- Hanime1 Cookie values must never be logged and must never be sent to third-party media hosts or FFmpeg.
- MP4/ordinary URLs use the built-in async downloader; M3U8 uses system FFmpeg with stream copy and no transcoding.
- All persistent writes use same-directory temporary files followed by atomic replacement.
- User-facing text and errors are Chinese; internal identifiers use English `snake_case`.
- Implement every behavioral change test-first and make the commit listed at the end of each task only after its focused tests pass.

---

## File Map

Files created by this plan:

```text
hanime_downloader_cli/
├── .gitignore                         # Local uv/test/download artifacts
├── pyproject.toml                     # Package metadata, dependencies, entry point, pytest config
├── uv.lock                            # Reproducible dependency lock
├── README.md                          # Linux installation, operation, Cookie, proxy and FFmpeg guide
├── src/hanime_downloader/
│   ├── __init__.py                    # Package version
│   ├── cli.py                         # Interactive menus and batch presentation
│   ├── settings.py                    # XDG paths and validated settings persistence
│   ├── cookies.py                     # Cookie parsing and secret persistence
│   ├── client.py                      # curl-cffi page fetch and Cloudflare detection
│   ├── parser.py                      # Pure video/download/playlist HTML parsing
│   ├── series.py                      # Input normalization and task-list construction
│   ├── downloader.py                  # HTTP downloader, task models and concurrency coordinator
│   └── ffmpeg.py                      # FFmpeg M3U8 adapter
└── tests/
    ├── conftest.py                    # Isolated config/home and real local HTTP fixtures
    ├── fixtures/
    │   └── playlist_407460_snippet.html
    ├── test_settings.py
    ├── test_cookies.py
    ├── test_parser.py
    ├── test_client.py
    ├── test_series.py
    ├── test_http_downloader.py
    ├── test_ffmpeg.py
    ├── test_coordinator.py
    └── test_cli.py
```

No existing application source file is modified. The existing playlist fixture is copied into the new project so `hanime_downloader_cli/` remains portable when moved by itself.

---

### Task 1: Scaffold the uv package and implement validated settings

**Files:**
- Create: `hanime_downloader_cli/pyproject.toml`
- Create: `hanime_downloader_cli/.gitignore`
- Create: `hanime_downloader_cli/src/hanime_downloader/__init__.py`
- Create: `hanime_downloader_cli/src/hanime_downloader/settings.py`
- Create: `hanime_downloader_cli/tests/test_settings.py`
- Create: `hanime_downloader_cli/uv.lock`

**Interfaces:**
- Produces: `AppSettings(download_directory: str = "./downloads", concurrent_downloads: int = 3, proxy_enabled: bool = False, proxy_url: str = "")`.
- Produces: `SettingsLoad(settings: AppSettings, warning: str | None)`.
- Produces: `config_directory(environ: Mapping[str, str] | None = None, home: Path | None = None) -> Path`.
- Produces: `SettingsStore(path: Path | None = None)` with `load() -> SettingsLoad` and `save(settings: AppSettings) -> None`.

- [ ] **Step 1: Initialize the package metadata and declare exact dependency ranges**

Run from the repository root. `--bare` ensures uv creates only the project metadata, so the package name and source layout below are deliberate rather than derived from the directory name:

```powershell
uv init --bare --python 3.11 --vcs none --no-workspace hanime_downloader_cli
```

Replace the generated `pyproject.toml` with:

```toml
[project]
name = "hanime-downloader"
version = "0.1.0"
description = "Browser-free Hanime1 terminal downloader"
requires-python = ">=3.11"
dependencies = [
    "curl-cffi>=0.7,<1",
    "httpx>=0.27,<1",
    "rich>=13,<15",
    "selectolax>=0.3,<1",
]

[project.scripts]
hanime-downloader = "hanime_downloader.cli:main"

[dependency-groups]
dev = [
    "pytest>=8,<9",
    "pytest-asyncio>=0.24,<1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

Create `.gitignore`:

```gitignore
.venv/
.pytest_cache/
__pycache__/
*.py[cod]
downloads/
```

Create `src/hanime_downloader/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 2: Write failing settings tests**

Create `tests/test_settings.py` with tests for XDG selection, defaults, validation, round-trip persistence, atomic overwrite, and corrupt-file fallback:

```python
import json
from pathlib import Path

import pytest

from hanime_downloader.settings import (
    AppSettings,
    SettingsStore,
    config_directory,
)


def test_config_directory_prefers_xdg(tmp_path: Path):
    result = config_directory(
        environ={"XDG_CONFIG_HOME": str(tmp_path / "xdg")},
        home=tmp_path / "home",
    )
    assert result == tmp_path / "xdg" / "hanime-downloader"


def test_settings_defaults_and_validation():
    settings = AppSettings()
    assert settings.download_directory == "./downloads"
    assert settings.concurrent_downloads == 3
    assert settings.proxy_enabled is False
    with pytest.raises(ValueError, match="1 到 16"):
        AppSettings(concurrent_downloads=17)
    with pytest.raises(ValueError, match="HTTP/HTTPS"):
        AppSettings(proxy_enabled=True, proxy_url="socks5://127.0.0.1:1080")


def test_settings_store_round_trip_and_replaces_atomically(tmp_path: Path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    expected = AppSettings(
        download_directory="~/Videos/Hanime",
        concurrent_downloads=5,
        proxy_enabled=True,
        proxy_url="http://127.0.0.1:7890",
    )
    store.save(expected)
    loaded = store.load()
    assert loaded.settings == expected
    assert loaded.warning is None
    assert json.loads(path.read_text(encoding="utf-8"))["concurrentDownloads"] == 5
    assert list(tmp_path.glob("settings.json.*.tmp")) == []


def test_corrupt_settings_return_defaults_without_overwrite(tmp_path: Path):
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    loaded = SettingsStore(path).load()
    assert loaded.settings == AppSettings()
    assert "设置文件损坏" in (loaded.warning or "")
    assert path.read_text(encoding="utf-8") == "{broken"
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```powershell
cd hanime_downloader_cli
uv sync
uv run pytest tests/test_settings.py -q
```

Expected: collection fails because `hanime_downloader.settings` does not exist.

- [ ] **Step 4: Implement XDG paths and settings persistence**

Create `settings.py` with immutable dataclasses, URL validation through `urllib.parse.urlsplit`, camel-case JSON keys, UTF-8 JSON, `tempfile.NamedTemporaryFile(delete=False, dir=path.parent)`, `os.fsync`, `os.replace`, and cleanup on failure. The public implementation must match:

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit


@dataclass(frozen=True)
class AppSettings:
    download_directory: str = "./downloads"
    concurrent_downloads: int = 3
    proxy_enabled: bool = False
    proxy_url: str = ""

    def __post_init__(self) -> None:
        if not 1 <= self.concurrent_downloads <= 16:
            raise ValueError("下载线程数必须在 1 到 16 之间")
        if self.proxy_enabled:
            parsed = urlsplit(self.proxy_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("代理地址必须是有效的 HTTP/HTTPS URL")


@dataclass(frozen=True)
class SettingsLoad:
    settings: AppSettings
    warning: str | None = None


def config_directory(
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    values = os.environ if environ is None else environ
    base = Path(values["XDG_CONFIG_HOME"]) if values.get("XDG_CONFIG_HOME") else (home or Path.home()) / ".config"
    return base / "hanime-downloader"


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or config_directory() / "settings.json"

    def load(self) -> SettingsLoad:
        if not self.path.exists():
            return SettingsLoad(AppSettings())
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return SettingsLoad(AppSettings(
                download_directory=str(data.get("downloadDirectory", "./downloads")),
                concurrent_downloads=int(data.get("concurrentDownloads", 3)),
                proxy_enabled=bool(data.get("proxyEnabled", False)),
                proxy_url=str(data.get("proxyUrl", "")),
            ))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return SettingsLoad(AppSettings(), f"设置文件损坏，当前使用默认值: {exc}")

    def save(self, settings: AppSettings) -> None:
        payload = {
            "downloadDirectory": settings.download_directory,
            "concurrentDownloads": settings.concurrent_downloads,
            "proxyEnabled": settings.proxy_enabled,
            "proxyUrl": settings.proxy_url,
        }
        _atomic_json_write(self.path, payload, mode=0o600)


def _atomic_json_write(path: Path, payload: dict, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f"{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        os.chmod(path, mode)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
```

Export `_atomic_json_write` for reuse by `cookies.py` but keep it undocumented as an internal helper.

- [ ] **Step 5: Run focused tests and create the lock file**

Run:

```powershell
uv lock
uv run pytest tests/test_settings.py -q
```

Expected: all settings tests pass and `uv.lock` exists.

- [ ] **Step 6: Commit the scaffold and settings component**

```powershell
git add hanime_downloader_cli
git commit -m "Add uv project and downloader settings"
```

---

### Task 2: Implement secure Cookie parsing and overwrite storage

**Files:**
- Create: `hanime_downloader_cli/src/hanime_downloader/cookies.py`
- Create: `hanime_downloader_cli/tests/test_cookies.py`

**Interfaces:**
- Consumes: `config_directory()` and `_atomic_json_write()` from `settings.py`.
- Produces: `CookieMissingError`.
- Produces: `parse_cookie_header(raw: str) -> dict[str, str]` preserving the last value for duplicate names.
- Produces: `CookieStore(path: Path | None = None)` with `save(raw: str) -> None`, `load() -> dict[str, str]`, and `exists() -> bool`.

- [ ] **Step 1: Write failing Cookie tests**

Create `tests/test_cookies.py`:

```python
import json
import os
from pathlib import Path

import pytest

from hanime_downloader.cookies import (
    CookieMissingError,
    CookieStore,
    parse_cookie_header,
)


def test_parse_cookie_header_trims_and_uses_last_duplicate():
    assert parse_cookie_header(" cf_clearance=abc ; session=one; session=two ") == {
        "cf_clearance": "abc",
        "session": "two",
    }


@pytest.mark.parametrize("raw", ["", "   ", "missing_equals", "=empty-name", "empty="])
def test_parse_cookie_header_rejects_invalid_input(raw: str):
    with pytest.raises(ValueError, match="Cookie"):
        parse_cookie_header(raw)


def test_cookie_store_overwrites_instead_of_merging(tmp_path: Path):
    path = tmp_path / "cookies.json"
    store = CookieStore(path)
    store.save("first=1; stale=old")
    store.save("second=2")
    assert store.load() == {"second": "2"}
    assert "stale" not in path.read_text(encoding="utf-8")
    if os.name == "posix":
        assert path.stat().st_mode & 0o777 == 0o600


def test_cookie_store_missing_is_explicit(tmp_path: Path):
    store = CookieStore(tmp_path / "cookies.json")
    assert store.exists() is False
    with pytest.raises(CookieMissingError, match="保存/更新 Cookie"):
        store.load()


def test_cookie_json_does_not_retain_raw_header_field(tmp_path: Path):
    path = tmp_path / "cookies.json"
    CookieStore(path).save("cf_clearance=secret")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload == {"cookies": {"cf_clearance": "secret"}}
```

- [ ] **Step 2: Run the Cookie tests and verify failure**

Run:

```powershell
uv run pytest tests/test_cookies.py -q
```

Expected: collection fails because `hanime_downloader.cookies` does not exist.

- [ ] **Step 3: Implement Cookie parsing and atomic overwrite**

Create `cookies.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from .settings import _atomic_json_write, config_directory


class CookieMissingError(RuntimeError):
    pass


def parse_cookie_header(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for part in raw.split(";"):
        candidate = part.strip()
        if not candidate:
            continue
        if "=" not in candidate:
            raise ValueError("Cookie 必须使用 name=value 格式")
        name, value = candidate.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name or not value:
            raise ValueError("Cookie 名称和值不能为空")
        parsed[name] = value
    if not parsed:
        raise ValueError("Cookie 不能为空")
    return parsed


class CookieStore:
    def __init__(self, path: Path | None = None):
        self.path = path or config_directory() / "cookies.json"

    def exists(self) -> bool:
        return self.path.is_file()

    def save(self, raw: str) -> None:
        _atomic_json_write(self.path, {"cookies": parse_cookie_header(raw)}, mode=0o600)

    def load(self) -> dict[str, str]:
        if not self.path.is_file():
            raise CookieMissingError("尚未保存 Cookie，请从主菜单选择“保存/更新 Cookie”")
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            cookies = payload["cookies"]
            if not isinstance(cookies, dict):
                raise TypeError("cookies 不是对象")
            return parse_cookie_header("; ".join(f"{name}={value}" for name, value in cookies.items()))
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CookieMissingError(f"Cookie 文件无效，请从主菜单重新保存: {exc}") from exc
```

- [ ] **Step 4: Run focused tests and verify no secret appears in assertion output**

Run:

```powershell
uv run pytest tests/test_cookies.py -q
```

Expected: all Cookie tests pass. Inspect failures produced by deliberately calling `parse_cookie_header("bad")`; the error text must not contain any saved Cookie value.

- [ ] **Step 5: Commit the Cookie component**

```powershell
git add hanime_downloader_cli/src/hanime_downloader/cookies.py hanime_downloader_cli/tests/test_cookies.py
git commit -m "Add secure Cookie storage"
```

---

### Task 3: Implement pure video and series HTML parsing

**Files:**
- Create: `hanime_downloader_cli/src/hanime_downloader/parser.py`
- Create: `hanime_downloader_cli/tests/test_parser.py`
- Copy: `python_backend/tests/fixtures/playlist_407460_snippet.html` to `hanime_downloader_cli/tests/fixtures/playlist_407460_snippet.html`

**Interfaces:**
- Produces: `PlaylistItem(page_url: str, title: str, video_id: str)`.
- Produces: `VideoPage(page_url: str, video_id: str, title: str, media_url: str, playlist: tuple[PlaylistItem, ...])`.
- Produces: `extract_video_page(page_url: str, html: str, download_html: str = "") -> VideoPage`.
- Produces: `build_safe_filename(title: str, media_url: str) -> str`.

- [ ] **Step 1: Copy the existing real-layout fixture into the portable project**

Run from the repository root:

```powershell
New-Item -ItemType Directory -Force hanime_downloader_cli\tests\fixtures | Out-Null
Copy-Item python_backend\tests\fixtures\playlist_407460_snippet.html hanime_downloader_cli\tests\fixtures\playlist_407460_snippet.html
```

- [ ] **Step 2: Write failing parser tests**

Create `tests/test_parser.py`:

```python
from pathlib import Path

from hanime_downloader.parser import build_safe_filename, extract_video_page


def test_download_page_media_takes_priority():
    page = extract_video_page(
        "https://hanime1.me/watch?v=123",
        """
        <html><h1 id="shareBtn-title">Episode / 1</h1>
        <source src="https://cdn.test/fallback.m3u8"></html>
        """,
        """
        <table class="download-table"><tr><td>
        <a data-url="https://cdn.test/final.mp4">download</a>
        </td></tr></table>
        """,
    )
    assert page.video_id == "123"
    assert page.title == "Episode / 1"
    assert page.media_url == "https://cdn.test/final.mp4"


def test_fixture_playlist_keeps_page_order_and_entries_without_images():
    fixture = Path(__file__).parent / "fixtures" / "playlist_407460_snippet.html"
    page = extract_video_page(
        "https://hanime1.me/watch?v=407460",
        fixture.read_text(encoding="utf-8"),
    )
    assert [item.video_id for item in page.playlist] == ["407463", "407460"]
    assert page.playlist[0].title == "鄉下幾乎沒有娛樂活動 2"


def test_parser_rejects_page_without_media():
    try:
        extract_video_page("https://hanime1.me/watch?v=9", "<h1>Missing</h1>")
    except ValueError as exc:
        assert "媒体地址" in str(exc)
    else:
        raise AssertionError("missing media must fail")


def test_safe_filename_removes_path_characters_and_keeps_type():
    assert build_safe_filename("A/B\\C: 01", "https://cdn.test/index.m3u8") == "A_B_C_ 01.mp4"
    assert build_safe_filename("..", "https://cdn.test/video.mp4") == "video.mp4"
```

- [ ] **Step 3: Run parser tests to verify failure**

Run:

```powershell
uv run pytest tests/test_parser.py -q
```

Expected: collection fails because `hanime_downloader.parser` does not exist.

- [ ] **Step 4: Implement only the required pure parser**

Create `parser.py` using `selectolax.parser.HTMLParser`. Port the proven stream and playlist selectors from `python_backend/app/parser.py`, but omit creator, comments, likes, account state, thumbnails, related videos, and browsing helpers. Implement these exact dataclasses and selection order:

```python
from dataclasses import dataclass
import re
from urllib.parse import parse_qs, urljoin, urlparse

from selectolax.parser import HTMLParser


@dataclass(frozen=True)
class PlaylistItem:
    page_url: str
    title: str
    video_id: str


@dataclass(frozen=True)
class VideoPage:
    page_url: str
    video_id: str
    title: str
    media_url: str
    playlist: tuple[PlaylistItem, ...]


def extract_video_page(page_url: str, html: str, download_html: str = "") -> VideoPage:
    media_url = _extract_first_stream(download_html) or _extract_first_stream(html)
    if not media_url:
        raise ValueError("页面中未找到可下载的媒体地址")
    tree = HTMLParser(html or "")
    title_node = tree.css_first("#shareBtn-title, h1")
    title = (title_node.text(strip=True) if title_node else "video").strip() or "video"
    video_id = parse_qs(urlparse(page_url).query).get("v", [""])[0]
    return VideoPage(
        page_url=page_url,
        video_id=video_id,
        title=title,
        media_url=media_url,
        playlist=tuple(_extract_playlist(tree, page_url)),
    )
```

`_extract_first_stream` must check, in order: `.download-table a[data-url]`, all `a[data-url]`, `source[src]`, then MP4/M3U8 regex; it must reject candidates containing `juicyads`. `_extract_playlist` must first inspect `.playlist-hover-wrap[data-href*='watch?v=']`, then fall back to anchors under the three playlist containers. It must normalize relative URLs with `urljoin`, require a title, preserve source order, and deduplicate normalized page URLs.

`build_safe_filename` must replace `/`, `\\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`, ASCII controls and path traversal-only names. It returns `.mp4` for M3U8 and uses a short safe suffix from ordinary media URLs, defaulting to `.mp4`.

- [ ] **Step 5: Run focused parser tests**

Run:

```powershell
uv run pytest tests/test_parser.py -q
```

Expected: all parser tests pass, including the copied real-layout fixture.

- [ ] **Step 6: Commit the pure parser**

```powershell
git add hanime_downloader_cli/src/hanime_downloader/parser.py hanime_downloader_cli/tests/test_parser.py hanime_downloader_cli/tests/fixtures/playlist_407460_snippet.html
git commit -m "Add video and series page parser"
```

---

### Task 4: Implement URL validation and the Cookie-aware site client

**Files:**
- Create: `hanime_downloader_cli/src/hanime_downloader/client.py`
- Create: `hanime_downloader_cli/tests/test_client.py`

**Interfaces:**
- Consumes: `AppSettings`, `CookieStore`, and `extract_video_page()`.
- Produces: `InvalidVideoUrl`, `CloudflareBlockedError`, and `PageRequestError`.
- Produces: `validate_video_page_url(url: str) -> str` returning a normalized URL.
- Produces: `HanimeClient(settings: AppSettings, cookie_store: CookieStore, session_factory: Callable | None = None)` with `async resolve(url: str) -> VideoPage` and `async close() -> None`.

- [ ] **Step 1: Write failing URL and client tests with an injected fake curl session**

Create `tests/test_client.py`:

```python
from dataclasses import dataclass
from pathlib import Path

import pytest

from hanime_downloader.client import (
    CloudflareBlockedError,
    HanimeClient,
    InvalidVideoUrl,
    validate_video_page_url,
)
from hanime_downloader.cookies import CookieStore
from hanime_downloader.settings import AppSettings


@dataclass
class FakeResponse:
    status_code: int
    text: str


class FakeSession:
    def __init__(self, responses: dict[str, FakeResponse], calls: list[dict], **kwargs):
        self.responses = responses
        self.calls = calls
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, url: str, **kwargs):
        self.calls.append({"url": url, "kwargs": kwargs, "session": self.kwargs})
        return self.responses[url]


def test_validate_video_page_url_restricts_host_and_watch_id():
    assert validate_video_page_url("https://hanime1.me/watch?v=123") == "https://hanime1.me/watch?v=123"
    for invalid in ("file:///tmp/a", "https://example.com/watch?v=1", "https://hanime1.me/"):
        with pytest.raises(InvalidVideoUrl):
            validate_video_page_url(invalid)


@pytest.mark.asyncio
async def test_resolve_sends_cookie_only_to_hanime_and_uses_proxy(tmp_path: Path):
    cookies = CookieStore(tmp_path / "cookies.json")
    cookies.save("cf_clearance=secret")
    calls: list[dict] = []
    responses = {
        "https://hanime1.me/watch?v=1": FakeResponse(200, '<h1 id="shareBtn-title">One</h1><source src="https://cdn.test/fallback.mp4">'),
        "https://hanime1.me/download?v=1": FakeResponse(200, '<a data-url="https://cdn.test/final.mp4">download</a>'),
    }
    factory = lambda **kwargs: FakeSession(responses, calls, **kwargs)
    client = HanimeClient(
        AppSettings(proxy_enabled=True, proxy_url="http://127.0.0.1:7890"),
        cookies,
        session_factory=factory,
    )
    page = await client.resolve("https://hanime1.me/watch?v=1")
    assert page.media_url == "https://cdn.test/final.mp4"
    assert all(call["kwargs"]["cookies"] == {"cf_clearance": "secret"} for call in calls)
    assert calls[0]["session"]["proxy"] == "http://127.0.0.1:7890"


@pytest.mark.asyncio
async def test_cloudflare_page_raises_explicit_error(tmp_path: Path):
    cookies = CookieStore(tmp_path / "cookies.json")
    cookies.save("cf_clearance=secret")
    response = FakeResponse(403, "<title>Just a moment...</title><div>cf-chl</div>")
    factory = lambda **kwargs: FakeSession({
        "https://hanime1.me/watch?v=1": response,
        "https://hanime1.me/download?v=1": response,
    }, [], **kwargs)
    client = HanimeClient(AppSettings(), cookies, session_factory=factory)
    with pytest.raises(CloudflareBlockedError, match="保存/更新 Cookie"):
        await client.resolve("https://hanime1.me/watch?v=1")
```

- [ ] **Step 2: Run the client tests and verify failure**

Run:

```powershell
uv run pytest tests/test_client.py -q
```

Expected: collection fails because `hanime_downloader.client` does not exist.

- [ ] **Step 3: Implement validation, concurrent page fetches, retries, and redacted errors**

Create `client.py`. `validate_video_page_url` must require `http` or `https`, hostname exactly `hanime1.me` or a subdomain ending in `.hanime1.me`, path `/watch`, and a non-empty `v` query value. Strip fragments but preserve other query parameters.

`HanimeClient.resolve()` must:

1. Load Cookie once for the resolve call.
2. Create `curl_cffi.requests.AsyncSession(impersonate="chrome124", timeout=30, proxy=proxy_or_none)` through the injectable factory.
3. Concurrently fetch the watch URL and `https://hanime1.me/download?v=<id>` using `asyncio.gather`.
4. Pass Cookie only on these Hanime1 calls.
5. Use `Referer: https://hanime1.me/` for the watch page and the watch URL for the download page.
6. Retry transport errors and HTTP 429/5xx up to three total attempts with delays `0.5` and `1.0` seconds.
7. Never retry malformed input, missing Cookie, HTTP 401/403 Cloudflare pages, or parser errors.
8. Detect Cloudflare by status `403` or body markers `cf-chl`, `challenge-platform`, `Just a moment`, and `Attention Required`.
9. Raise messages that mention the host/status but never Cookie or proxy credentials.

Wrap only the download-page fetch in `_safe_fetch_download()`: after its own retries, a non-Cloudflare failure returns an empty string so the parser can still use a media URL embedded in the watch page. A Cloudflare response from the watch page remains fatal. This preserves the existing application's download-page fallback without hiding a blocked primary session.

Use a module constant for headers:

```python
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}
```

Sanitize exceptions with a helper that replaces `urlsplit(proxy_url).username`, password, and the complete proxy URL with `[redacted]` before building `PageRequestError`.

- [ ] **Step 4: Run focused client tests**

Run:

```powershell
uv run pytest tests/test_client.py -q
```

Expected: all URL, Cookie, proxy, priority, and Cloudflare tests pass.

- [ ] **Step 5: Commit the site client**

```powershell
git add hanime_downloader_cli/src/hanime_downloader/client.py hanime_downloader_cli/tests/test_client.py
git commit -m "Add Cookie-aware Hanime page client"
```

---

### Task 5: Implement input normalization and series task construction

**Files:**
- Create: `hanime_downloader_cli/src/hanime_downloader/series.py`
- Create: `hanime_downloader_cli/tests/test_series.py`

**Interfaces:**
- Consumes: `validate_video_page_url()`, `VideoPage`, and `PlaylistItem`.
- Produces: `parse_multiple_urls(raw: str) -> list[str]`.
- Produces: `build_series_urls(current_url: str, page: VideoPage) -> list[str]`.

- [ ] **Step 1: Write failing tests for comma input and current-first series behavior**

Create `tests/test_series.py`:

```python
import pytest

from hanime_downloader.parser import PlaylistItem, VideoPage
from hanime_downloader.series import build_series_urls, parse_multiple_urls


def test_multiple_urls_trim_validate_and_deduplicate_in_first_order():
    raw = " https://hanime1.me/watch?v=2,https://hanime1.me/watch?v=1, https://hanime1.me/watch?v=2 "
    assert parse_multiple_urls(raw) == [
        "https://hanime1.me/watch?v=2",
        "https://hanime1.me/watch?v=1",
    ]


def test_multiple_urls_report_every_invalid_item_before_download():
    with pytest.raises(ValueError) as error:
        parse_multiple_urls("bad,https://example.com/watch?v=1")
    assert "bad" in str(error.value)
    assert "example.com" in str(error.value)


def test_series_includes_current_first_then_playlist_order_without_duplicates():
    current = "https://hanime1.me/watch?v=2"
    page = VideoPage(
        page_url=current,
        video_id="2",
        title="Two",
        media_url="https://cdn.test/2.mp4",
        playlist=(
            PlaylistItem("https://hanime1.me/watch?v=3", "Three", "3"),
            PlaylistItem(current, "Two", "2"),
            PlaylistItem("https://hanime1.me/watch?v=1", "One", "1"),
        ),
    )
    assert build_series_urls(current, page) == [
        current,
        "https://hanime1.me/watch?v=3",
        "https://hanime1.me/watch?v=1",
    ]


def test_series_requires_more_than_current_video():
    page = VideoPage("https://hanime1.me/watch?v=1", "1", "One", "https://cdn.test/1.mp4", ())
    with pytest.raises(ValueError, match="未识别到可批量下载"):
        build_series_urls(page.page_url, page)
```

- [ ] **Step 2: Run series tests and verify failure**

Run:

```powershell
uv run pytest tests/test_series.py -q
```

Expected: collection fails because `hanime_downloader.series` does not exist.

- [ ] **Step 3: Implement deterministic normalization and series expansion**

Create `series.py` with this behavior:

```python
from .client import InvalidVideoUrl, validate_video_page_url
from .parser import VideoPage


def parse_multiple_urls(raw: str) -> list[str]:
    valid: list[str] = []
    invalid: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        candidate = part.strip()
        if not candidate:
            continue
        try:
            normalized = validate_video_page_url(candidate)
        except InvalidVideoUrl:
            invalid.append(candidate)
            continue
        if normalized not in seen:
            seen.add(normalized)
            valid.append(normalized)
    if invalid:
        raise ValueError("以下地址无效: " + ", ".join(invalid))
    if not valid:
        raise ValueError("至少需要一个视频地址")
    return valid


def build_series_urls(current_url: str, page: VideoPage) -> list[str]:
    ordered = [validate_video_page_url(current_url)]
    seen = set(ordered)
    for item in page.playlist:
        normalized = validate_video_page_url(item.page_url)
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    if len(ordered) <= 1:
        raise ValueError("当前未识别到可批量下载的系列视频")
    return ordered
```

- [ ] **Step 4: Run focused tests and commit**

Run:

```powershell
uv run pytest tests/test_series.py -q
git add hanime_downloader_cli/src/hanime_downloader/series.py hanime_downloader_cli/tests/test_series.py
git commit -m "Add batch and series URL construction"
```

Expected: all series tests pass before the commit is created.

---

### Task 6: Implement the real-byte HTTP downloader with resume and atomic commit

**Files:**
- Create: `hanime_downloader_cli/tests/conftest.py`
- Create: `hanime_downloader_cli/src/hanime_downloader/downloader.py`
- Create: `hanime_downloader_cli/tests/test_http_downloader.py`

**Interfaces:**
- Consumes: `AppSettings` for proxy selection and `build_safe_filename()` for target names.
- Produces: `DownloadStatus` enum values `WAITING`, `RESOLVING`, `DOWNLOADING`, `SKIPPED`, `SUCCESS`, `FAILED`.
- Produces: `DownloadSpec(page_url: str, title: str, media_url: str, output_directory: Path, force: bool = False)`.
- Produces: `DownloadResult(spec: DownloadSpec, status: DownloadStatus, path: Path | None = None, error: str | None = None)`.
- Produces: `HttpDownloader(settings: AppSettings, client_factory: Callable | None = None)` with `async download(spec: DownloadSpec, progress: ProgressSink | None = None) -> DownloadResult` and `async close() -> None`.

- [ ] **Step 1: Add a real local Range-capable HTTP fixture**

In `tests/conftest.py`, add this real TCP fixture. It records incoming `Range` headers, returns `206` plus `Content-Range` for `bytes=N-`, and supports `?ignore_range=1` to deliberately return `200` with the complete payload:

```python
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
from threading import Thread

import pytest


@dataclass
class RangeServer:
    base_url: str
    payload: bytes
    ranges: list[str | None]


@pytest.fixture
def range_server():
    payload = bytes(range(256)) * 8
    ranges: list[str | None] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            range_value = self.headers.get("Range")
            ranges.append(range_value)
            ignore_range = "ignore_range=1" in self.path
            match = re.fullmatch(r"bytes=(\d+)-", range_value or "")
            if match and not ignore_range:
                start = int(match.group(1))
                body = payload[start:]
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{len(payload) - 1}/{len(payload)}")
                self.send_header("Accept-Ranges", "bytes")
            else:
                body = payload
                self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield RangeServer(f"http://{host}:{port}", payload, ranges)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
```

- [ ] **Step 2: Write failing real-byte downloader tests**

Create `tests/test_http_downloader.py`:

```python
from pathlib import Path

import pytest

from hanime_downloader.downloader import (
    DownloadSpec,
    DownloadStatus,
    HttpDownloader,
)
from hanime_downloader.settings import AppSettings


@pytest.mark.asyncio
async def test_http_download_writes_real_bytes_and_commits_atomically(range_server, tmp_path: Path):
    downloader = HttpDownloader(AppSettings())
    spec = DownloadSpec(
        page_url="https://hanime1.me/watch?v=1",
        title="Episode 1",
        media_url=f"{range_server.base_url}/video.mp4",
        output_directory=tmp_path,
    )
    result = await downloader.download(spec)
    assert result.status is DownloadStatus.SUCCESS
    assert result.path is not None
    assert result.path.read_bytes() == range_server.payload
    assert list(tmp_path.glob("*.part*")) == []
    await downloader.close()


@pytest.mark.asyncio
async def test_http_download_resumes_existing_part(range_server, tmp_path: Path):
    prefix = range_server.payload[:37]
    part = tmp_path / "Episode 1.mp4.part"
    part.write_bytes(prefix)
    downloader = HttpDownloader(AppSettings())
    spec = DownloadSpec("https://hanime1.me/watch?v=1", "Episode 1", f"{range_server.base_url}/video.mp4", tmp_path)
    result = await downloader.download(spec)
    assert result.path is not None and result.path.read_bytes() == range_server.payload
    assert "bytes=37-" in range_server.ranges


@pytest.mark.asyncio
async def test_ignored_range_restarts_instead_of_appending(range_server, tmp_path: Path):
    (tmp_path / "Episode 1.mp4.part").write_bytes(b"wrong-prefix")
    downloader = HttpDownloader(AppSettings())
    spec = DownloadSpec("https://hanime1.me/watch?v=1", "Episode 1", f"{range_server.base_url}/video.mp4?ignore_range=1", tmp_path)
    result = await downloader.download(spec)
    assert result.path is not None and result.path.read_bytes() == range_server.payload


@pytest.mark.asyncio
async def test_existing_final_is_skipped_without_force(range_server, tmp_path: Path):
    final = tmp_path / "Episode 1.mp4"
    final.write_bytes(b"existing")
    downloader = HttpDownloader(AppSettings())
    spec = DownloadSpec("https://hanime1.me/watch?v=1", "Episode 1", f"{range_server.base_url}/video.mp4", tmp_path)
    result = await downloader.download(spec)
    assert result.status is DownloadStatus.SKIPPED
    assert final.read_bytes() == b"existing"
```

- [ ] **Step 3: Run the downloader tests to verify failure**

Run:

```powershell
uv run pytest tests/test_http_downloader.py -q
```

Expected: collection fails because the downloader types do not exist.

- [ ] **Step 4: Implement stream download, Range validation, and secret-safe proxy use**

Create `downloader.py` with the listed enum and frozen dataclasses. Define a progress protocol:

```python
from typing import Protocol


class ProgressSink(Protocol):
    def start(self, label: str, total: int | None) -> object: ...
    def advance(self, token: object, amount: int) -> None: ...
    def finish(self, token: object) -> None: ...
```

`HttpDownloader.download()` must create the output directory, resolve and verify target containment, skip a non-empty final unless forced, and use `<final-name>.part` for normal downloads or `<final-name>.force.part` for forced replacement. Build `httpx.AsyncClient(follow_redirects=True, timeout=httpx.Timeout(30, read=None), proxy=settings.proxy_url if enabled else None, headers={User-Agent, Referer})` through the injectable factory.

When a part exists, send `Range: bytes=<size>-`. Append only if status is `206` and `Content-Range` begins with `bytes <size>-`; otherwise close the response and issue a second GET without Range while opening the part in `wb`. Stream with `response.aiter_bytes(1024 * 256)`, flush and `os.fsync`, verify the expected total when the response provides one, then `os.replace(part, final)`. On cancellation or failure, leave the part and return/raise without modifying an existing final.

Return `DownloadResult` for skip and success. Raise a domain `DownloadError` with a redacted Chinese message on HTTP, length, filesystem, and proxy failures; the coordinator in Task 8 converts it to `FAILED`.

- [ ] **Step 5: Run real-byte tests plus settings tests**

Run:

```powershell
uv run pytest tests/test_http_downloader.py tests/test_settings.py -q
```

Expected: real bytes are written, resume sends the recorded Range, ignored Range restarts cleanly, and existing files are not overwritten.

- [ ] **Step 6: Commit the HTTP downloader**

```powershell
git add hanime_downloader_cli/src/hanime_downloader/downloader.py hanime_downloader_cli/tests/conftest.py hanime_downloader_cli/tests/test_http_downloader.py
git commit -m "Add resumable HTTP video downloader"
```

---

### Task 7: Implement the FFmpeg M3U8 backend

**Files:**
- Create: `hanime_downloader_cli/src/hanime_downloader/ffmpeg.py`
- Create: `hanime_downloader_cli/tests/test_ffmpeg.py`

**Interfaces:**
- Consumes: `DownloadSpec`, `DownloadResult`, `DownloadStatus`, and `AppSettings`.
- Produces: `FfmpegMissingError` and `FfmpegDownloadError`.
- Produces: `FfmpegDownloader(settings: AppSettings, executable: str | None = None, process_factory: Callable | None = None)` with `async download(spec: DownloadSpec) -> DownloadResult`.

- [ ] **Step 1: Write failing FFmpeg command and commit tests**

Create `tests/test_ffmpeg.py`:

```python
from pathlib import Path

import pytest

from hanime_downloader.downloader import DownloadSpec, DownloadStatus
from hanime_downloader.ffmpeg import FfmpegDownloader, FfmpegMissingError
from hanime_downloader.settings import AppSettings


class FakeProcess:
    def __init__(self, returncode: int, output_path: Path, payload: bytes = b"video"):
        self.returncode = returncode
        self.output_path = output_path
        self.payload = payload

    async def communicate(self):
        if self.returncode == 0:
            self.output_path.write_bytes(self.payload)
        return b"", b"ffmpeg failed" if self.returncode else b""


@pytest.mark.asyncio
async def test_ffmpeg_uses_argument_array_proxy_and_atomic_result(tmp_path: Path):
    calls: list[tuple] = []

    async def factory(*args, **kwargs):
        calls.append((args, kwargs))
        output = Path(args[-1])
        return FakeProcess(0, output)

    settings = AppSettings(proxy_enabled=True, proxy_url="http://127.0.0.1:7890")
    downloader = FfmpegDownloader(settings, executable="/usr/bin/ffmpeg", process_factory=factory)
    spec = DownloadSpec("https://hanime1.me/watch?v=1", "Episode", "https://cdn.test/index.m3u8", tmp_path)
    result = await downloader.download(spec)
    assert result.status is DownloadStatus.SUCCESS
    assert result.path is not None and result.path.read_bytes() == b"video"
    args, kwargs = calls[0]
    assert args[0] == "/usr/bin/ffmpeg"
    assert ("-c", "copy") == (args[args.index("-c")], args[args.index("-c") + 1])
    assert "shell" not in kwargs
    assert "http://127.0.0.1:7890" in kwargs["env"]["http_proxy"]


def test_missing_ffmpeg_is_explicit(monkeypatch):
    monkeypatch.setattr("hanime_downloader.ffmpeg.shutil.which", lambda _name: None)
    with pytest.raises(FfmpegMissingError, match="FFmpeg"):
        FfmpegDownloader(AppSettings())
```

- [ ] **Step 2: Run FFmpeg tests and verify failure**

Run:

```powershell
uv run pytest tests/test_ffmpeg.py -q
```

Expected: collection fails because `hanime_downloader.ffmpeg` does not exist.

- [ ] **Step 3: Implement safe subprocess invocation and temporary output**

Create `ffmpeg.py`. Resolve `executable or shutil.which("ffmpeg")` in the constructor and fail immediately when absent. `download()` must skip an existing non-empty final unless `force`, create a temp name ending in `.part.mp4`, and invoke:

```python
args = [
    executable,
    "-nostdin",
    "-y",
    "-user_agent", DEFAULT_USER_AGENT,
    "-referer", spec.page_url,
    "-i", spec.media_url,
    "-c", "copy",
    str(part_path),
]
```

Call `asyncio.create_subprocess_exec(*args, stdout=PIPE, stderr=PIPE, env=child_env)` directly. Never pass a `shell` argument. When proxy is enabled, set only the child environment's `http_proxy`, `https_proxy`, `HTTP_PROXY`, and `HTTPS_PROXY`; never mutate `os.environ` globally.

On return code zero, require a non-empty part and `os.replace` it to final. On failure, keep the part, decode only the final 2,000 bytes of stderr, redact proxy credentials, and raise `FfmpegDownloadError` without Cookie data.

- [ ] **Step 4: Run focused FFmpeg tests**

Run:

```powershell
uv run pytest tests/test_ffmpeg.py -q
```

Expected: missing-binary, command-array, proxy-child-environment, success, nonzero exit, and empty-output tests pass.

- [ ] **Step 5: Commit the FFmpeg backend**

```powershell
git add hanime_downloader_cli/src/hanime_downloader/ffmpeg.py hanime_downloader_cli/tests/test_ffmpeg.py
git commit -m "Add FFmpeg HLS downloader"
```

---

### Task 8: Implement concurrent resolution and download coordination

**Files:**
- Modify: `hanime_downloader_cli/src/hanime_downloader/downloader.py`
- Create: `hanime_downloader_cli/tests/test_coordinator.py`

**Interfaces:**
- Consumes: `HanimeClient.resolve()`, `HttpDownloader.download()`, a lazy `FfmpegDownloader` factory, and settings concurrency.
- Produces: `BatchResult(results: tuple[DownloadResult, ...])` with `success_count`, `skipped_count`, `failed_count`, and `has_failures` properties.
- Produces: `DownloadCoordinator(settings: AppSettings, resolver, http_downloader, ffmpeg_downloader_factory: Callable[[], object])` with `async run(page_urls: list[str], force: bool = False, progress: ProgressSink | None = None) -> BatchResult`.

- [ ] **Step 1: Write failing tests for the concurrency ceiling, order, backend routing, and failure isolation**

Create `tests/test_coordinator.py`:

```python
import asyncio
from pathlib import Path

import pytest

from hanime_downloader.downloader import (
    BatchResult,
    DownloadCoordinator,
    DownloadResult,
    DownloadStatus,
)
from hanime_downloader.parser import VideoPage
from hanime_downloader.settings import AppSettings


@pytest.mark.asyncio
async def test_coordinator_limits_active_videos_and_preserves_input_result_order(tmp_path: Path):
    active = 0
    peak = 0

    async def resolve(url: str):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.02)
        active -= 1
        video_id = url.rsplit("=", 1)[-1]
        return VideoPage(url, video_id, f"Episode {video_id}", f"https://cdn.test/{video_id}.mp4", ())

    class Backend:
        async def download(self, spec, progress=None):
            await asyncio.sleep(0.01)
            return DownloadResult(spec, DownloadStatus.SUCCESS, tmp_path / f"{spec.title}.mp4")

    settings = AppSettings(download_directory=str(tmp_path), concurrent_downloads=2)
    coordinator = DownloadCoordinator(settings, resolve, Backend(), lambda: Backend())
    urls = [f"https://hanime1.me/watch?v={index}" for index in range(5)]
    batch = await coordinator.run(urls)
    assert peak == 2
    assert [result.spec.page_url for result in batch.results] == urls
    assert batch.success_count == 5


@pytest.mark.asyncio
async def test_one_failure_does_not_cancel_other_tasks(tmp_path: Path):
    async def resolve(url: str):
        video_id = url.rsplit("=", 1)[-1]
        if video_id == "2":
            raise RuntimeError("blocked")
        return VideoPage(url, video_id, video_id, f"https://cdn.test/{video_id}.mp4", ())

    class Backend:
        async def download(self, spec, progress=None):
            return DownloadResult(spec, DownloadStatus.SUCCESS, tmp_path / f"{spec.title}.mp4")

    coordinator = DownloadCoordinator(AppSettings(download_directory=str(tmp_path), concurrent_downloads=3), resolve, Backend(), lambda: Backend())
    batch = await coordinator.run([f"https://hanime1.me/watch?v={index}" for index in (1, 2, 3)])
    assert batch.success_count == 2
    assert batch.failed_count == 1
    assert batch.has_failures is True
```

- [ ] **Step 2: Run coordinator tests and verify failure**

Run:

```powershell
uv run pytest tests/test_coordinator.py -q
```

Expected: imports fail because `BatchResult` and `DownloadCoordinator` do not exist.

- [ ] **Step 3: Implement one semaphore around the whole per-video lifecycle**

Extend `downloader.py` with `BatchResult` and `DownloadCoordinator`. Create one `asyncio.Semaphore(settings.concurrent_downloads)`. Each worker must acquire it before resolving the page and release it only after the selected backend finishes, so the configured number means simultaneous video tasks, not only simultaneous network writes.

Build `DownloadSpec` from each resolved page with `Path(settings.download_directory).expanduser()`. Select FFmpeg when `urlsplit(page.media_url).path.lower().endswith(".m3u8")`; otherwise select HTTP. Invoke `ffmpeg_downloader_factory` only on the first M3U8 task and cache that backend, so MP4-only batches work on systems without FFmpeg. Protect first creation with an `asyncio.Lock` because multiple M3U8 workers may arrive together. Catch all non-cancellation exceptions per worker and return a `FAILED` result with a redacted error. If resolution fails before a normal `DownloadSpec` exists, create one with the page URL as `title`, an empty `media_url`, the configured output directory, and the current `force` value. Re-raise `asyncio.CancelledError`. Use indexed task slots so `BatchResult.results` matches input order regardless of completion order.

Define counts exactly:

```python
@dataclass(frozen=True)
class BatchResult:
    results: tuple[DownloadResult, ...]

    @property
    def success_count(self) -> int:
        return sum(item.status is DownloadStatus.SUCCESS for item in self.results)

    @property
    def skipped_count(self) -> int:
        return sum(item.status is DownloadStatus.SKIPPED for item in self.results)

    @property
    def failed_count(self) -> int:
        return sum(item.status is DownloadStatus.FAILED for item in self.results)

    @property
    def has_failures(self) -> bool:
        return self.failed_count > 0
```

- [ ] **Step 4: Run coordinator and backend regression tests**

Run:

```powershell
uv run pytest tests/test_coordinator.py tests/test_http_downloader.py tests/test_ffmpeg.py -q
```

Expected: peak concurrency equals the configured limit, result order is stable, M3U8 routes to FFmpeg, and failure isolation passes.

- [ ] **Step 5: Commit the coordinator**

```powershell
git add hanime_downloader_cli/src/hanime_downloader/downloader.py hanime_downloader_cli/tests/test_coordinator.py
git commit -m "Add concurrent video download coordinator"
```

---

### Task 9: Build the interactive terminal program and Rich progress adapter

**Files:**
- Create: `hanime_downloader_cli/src/hanime_downloader/cli.py`
- Create: `hanime_downloader_cli/tests/test_cli.py`

**Interfaces:**
- Consumes: all public settings, Cookie, client, series, coordinator, and backend interfaces.
- Produces: `main() -> int` console entry point.
- Produces: `Application.run() -> int`, `Application.settings_menu()`, `Application.cookie_menu()`, and `Application.download_menu()`.
- Produces: `RichProgressSink` implementing `ProgressSink`.

- [ ] **Step 1: Write failing menu-flow tests with injected input and secret functions**

Create `tests/test_cli.py`:

```python
from pathlib import Path

from rich.console import Console

from hanime_downloader.cli import Application
from hanime_downloader.cookies import CookieStore
from hanime_downloader.settings import SettingsStore


def scripted_input(values: list[str]):
    iterator = iter(values)
    return lambda _prompt="": next(iterator)


def test_cookie_menu_overwrites_secret_without_echo(tmp_path: Path):
    output = Console(record=True, width=100)
    app = Application(
        settings_store=SettingsStore(tmp_path / "settings.json"),
        cookie_store=CookieStore(tmp_path / "cookies.json"),
        input_fn=scripted_input(["2", "0"]),
        secret_fn=lambda _prompt="": "cf_clearance=top-secret",
        console=output,
    )
    assert app.run() == 0
    rendered = output.export_text()
    assert "Cookie 已覆盖保存" in rendered
    assert "top-secret" not in rendered


def test_settings_menu_persists_download_directory_threads_and_proxy(tmp_path: Path):
    output = Console(record=True, width=100)
    settings_store = SettingsStore(tmp_path / "settings.json")
    app = Application(
        settings_store=settings_store,
        cookie_store=CookieStore(tmp_path / "cookies.json"),
        input_fn=scripted_input([
            "1",
            "~/Videos/Hanime",
            "4",
            "y",
            "http://127.0.0.1:7890",
            "0",
        ]),
        secret_fn=lambda _prompt="": "",
        console=output,
    )
    assert app.run() == 0
    saved = settings_store.load().settings
    assert saved.download_directory == "~/Videos/Hanime"
    assert saved.concurrent_downloads == 4
    assert saved.proxy_enabled is True


def test_multiple_download_passes_comma_normalized_urls_to_batch(tmp_path: Path):
    captured: list[list[str]] = []

    async def run_batch(urls, _settings, _force, _console):
        captured.append(urls)
        return False

    app = Application(
        SettingsStore(tmp_path / "settings.json"),
        CookieStore(tmp_path / "cookies.json"),
        input_fn=scripted_input([
            "3", "2",
            "https://hanime1.me/watch?v=1, https://hanime1.me/watch?v=2",
            "n",
            "0", "0",
        ]),
        secret_fn=lambda _prompt="": "",
        console=Console(record=True, width=100),
        batch_runner=run_batch,
    )
    assert app.run() == 0
    assert captured == [[
        "https://hanime1.me/watch?v=1",
        "https://hanime1.me/watch?v=2",
    ]]
```

- [ ] **Step 2: Run CLI tests and verify failure**

Run:

```powershell
uv run pytest tests/test_cli.py -q
```

Expected: collection fails because `hanime_downloader.cli` does not exist.

- [ ] **Step 3: Implement the main menu, settings flow, secret Cookie input, and download submenus**

Create `cli.py` with dependency-injected `input_fn`, `secret_fn`, `Console`, and `batch_runner`. Use `getpass.getpass` as the production secret function. Main menu choices must be exactly `1` settings, `2` Cookie, `3` downloads, and `0` exit. Download submenu choices must be exactly `1` single, `2` multiple, `3` series, and `0` back.

Settings flow asks for download directory, integer concurrency, proxy `y/n`, and proxy URL only when enabled. Construct `AppSettings` before saving so invalid values are displayed and the menu repeats without overwriting the previous valid file.

Single mode validates one URL. Multiple mode uses `parse_multiple_urls`. Series mode resolves the supplied page once, calls `build_series_urls`, and then passes the expanded URLs to the coordinator; accepting one repeated resolve for the current video is correct because every queued episode must obtain a fresh media URL. Each download mode asks `是否强制覆盖已存在文件？[y/N]`.

Implement `RichProgressSink` using one shared `rich.progress.Progress` instance safe for updates from asyncio tasks in the same event loop. The batch runner creates `HanimeClient`, `HttpDownloader`, and `FfmpegDownloader` lazily; therefore missing FFmpeg affects only a batch that actually contains M3U8. Always close page and HTTP clients in `finally`.

Render a final Rich table with columns `状态`, `标题`, `文件`, and `原因`, plus counts for success, skipped, and failed. Track `self.had_failures`; `Application.run()` returns `1` when the user exits after any batch failure and `0` otherwise. Catch `KeyboardInterrupt`, print `已停止，临时文件已保留`, cancel the active batch, and return `130`.

The console entry point must be:

```python
def main() -> int:
    app = Application(
        settings_store=SettingsStore(),
        cookie_store=CookieStore(),
        input_fn=input,
        secret_fn=getpass.getpass,
        console=Console(),
    )
    return app.run()
```

The script wrapper installed by `uv` uses this integer as the process exit code.

- [ ] **Step 4: Run CLI tests and an automated start/exit smoke test**

Run:

```powershell
uv run pytest tests/test_cli.py -q
"0" | uv run hanime-downloader
```

Expected: CLI tests pass; the smoke command prints the main menu and exits with code `0` without requiring Cookie, network, browser, or FFmpeg.

- [ ] **Step 5: Commit the terminal application**

```powershell
git add hanime_downloader_cli/src/hanime_downloader/cli.py hanime_downloader_cli/tests/test_cli.py hanime_downloader_cli/pyproject.toml hanime_downloader_cli/uv.lock
git commit -m "Add interactive downloader terminal app"
```

---

### Task 10: Complete documentation and cross-platform acceptance verification

**Files:**
- Create: `hanime_downloader_cli/README.md`
- Modify: `hanime_downloader_cli/pyproject.toml`
- Modify: `hanime_downloader_cli/tests/test_cli.py`
- Modify only if verification reveals a defect: files under `hanime_downloader_cli/src/hanime_downloader/`

**Interfaces:**
- Consumes: final `uv` project and `hanime-downloader` entry point.
- Produces: a standalone documented directory that can be copied to Linux and installed with `uv sync --locked`.

- [ ] **Step 1: Add an end-to-end acceptance test through the application batch boundary**

Extend `tests/test_cli.py` with a test that uses a temporary settings file and Cookie file, the real local HTTP fixture, a fake page resolver returning the fixture's media URL, the real `HttpDownloader`, and `DownloadCoordinator`. Drive the menu with scripted input for a single download and assert the downloaded file's bytes equal the server payload. The test must call the same `batch_runner` used by production with only the page resolver injected; it must not call `HttpDownloader.download()` directly.

Run just this test first:

```powershell
uv run pytest tests/test_cli.py::test_single_download_menu_produces_real_file -q
```

Expected before wiring the injection seam: FAIL because the production batch runner cannot yet accept the resolver override.

- [ ] **Step 2: Add the smallest resolver injection seam and make the acceptance test pass**

Add an optional `resolver_factory` argument to the production batch runner. Default it to the real `HanimeClient`; the test supplies an async resolver returning `VideoPage` with the real local server media URL. Do not add a separate test-only code path.

Run:

```powershell
uv run pytest tests/test_cli.py::test_single_download_menu_produces_real_file -q
```

Expected: PASS and the target file contains the local server's exact bytes.

- [ ] **Step 3: Write the Linux-focused README with exact operations**

Create `README.md` with this complete operational content, adding screenshots only if they can be generated without including Cookie values:

````markdown
# Hanime Downloader

一个不包含浏览器和 Web 前端的 Hanime1 终端下载程序。支持单视频、英文逗号分隔的多视频以及页面系列清单下载。

请只下载你有权保存的内容，并遵守目标网站条款和所在地法律。

## 环境要求

- Linux 或 Windows，Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- 只有 M3U8 下载需要系统 FFmpeg；普通 MP4 不需要 FFmpeg

## 安装和启动

```bash
uv sync --locked
uv run hanime-downloader
```

程序不会打开浏览器。启动后通过数字选择主菜单：

```text
1. 设置
2. 保存/更新 Cookie
3. 下载视频
0. 退出
```

## 首次设置

在“设置”中填写：

- 下载目录，默认 `./downloads`
- 下载线程数，表示同时下载的视频数量，可选 `1-16`
- 是否使用 HTTP/HTTPS 代理
- 代理地址，例如 `http://127.0.0.1:7890`

代理启用后同时用于页面解析、MP4 和 FFmpeg。首版不支持 SOCKS。

## 保存或更新 Cookie

1. 在浏览器中正常打开 Hanime1。
2. 打开开发者工具的 Network 面板并刷新页面。
3. 选择发往 `hanime1.me` 的请求，在 Request Headers 中复制 `Cookie` 的值，不要复制 `Cookie:` 标签。
4. 返回程序选择“保存/更新 Cookie”，粘贴后回车。

输入不会显示在终端上。每次保存都会完整覆盖旧 Cookie。不要把 `cookies.json` 分享给任何人，也不要提交到版本控制。

## 下载方式

下载菜单包含：

```text
1. 下载单个视频
2. 下载多个视频
3. 下载系列视频
0. 返回
```

- 单个：输入一个 `https://hanime1.me/watch?v=...` 页面地址。
- 多个：用英文逗号分隔地址，例如 `地址1,地址2,地址3`。程序会校验并按首次出现顺序去重。
- 系列：输入系列中的任意一集。程序读取页面播放清单，包含当前集并按页面顺序下载。

每次可选择是否强制覆盖。默认情况下，已有非空文件会跳过；未完成下载保存在 `.part` 文件中，下次运行会尝试断点续传。批次结束后会列出成功、跳过和失败任务。

正常退出状态码为 `0`；会话中存在下载失败时为 `1`；按 `Ctrl+C` 中断时为 `130`。

## Linux 安装 FFmpeg

```bash
# Debian / Ubuntu
sudo apt install ffmpeg

# Fedora（需要已配置提供 FFmpeg 的软件源）
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

使用 `ffmpeg -version` 检查安装。FFmpeg 只负责 M3U8 流复制，程序不会重新编码视频。

## 本地文件

配置目录优先使用：

```text
$XDG_CONFIG_HOME/hanime-downloader/
```

未设置 `XDG_CONFIG_HOME` 时使用：

```text
~/.config/hanime-downloader/
```

- `settings.json`：下载目录、并发数和代理设置
- `cookies.json`：站点 Cookie；Linux 权限为 `0600`
- `./downloads`：默认下载目录，以启动程序时的当前目录为基准

## 常见问题

### 提示 Cloudflare 拦截

Cookie 可能过期。退出下载菜单，在主菜单重新选择“保存/更新 Cookie”。程序不会自动启动浏览器或刷新 Cookie。

### 代理连接失败

确认代理已启动，并使用 `http://主机:端口` 或 `https://主机:端口`。不要填写 `socks5://`。

### M3U8 提示找不到 FFmpeg

按照上面的系统命令安装 FFmpeg，然后重新运行该任务。MP4 下载不受影响。

### 无法写入下载目录

检查目录是否存在、当前用户是否有写权限以及磁盘剩余空间。相对目录以程序启动位置为基准。

### 临时文件一直存在

`.part` 或 `.part.mp4` 是未完成任务的断点文件。保留它可在下次继续；确认不再需要后才手动删除。

## 安全说明

Cookie 只用于 `hanime1.me` 页面请求，不会发送给第三方媒体 CDN 或 FFmpeg。含账号密码的代理 URL 会保存在 `settings.json`，请自行限制该文件权限。不要在公开日志、截图或问题报告中粘贴 Cookie 或代理凭据。
````

Add `readme = "README.md"` under `[project]` in `pyproject.toml`, then run `uv lock` so final package metadata and the lock remain synchronized.

- [ ] **Step 4: Run the complete new-project verification suite**

Run from `hanime_downloader_cli/`:

```powershell
uv sync --locked
uv run pytest -q
uv run python -m compileall -q src
"0" | uv run hanime-downloader
```

Expected: all tests pass; compileall exits `0`; the menu starts and exits `0`; the real-byte acceptance and resume tests pass.

- [ ] **Step 5: Run the existing desktop-project regression suite**

Run from the repository root:

```powershell
python -m pytest python_backend\tests -q
python -m compileall -q python_backend
node --check src\main\resources\static\app.js
```

Expected: the existing test suite, Python compilation, and frontend syntax check still pass because the new project is isolated.

- [ ] **Step 6: Perform Linux verification when a Linux runtime is available**

First check without changing host configuration:

```powershell
wsl.exe --status
docker version
```

If WSL is available, run from the repository mounted in WSL:

```bash
cd /mnt/d/Project/AI-Project/Hanime1-Vedio-Download/hanime_downloader_cli
uv sync --locked
uv run pytest -q
printf '0\n' | uv run hanime-downloader
```

If Docker is available but WSL is not usable, run:

```powershell
docker run --rm -v "${PWD}:/work" -w /work/hanime_downloader_cli ghcr.io/astral-sh/uv:python3.11-bookworm-slim sh -lc "uv sync --locked && uv run pytest -q && printf '0\n' | uv run hanime-downloader"
```

Expected: dependency sync, all tests, and menu smoke pass in Linux. If neither runtime is available, record exactly `Linux runtime unavailable; Linux execution not verified on this host` in the final handoff and do not claim Linux was executed.

- [ ] **Step 7: Review the final diff for secrets and scope**

Run:

```powershell
git status --short
git diff --check
git diff -- hanime_downloader_cli
Get-ChildItem -Recurse -File hanime_downloader_cli | Where-Object { $_.FullName -notmatch '\\.venv\\|\\.pytest_cache\\|__pycache__' } | Select-String -Pattern 'cf_clearance=|hanime1_session=|remember_web|top-secret'
```

Expected: only the intended new project and plan-related files are changed; `git diff --check` is clean; any secret-pattern match is confined to explicit dummy test values such as `cf_clearance=secret`, never a real Cookie.

- [ ] **Step 8: Commit documentation and acceptance coverage**

```powershell
git add hanime_downloader_cli
git commit -m "Document and verify Linux terminal downloader"
```

---

## Final Acceptance Checklist

- [ ] `uv sync --locked` succeeds from the standalone `hanime_downloader_cli/` directory.
- [ ] `uv run pytest -q` passes, including real-byte download and Range-resume tests.
- [ ] `uv run python -m compileall -q src` succeeds.
- [ ] `uv run hanime-downloader` shows settings, Cookie, and download menus without opening a browser.
- [ ] Saving Cookie twice leaves only the second Cookie set and does not echo its value.
- [ ] Single download produces a verified file.
- [ ] Comma-separated input is trimmed, validated, ordered, and deduplicated.
- [ ] Series input includes the current video, preserves page playlist order, and continues after an episode failure.
- [ ] Configured concurrency limits whole video tasks, not file segments.
- [ ] HTTP proxy is applied to page, MP4, and FFmpeg operations without logging credentials.
- [ ] Hanime1 Cookie is never sent to the media client or FFmpeg.
- [ ] Existing final files are skipped by default; force replacement is atomic.
- [ ] `Ctrl+C` preserves resumable temporary files.
- [ ] Existing desktop-project tests and frontend syntax check still pass.
- [ ] Linux execution evidence is reported accurately as passed or unavailable.
