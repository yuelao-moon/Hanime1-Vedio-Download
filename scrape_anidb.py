"""
抓取 anidb.net 动漫页面的所有数据，输出为 JSON 文件到根目录。
完全复用项目中 HanimeScraper 的 Cloudflare 绕过逻辑（headless=False 真实浏览器 + 循环等待）。
用法: python scrape_anidb.py [URL]
默认: https://anidb.net/anime/8727
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path

from selectolax.parser import HTMLParser

TARGET_URL = "https://anidb.net/anime/8727"
ROOT = Path(__file__).parent

# ──────────────────────────────────────────────
# 与项目 scraper.py 相同的浏览器检测逻辑
# ──────────────────────────────────────────────

def looks_like_blocked_page(html: str) -> bool:
    """完全复用 parser.py 中的判断逻辑。"""
    lower = (html or "").lower()
    return any(
        marker in lower
        for marker in (
            "attention required! | cloudflare",
            "cloudflare ray id",
            "cf-challenge",
            "cf-turnstile",
            "just a moment",
            "checking your browser",
            "verify you are human",
            "正在检查您的浏览器",
            "请验证您是真人",
        )
    )


def looks_like_anidb_content(html: str) -> bool:
    """等价于 scraper.py 中 looks_like_hanime_content，改为检测 anidb 内容特征。"""
    lower = (html or "").lower()
    return any(
        marker in lower
        for marker in (
            "anidb.net",
            "g_definitionlist",
            "anime-title",
            "div.data",
            "episodelist",
            "id=\"tab_",
            "adult content warning",  # 登录前的内容警告也算真实 anidb 页面
        )
    )


def is_adult_warning_page(html: str) -> bool:
    """检测是否停留在 18+ 成人内容警告页（需要登录才能继续）。"""
    lower = (html or "").lower()
    return "adult content warning" in lower and "you have to be logged in" in lower


def has_real_anime_data(html: str) -> bool:
    """检测页面是否包含真实的动漫详情数据（已登录且权限开放）。"""
    lower = (html or "").lower()
    return any(
        marker in lower
        for marker in (
            "g_definitionlist",
            "episodelist",
            "id=\"tab_1",
            "id=\"tab_2",
            "div.data.anime",
            "itemprop=\"name\"",
        )
    ) and "adult content warning" not in lower


def is_browser_closed_error(exc: BaseException) -> bool:
    """直接复用 scraper.py 中的同名函数。"""
    try:
        from playwright.async_api import TargetClosedError
        if isinstance(exc, TargetClosedError):
            return True
    except ImportError:
        pass
    msg = str(exc).lower()
    return any(
        phrase in msg
        for phrase in (
            "target closed",
            "browser has been closed",
            "browser closed",
            "connection closed",
            "context or browser has been closed",
            "page has been closed",
        )
    )


# ──────────────────────────────────────────────
# 浏览器会话（参照 HanimeScraper 的结构）
# ──────────────────────────────────────────────

class AnidbScraper:
    """精简版爬虫，完全参照 HanimeScraper 的 Playwright 浏览器逻辑。"""

    VERIFICATION_TIMEOUT = 180  # 与 AppSettings.browserVerificationTimeoutSeconds 默认值一致

    def __init__(self) -> None:
        self._browser_lock = asyncio.Lock()
        self._playwright = None
        self._context = None
        self._session_page = None

    async def fetch_html(self, url: str) -> str:
        async with self._browser_lock:
            return await self._fetch_locked(url)

    async def _fetch_locked(self, url: str, _retried: bool = False) -> str:
        """与 HanimeScraper._fetch_with_playwright_locked 完全相同的结构。"""
        try:
            await self._ensure_browser(url)
            page = self._session_page
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            deadline = time.monotonic() + self.VERIFICATION_TIMEOUT

            async def safe_content() -> str:
                for _ in range(5):
                    try:
                        return await page.content()
                    except Exception:
                        await asyncio.sleep(1)
                return await page.content()

            html = await safe_content()
            # 循环等待 Cloudflare 验证通过（与 HanimeScraper 完全一致）
            while looks_like_blocked_page(html) and time.monotonic() < deadline:
                print("[+] 等待 Cloudflare 验证通过…")
                await asyncio.sleep(2)
                html = await safe_content()

            if looks_like_blocked_page(html):
                raise RuntimeError("Cloudflare 验证超时，请在弹出的浏览器窗口中手动完成验证后重试")

            if not looks_like_anidb_content(html):
                raise RuntimeError("页面内容不像 anidb，可能被拦截")

            # 如果是成人内容警告页，引导用户登录并开启成人内容设置
            if is_adult_warning_page(html):
                print()
                print("=" * 60)
                print("[!] AniDB 需要登录且开启成人内容权限才能查看该页面。")
                print("    请在已打开的浏览器窗口中依次完成：")
                print("    1. 点击右上角 'login'，输入账号密码登录")
                print("    2. 登录后访问：https://anidb.net/user/profile/settings")
                print("       找到 'Adult Content' 选项并启用")
                print("    3. 然后在浏览器中访问目标地址：")
                print(f"       {url}")
                print("    4. 确认页面显示动漫详情后，脚本将自动继续")
                print("=" * 60)
                print()

                # 等待直到目标 URL 上出现真实动漫数据（最多10分钟）
                data_deadline = time.monotonic() + 600
                while time.monotonic() < data_deadline:
                    await asyncio.sleep(4)
                    # 检查浏览器当前 URL，如果用户已导航到目标页再检测
                    try:
                        current_url = page.url
                    except Exception:
                        current_url = ""
                    html = await safe_content()
                    # 判断是否拿到了真实的动漫数据（不再是警告页）
                    if has_real_anime_data(html):
                        print("[+] 检测到动漫详情数据，继续抓取！")
                        break
                    if is_adult_warning_page(html):
                        print(f"[+] 仍在警告页，请在浏览器完成以上步骤… (剩余 {int(data_deadline - time.monotonic())}s)")
                    else:
                        # 用户可能在其他页面（登录页/设置页），等待其导航回目标 URL
                        print(f"[+] 请导航到目标 URL: {url}")
                        try:
                            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        except Exception:
                            pass
                else:
                    print("[!] 等待超时，保存当前页面内容（可能数据不完整）")

            return html

        except Exception as exc:
            if not _retried and is_browser_closed_error(exc):
                import logging
                logging.getLogger(__name__).warning("浏览器意外关闭，正在重启… (%s)", exc)
                await self._reset_browser()
                return await self._fetch_locked(url, _retried=True)
            raise

    async def _ensure_browser(self, first_url: str) -> None:
        if self._context:
            return
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()

        # 与 HanimeScraper.ensure_browser 完全相同：
        # headless=False，使用系统真实浏览器（优先 msedge/chrome），data_dir 持久化
        data_dir = ROOT / ".playwright_data_anidb"
        channels = _launch_channel_order("msedge")
        last_error = None
        for channel in channels:
            try:
                kwargs = {} if channel == "chromium" else {"channel": channel}
                self._context = await self._playwright.chromium.launch_persistent_context(
                    str(data_dir),
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled", "--start-minimized"],
                    **kwargs,
                )
                break
            except Exception as exc:
                last_error = exc

        if self._context is None and last_error is not None:
            raise last_error

        if self._context.pages:
            self._session_page = self._context.pages[0]
        else:
            self._session_page = await self._context.new_page()

        # 先导航到域名首页让 Cloudflare 建立信任（同 HanimeScraper.ensure_browser 打开 hanime1.me）
        await self._session_page.goto("https://anidb.net/", wait_until="domcontentloaded", timeout=60000)

    async def _reset_browser(self) -> None:
        try:
            if self._context:
                await self._context.close()
        except Exception:
            pass
        self._context = None
        self._session_page = None
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        self._playwright = None

    async def close(self) -> None:
        await self._reset_browser()


def _available_channels() -> list[str]:
    import shutil, os
    from pathlib import Path as P

    def exe_exists(name: str) -> bool:
        if shutil.which(name):
            return True
        for root_key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            root = os.environ.get(root_key)
            if not root:
                continue
            candidates = {
                "msedge.exe": P(root) / "Microsoft/Edge/Application/msedge.exe",
                "chrome.exe": P(root) / "Google/Chrome/Application/chrome.exe",
            }
            if name in candidates and candidates[name].exists():
                return True
        return False

    result = []
    if exe_exists("msedge") or exe_exists("msedge.exe"):
        result.append("msedge")
    if exe_exists("chrome") or exe_exists("chrome.exe"):
        result.append("chrome")
    result.append("chromium")
    return result


def _launch_channel_order(selected: str) -> list[str]:
    ordered = [selected]
    for ch in _available_channels():
        if ch not in ordered:
            ordered.append(ch)
    if "chromium" not in ordered:
        ordered.append("chromium")
    return ordered


# ──────────────────────────────────────────────
# HTML 解析
# ──────────────────────────────────────────────

def _text(node) -> str:
    return node.text(strip=True) if node else ""


def _attr(node, name: str) -> str:
    return node.attributes.get(name, "") if node else ""


def _abs(href: str, base: str = "https://anidb.net") -> str:
    if not href:
        return ""
    return href if href.startswith("http") else (base + href if href.startswith("/") else href)


def parse_anidb_page(html: str, url: str) -> dict:
    tree = HTMLParser(html)
    data: dict = {
        "url": url,
        "raw_title": "",
        "titles": [],
        "info": {},
        "description": "",
        "episodes": [],
        "characters": [],
        "staff": [],
        "tags": [],
        "relations": [],
        "ratings": {},
        "links": [],
        "images": [],
    }

    # 主标题
    for sel in ("h1.anime span[itemprop='name']", "h1.anime", "h1", "title"):
        node = tree.css_first(sel)
        if node:
            data["raw_title"] = _text(node)
            break

    # 多语言标题（#tab_2_pane 或 table.titles）
    for row in tree.css("table.titles tr, #tab_2_pane tr, div.titles tr"):
        cells = row.css("td")
        if len(cells) >= 2:
            lang = _text(cells[0])
            name = _text(cells[1])
            if name:
                data["titles"].append({"lang": lang, "title": name})

    # 基本信息定义列表
    for row in tree.css("div.g_definitionlist tr, table.g_definitionlist tr, div.data tr"):
        key_node = row.css_first("td.key, th, td:first-child")
        val_node = row.css_first("td.value, td:last-child")
        if key_node and val_node and key_node is not val_node:
            k = _text(key_node).rstrip(":")
            v = _text(val_node)
            if k and v:
                data["info"][k] = v

    # 简介
    for sel in (
        "div.desc[itemprop='description']",
        "div[itemprop='description']",
        "div.synopsis",
        "#tab_1_pane div.desc",
        ".g_bubble .desc",
    ):
        node = tree.css_first(sel)
        if node:
            data["description"] = _text(node)
            break

    # 剧集列表
    for row in tree.css("#episodelist tr[id^='ep'], table#eplist tr[id^='ep'], tr.ep-row"):
        num_node = row.css_first("td.no a, td.no, td[class*='epno']")
        title_nodes = row.css("td.title label, td.title span, td.title a, td[class*='title'] label")
        date_node = row.css_first("td.date, td[class*='date']")
        ep = {
            "number": _text(num_node),
            "titles": [_text(t) for t in title_nodes if _text(t)],
            "airdate": _text(date_node),
        }
        if ep["number"] or ep["titles"]:
            data["episodes"].append(ep)

    # 角色
    for row in tree.css("div.characters tr, #tab_3_pane tr, table.characterlist tr"):
        name_node = row.css_first("td.name a, td.value a")
        type_node = row.css_first("td.type, td.key")
        img_node = row.css_first("img")
        char = {
            "name": _text(name_node),
            "url": _abs(_attr(name_node, "href")),
            "type": _text(type_node),
            "image": _abs(_attr(img_node, "src") or _attr(img_node, "data-src")),
        }
        if char["name"]:
            data["characters"].append(char)

    # 制作人员
    for row in tree.css("div.staff tr, #tab_4_pane tr, table.stafflist tr"):
        name_node = row.css_first("td.name a, td.value a")
        role_node = row.css_first("td.role, td.key")
        staff = {
            "name": _text(name_node),
            "url": _abs(_attr(name_node, "href")),
            "role": _text(role_node),
        }
        if staff["name"]:
            data["staff"].append(staff)

    # 标签
    for node in tree.css("div.tags span.tag, ul.tags li a, .tag a, span.tagname"):
        t = _text(node)
        if t and t not in data["tags"]:
            data["tags"].append(t)

    # 相关作品
    for row in tree.css("div.related tr, table.related tr, #tab_5_pane tr"):
        link_node = row.css_first("td.name a, a[href*='/anime/']")
        if link_node:
            data["relations"].append({
                "title": _text(link_node),
                "url": _abs(_attr(link_node, "href")),
                "type": _text(row.css_first("td.type, td.relation")),
            })

    # 评分
    for sel in ("span[itemprop='ratingValue']", "span.value.rating", "div.ratings span.value"):
        node = tree.css_first(sel)
        if node:
            data["ratings"]["value"] = _text(node)
            break
    for sel in ("span[itemprop='ratingCount']", "span.count"):
        node = tree.css_first(sel)
        if node:
            data["ratings"]["votes"] = _text(node)
            break

    # 所有超链接（去重）
    seen_hrefs: set[str] = set()
    for a in tree.css("a[href]"):
        href = _abs(_attr(a, "href"))
        if href and href not in seen_hrefs and not href.startswith("javascript"):
            seen_hrefs.add(href)
            data["links"].append({"text": _text(a), "url": href})

    # 图片
    seen_imgs: set[str] = set()
    for img in tree.css("img[src], img[data-src]"):
        src = _abs(_attr(img, "src") or _attr(img, "data-src"))
        if src and src not in seen_imgs:
            seen_imgs.add(src)
            data["images"].append(src)

    return data


# ──────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────

async def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else TARGET_URL
    anime_id_match = re.search(r"/anime/(\d+)", url)
    id_str = anime_id_match.group(1) if anime_id_match else "unknown"

    scraper = AnidbScraper()
    try:
        print(f"[+] 目标: {url}")
        html = await scraper.fetch_html(url)
    finally:
        await scraper.close()

    # 保存原始 HTML
    html_path = ROOT / f"anidb_{id_str}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"[+] 原始 HTML 已保存: {html_path}")

    # 解析并保存 JSON
    print("[+] 解析页面数据…")
    data = parse_anidb_page(html, url)

    json_path = ROOT / f"anidb_{id_str}.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] JSON 数据已保存: {json_path}")

    print("\n===== 抓取结果摘要 =====")
    print(f"  标题:      {data['raw_title'] or '(未解析)'}")
    print(f"  多语言标题: {len(data['titles'])} 条")
    print(f"  基本信息:  {len(data['info'])} 项")
    print(f"  剧集数:    {len(data['episodes'])} 集")
    print(f"  角色数:    {len(data['characters'])} 个")
    print(f"  制作人员:  {len(data['staff'])} 人")
    print(f"  标签:      {len(data['tags'])} 个")
    print(f"  相关作品:  {len(data['relations'])} 部")
    print(f"  链接总数:  {len(data['links'])} 个")
    print(f"  图片总数:  {len(data['images'])} 张")
    if data["info"]:
        print("\n  基本信息字段:")
        for k, v in list(data["info"].items())[:15]:
            try:
                print(f"    {k}: {v}")
            except UnicodeEncodeError:
                print(f"    {k}: {v.encode('ascii', 'replace').decode()}")
    if data["ratings"]:
        try:
            print(f"\n  评分: {data['ratings']}")
        except UnicodeEncodeError:
            pass
    print(f"\n输出文件:")
    print(f"  {json_path}")
    print(f"  {html_path}")


if __name__ == "__main__":
    asyncio.run(main())
