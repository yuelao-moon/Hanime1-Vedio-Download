"""
从 AniDB 页面的 Resources 区域提取所有外部链接，
按域名路由到对应的免费 API，抓取结构化数据。

支持的站点：
  - MyAnimeList (MAL)    → Jikan API（免费，无需 key）
  - TMDB                 → TMDB API（免费，需要 key，或无 key 抓页面）
  - Anime News Network   → ANN API XML（免费）
  - AniList              → GraphQL API（免费）
  - DLsite               → 解析产品页
  - 其他站点             → 只保存链接+标题（不抓取）

用法:
  python scrape_resources.py anidb_8727.html        # 从已有 HTML 文件
  python scrape_resources.py https://anidb.net/...  # 直接从网络（需先跑 scrape_anidb.py）
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import httpx
from selectolax.parser import HTMLParser

ROOT = Path(__file__).parent

# TMDB API key（可选：填入后可获取更多数据，留空则解析 HTML 页面）
TMDB_API_KEY = ""

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ──────────────────────────────────────────────
# 第一步：从 AniDB HTML 精准提取 Resources 链接
# ──────────────────────────────────────────────

def extract_resource_links(html: str) -> list[dict]:
    """
    专门解析 <tr class="resources"> 内的所有外部链接。
    返回: [{"site": "MAL", "url": "...", "group": "official/thirdparty"}]
    """
    tree = HTMLParser(html)
    resources = []

    row = tree.css_first("tr.resources, tr.g_odd.resources")
    if not row:
        return resources

    for group_div in row.css("div.group"):
        # 判断分组：官方 or 第三方
        cls = group_div.attributes.get("class", "")
        if "official" in cls:
            group = "official"
        elif "thirdparty" in cls:
            group = "thirdparty"
        else:
            group = "other"

        for a in group_div.css("a[href]"):
            href = a.attributes.get("href", "").strip()
            if not href or href.startswith("javascript") or "anidb.net" in href:
                continue
            # 从 title 或 class 或文字提取站点名
            site_name = (
                a.attributes.get("title", "")
                or a.text(strip=True)
                or _guess_site_name(href)
            )
            resources.append({
                "site": site_name,
                "url": href,
                "group": group,
            })

    return resources


def _guess_site_name(url: str) -> str:
    """从 URL 域名猜测站点名称。"""
    host = urlparse(url).netloc.lower()
    mapping = {
        "myanimelist.net": "MAL",
        "animenewsnetwork.com": "ANN",
        "themoviedb.org": "TMDB",
        "anilist.co": "AniList",
        "thetvdb.com": "TVDB",
        "tvdb.com": "TVDB",
        "imdb.com": "IMDb",
        "bangumi.tv": "Bangumi",
        "bgm.tv": "Bangumi",
        "vndb.org": "VNDB",
        "anisearch.com": "AniSearch",
        "kitsu.io": "Kitsu",
        "dlsite.com": "DLsite",
        "web.archive.org": "Wayback",
    }
    for domain, name in mapping.items():
        if domain in host:
            return name
    # 取主域名作为名字
    parts = host.replace("www.", "").split(".")
    return parts[0].upper() if parts else host


# ──────────────────────────────────────────────
# 第二步：按域名路由到各站点抓取逻辑
# ──────────────────────────────────────────────

async def fetch_resource_data(client: httpx.AsyncClient, resource: dict) -> dict:
    """根据站点名路由到对应的抓取函数，失败时返回原始链接信息。"""
    site = resource["site"]
    url = resource["url"]
    # 始终同时用域名进行二次确认，防止站点名识别不准
    domain_site = _guess_site_name(url)
    effective_site = site if site not in ("(1)", "", "text") else domain_site

    result = {"site": effective_site, "url": url, "group": resource["group"], "data": None, "error": None}

    try:
        if effective_site == "MAL":
            result["data"] = await fetch_mal(client, url)
        elif effective_site == "TMDB":
            result["data"] = await fetch_tmdb(client, url)
        elif effective_site == "ANN":
            result["data"] = await fetch_ann(client, url)
        elif effective_site == "AniList":
            result["data"] = await fetch_anilist(client, url)
        elif effective_site == "DLsite":
            result["data"] = await fetch_dlsite(client, url)
        else:
            # 未知站点：只获取页面标题和描述，不深度解析
            result["data"] = await fetch_generic_meta(client, url)
    except Exception as e:
        result["error"] = str(e)
        print(f"  [!] {effective_site} 抓取失败: {e}")

    return result


# ── MAL：使用 Jikan API（完全免费，无需 key）──

async def fetch_mal(client: httpx.AsyncClient, url: str) -> dict:
    """MyAnimeList → Jikan v4 公开 API"""
    # 从 URL 提取 anime ID: /anime/11969
    match = re.search(r"/anime/(\d+)", url)
    if not match:
        return {"url": url, "note": "无法从 URL 提取 MAL ID"}
    mal_id = match.group(1)
    api_url = f"https://api.jikan.moe/v4/anime/{mal_id}"
    print(f"  [MAL] 调用 Jikan API: {api_url}")
    resp = await client.get(api_url, headers={"Accept": "application/json"})
    resp.raise_for_status()
    d = resp.json().get("data", {})
    return {
        "mal_id": d.get("mal_id"),
        "title": d.get("title"),
        "title_japanese": d.get("title_japanese"),
        "type": d.get("type"),
        "episodes": d.get("episodes"),
        "status": d.get("status"),
        "aired": d.get("aired", {}).get("string"),
        "score": d.get("score"),
        "scored_by": d.get("scored_by"),
        "rank": d.get("rank"),
        "synopsis": d.get("synopsis"),
        "genres": [g["name"] for g in d.get("genres", [])],
        "themes": [t["name"] for t in d.get("themes", [])],
        "demographics": [x["name"] for x in d.get("demographics", [])],
        "studios": [s["name"] for s in d.get("studios", [])],
        "image": d.get("images", {}).get("jpg", {}).get("large_image_url"),
        "trailer": d.get("trailer", {}).get("url"),
        "url": d.get("url"),
        "source_url": url,
    }


# ── TMDB：优先用 API，无 key 时解析 meta 标签 ──

async def fetch_tmdb(client: httpx.AsyncClient, url: str) -> dict:
    """The Movie Database → 官方 API 或 og: meta 标签"""
    # 从 URL 判断类型和 ID：/tv/98094 或 /movie/12345
    match = re.search(r"/(tv|movie)/(\d+)", url)
    if not match:
        return {"url": url, "note": "无法从 URL 提取 TMDB ID"}
    media_type, tmdb_id = match.group(1), match.group(2)

    if TMDB_API_KEY:
        api_url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&language=zh-CN&append_to_response=credits,videos"
        print(f"  [TMDB] 调用官方 API: {api_url}")
        resp = await client.get(api_url)
        resp.raise_for_status()
        d = resp.json()
        return {
            "tmdb_id": d.get("id"),
            "title": d.get("name") or d.get("title"),
            "original_title": d.get("original_name") or d.get("original_title"),
            "overview": d.get("overview"),
            "status": d.get("status"),
            "first_air_date": d.get("first_air_date") or d.get("release_date"),
            "vote_average": d.get("vote_average"),
            "vote_count": d.get("vote_count"),
            "genres": [g["name"] for g in d.get("genres", [])],
            "poster": f"https://image.tmdb.org/t/p/original{d['poster_path']}" if d.get("poster_path") else None,
            "number_of_episodes": d.get("number_of_episodes"),
            "number_of_seasons": d.get("number_of_seasons"),
            "source_url": url,
        }
    else:
        # 无 key：从页面 og:/meta 标签抓基本信息
        print(f"  [TMDB] 解析页面 meta 标签（未配置 API key）: {url}")
        return await fetch_generic_meta(client, url)


# ── ANN：使用官方 XML API ──

async def fetch_ann(client: httpx.AsyncClient, url: str) -> dict:
    """Anime News Network → 官方 XML API（免费）"""
    match = re.search(r"[?&]id=(\d+)", url)
    if not match:
        return {"url": url, "note": "无法从 URL 提取 ANN ID"}
    ann_id = match.group(1)
    api_url = f"https://cdn.animenewsnetwork.com/encyclopedia/api.xml?anime={ann_id}"
    print(f"  [ANN] 调用官方 XML API: {api_url}")
    resp = await client.get(api_url)
    resp.raise_for_status()
    # 简单解析 XML
    xml = resp.text
    tree = HTMLParser(xml)

    def xml_text(selector: str) -> str:
        n = tree.css_first(selector)
        return n.text(strip=True) if n else ""

    def xml_attrs(selector: str) -> list[dict]:
        return [dict(n.attributes) for n in tree.css(selector)]

    title_nodes = tree.css("info[type='Main title'], info[type='Alternative title']")
    titles = [{"type": n.attributes.get("type", ""), "lang": n.attributes.get("lang", ""), "title": n.text(strip=True)} for n in title_nodes]

    return {
        "ann_id": ann_id,
        "titles": titles,
        "vintage": xml_text("info[type='Vintage']"),
        "genres": [n.text(strip=True) for n in tree.css("info[type='Genres']")],
        "themes": [n.text(strip=True) for n in tree.css("info[type='Themes']")],
        "plot_summary": xml_text("info[type='Plot Summary']"),
        "picture": xml_text("info[type='Picture']") or (tree.css_first("episode img") or None) and "",
        "source_url": url,
    }


# ── AniList：GraphQL API ──

async def fetch_anilist(client: httpx.AsyncClient, url: str) -> dict:
    """AniList → 公开 GraphQL API（免费）"""
    match = re.search(r"/anime/(\d+)", url)
    if not match:
        return {"url": url, "note": "无法从 URL 提取 AniList ID"}
    al_id = int(match.group(1))
    query = """
    query ($id: Int) {
      Media(id: $id, type: ANIME) {
        id title { romaji english native }
        episodes status format
        startDate { year month day }
        averageScore popularity
        genres description(asHtml: false)
        coverImage { extraLarge }
        studios(isMain: true) { nodes { name } }
      }
    }"""
    print(f"  [AniList] 调用 GraphQL API, id={al_id}")
    resp = await client.post(
        "https://graphql.anilist.co",
        json={"query": query, "variables": {"id": al_id}},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    resp.raise_for_status()
    m = resp.json().get("data", {}).get("Media", {})
    if not m:
        return {"url": url, "note": "AniList 未找到数据"}
    sd = m.get("startDate", {})
    return {
        "anilist_id": m.get("id"),
        "title_romaji": m.get("title", {}).get("romaji"),
        "title_english": m.get("title", {}).get("english"),
        "title_native": m.get("title", {}).get("native"),
        "format": m.get("format"),
        "status": m.get("status"),
        "episodes": m.get("episodes"),
        "start_date": f"{sd.get('year','?')}-{sd.get('month','?'):02}-{sd.get('day','?'):02}" if sd.get("year") else None,
        "average_score": m.get("averageScore"),
        "popularity": m.get("popularity"),
        "genres": m.get("genres", []),
        "description": m.get("description"),
        "cover_image": m.get("coverImage", {}).get("extraLarge"),
        "studios": [s["name"] for s in m.get("studios", {}).get("nodes", [])],
        "source_url": url,
    }


# ── DLsite：解析产品页 ──

async def fetch_dlsite(client: httpx.AsyncClient, url: str) -> dict:
    """DLsite 产品页面解析"""
    print(f"  [DLsite] 解析产品页: {url}")
    resp = await client.get(url, headers={**HEADERS, "Accept-Language": "ja-JP,ja;q=0.9"})
    if resp.status_code >= 400:
        return {"url": url, "note": f"HTTP {resp.status_code}"}
    tree = HTMLParser(resp.text)

    def t(sel: str) -> str:
        n = tree.css_first(sel)
        return n.text(strip=True) if n else ""

    # 提取产品 ID
    match = re.search(r"product_id/(\w+)", url)
    product_id = match.group(1) if match else ""

    return {
        "product_id": product_id,
        "title": t("h1#work_name, h1.work_name") or t("title"),
        "circle": t("span.maker_name a, a.maker_name"),
        "genre": [n.text(strip=True) for n in tree.css("div.main_genre a, .genre a")],
        "price": t("span.price, .work_price"),
        "rating": t("span.point, .work_rating"),
        "description": t("div.work_parts_area, #work_parts"),
        "cover_image": tree.css_first("meta[property='og:image']").attributes.get("content", "") if tree.css_first("meta[property='og:image']") else "",
        "source_url": url,
    }


# ── 通用 meta 标签提取（适用于不认识的站点）──

async def fetch_generic_meta(client: httpx.AsyncClient, url: str) -> dict:
    """从任意页面提取 og:/twitter:/标准 meta 标签的基本信息。"""
    print(f"  [通用] 提取 meta 标签: {url}")
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        if resp.status_code >= 400:
            return {"url": url, "note": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"url": url, "note": str(e)}

    tree = HTMLParser(resp.text)

    def meta(prop: str) -> str:
        for attr in ("property", "name"):
            n = tree.css_first(f'meta[{attr}="{prop}"]')
            if n:
                return n.attributes.get("content", "").strip()
        return ""

    title_node = tree.css_first("title")
    return {
        "title": meta("og:title") or (title_node.text(strip=True) if title_node else ""),
        "description": meta("og:description") or meta("description"),
        "image": meta("og:image"),
        "site_name": meta("og:site_name"),
        "url": meta("og:url") or url,
        "source_url": url,
    }


# ──────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────

async def main() -> None:
    # 输入可以是本地 HTML 文件路径，也可以是直接传入 HTML 字符串
    arg = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "anidb_8727.html")

    if Path(arg).exists():
        html = Path(arg).read_text(encoding="utf-8")
        out_name = Path(arg).stem
    else:
        print(f"[!] 文件不存在: {arg}")
        return

    print(f"[+] 从 {arg} 提取 Resources 链接…")
    resources = extract_resource_links(html)

    if not resources:
        print("[!] 未找到任何 Resources 链接，请确认 HTML 是完整的 AniDB 动漫页面")
        return

    print(f"[+] 找到 {len(resources)} 个资源链接：")
    for r in resources:
        print(f"    [{r['group']:10}] {r['site']:12} → {r['url']}")

    print(f"\n[+] 开始逐一抓取…")
    results = []
    async with httpx.AsyncClient(
        timeout=30,
        follow_redirects=True,
        headers=HEADERS,
    ) as client:
        for resource in resources:
            print(f"\n>>> {resource['site']} ({resource['url']})")
            result = await fetch_resource_data(client, resource)
            results.append(result)
            # 礼貌性延迟，避免被限速
            await asyncio.sleep(1)

    # 保存结果
    out_path = ROOT / f"{out_name}_resources.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[+] 资源数据已保存: {out_path}")

    # 打印摘要
    print("\n===== 资源抓取摘要 =====")
    for r in results:
        status = "OK" if r["data"] and not r["error"] else f"FAIL: {r.get('error','')}"
        title = ""
        if r["data"]:
            title = (
                r["data"].get("title")
                or r["data"].get("title_romaji")
                or r["data"].get("note", "")
            ) or ""
        try:
            print(f"  [{r['site']:12}] {status}  {title}")
        except UnicodeEncodeError:
            print(f"  [{r['site']:12}] {status}  {title.encode('ascii','replace').decode()}")


if __name__ == "__main__":
    asyncio.run(main())
