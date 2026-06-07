"""
AniDB 番剧 NFO 生成器
从 AniDB 番剧页面抓取数据，生成 Kodi/Jellyfin 兼容的 NFO 文件结构。

目录结构：
  <标题>/
  ├── tvshow.nfo
  ├── poster.jpg
  ├── fanart.jpg
  └── Season 01/
      ├── S01E01 - <集标题>.nfo
      └── S01E02 - <集标题>.nfo

用法:
  python anidb_nfo.py <URL 或 anime_id>
  python anidb_nfo.py 18184
  python anidb_nfo.py https://anidb.net/anime/18184
"""
from __future__ import annotations

import asyncio
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

import httpx
from selectolax.parser import HTMLParser

ROOT = Path(__file__).parent

# ─────────────────────────────────────────────────────────
# 语言检测
# ─────────────────────────────────────────────────────────

def detect_lang(text: str) -> str:
    """
    从字符集判断语言：
      ja  - 含平假名 / 片假名
      zh  - 含汉字但无假名（中文简繁）
      ko  - 含韩文
      ru  - 含西里尔字母
      en  - 拉丁字母
      other - 其他
    """
    if re.search(r'[぀-ゟ゠-ヿ]', text):   # 平/片假名
        return 'ja'
    if re.search(r'[一-鿿㐀-䶿豈-﫿]', text):  # 汉字
        return 'zh'
    if re.search(r'[가-힯ᄀ-ᇿ㄰-㆏]', text):  # 韩文
        return 'ko'
    if re.search(r'[Ѐ-ӿ]', text):                  # 西里尔
        return 'ru'
    if re.search(r'[a-zA-Z]', text):
        return 'en'
    return 'other'


def select_best_title(title_list: list[dict]) -> str:
    """
    按优先级 zh > ja > en 选出最佳标题；
    若三者都不存在，取列表第一项。
    title_list: [{"title": "...", "lang": "zh/ja/en/other"}]
    """
    for lang in ('zh', 'ja', 'en'):
        for t in title_list:
            if t['lang'] == lang:
                return t['title']
    return title_list[0]['title'] if title_list else ''


# ─────────────────────────────────────────────────────────
# AniDB HTML 解析（精确 CSS 选择器，全部基于实际 HTML 结构）
# ─────────────────────────────────────────────────────────

def parse_anidb_html(html: str, anime_id: str) -> dict:
    tree = HTMLParser(html)
    data: dict = {
        'anime_id': anime_id,
        'main_title': '',
        'titles': [],           # [{"title": ..., "lang": ..., "source": "official/synonym"}]
        'selected_title': '',
        'original_title': '',   # 日语官方标题（用于 originaltitle 字段）
        'anime_type': '',       # OVA / TV Series / Movie …
        'episode_count': 1,
        'year': '',
        'season_text': '',
        'tags': [],
        'rating': '',
        'votes': '',
        'description': '',
        'poster_url': '',
        'episodes': [],         # [{"num":1, "eid":..., "title_en":..., "title_alt":..., "duration":..., "airdate":...}]
    }

    # ── 主标题（精确用 tr.romaji 避免匹配到页面其他 schema 标注）──
    main_node = tree.css_first("tr.romaji span[itemprop='name']")
    data['main_title'] = main_node.text(strip=True) if main_node else ''

    # ── Official Title（含语言标签），用 set 去重 ──────────
    seen_titles: set[str] = set()
    for tr in tree.css("tr.official"):
        flag = tr.css_first("span.i_icon[class*='i_audio_']")
        lang = 'other'
        if flag:
            cls = flag.attributes.get('class', '')
            if 'i_audio_ja' in cls:
                lang = 'ja'
            elif 'i_audio_zh' in cls or 'i_audio_x-jat' in cls:
                lang = 'zh'
            elif 'i_audio_en' in cls:
                lang = 'en'
        label = tr.css_first("label[itemprop='alternateName']")
        if label:
            t = label.text(strip=True)
            if t and t not in seen_titles:
                seen_titles.add(t)
                data['titles'].append({'title': t, 'lang': lang, 'source': 'official'})
                if lang == 'ja' and not data['original_title']:
                    data['original_title'] = t

    # ── Synonym（逗号分隔，逐一检测语言）──────────────────
    syn_td = tree.css_first("tr.syn td.value")
    if syn_td:
        raw = syn_td.text(strip=True)
        for part in re.split(r',\s+', raw):
            part = part.strip()
            if part and part not in seen_titles:
                seen_titles.add(part)
                data['titles'].append({'title': part, 'lang': detect_lang(part), 'source': 'synonym'})

    # 如果没有 Official Title，把 Main Title 也加进去
    if not data['titles'] and data['main_title']:
        data['titles'].append({'title': data['main_title'], 'lang': detect_lang(data['main_title']), 'source': 'main'})

    data['selected_title'] = select_best_title(data['titles'])

    # ── Type + 集数 ───────────────────────────────────────
    # 精准匹配含 itemprop="numberOfEpisodes" 的 Type 行（排除 mylist 表单行）
    ep_span = tree.css_first("span[itemprop='numberOfEpisodes']")
    if ep_span:
        type_td = ep_span.parent  # <td class="value">
        type_full = type_td.text(strip=True)   # "OVA, 2 episodes"
        parts = [p.strip() for p in type_full.split(',')]
        data['anime_type'] = parts[0]           # "OVA"
        try:
            data['episode_count'] = int(ep_span.text(strip=True))
        except ValueError:
            data['episode_count'] = 1
    else:
        # 无 numberOfEpisodes span：类型行只有类型文字，集数为 1
        type_tr = tree.css_first("tr.type td.value")
        if type_tr:
            raw = type_tr.text(strip=True)
            # 只取不含 <select> 的那个（含 select 是表单行，跳过）
            if not type_tr.css_first("select"):
                data['anime_type'] = raw.split(',')[0].strip()
                data['episode_count'] = 1

    # ── Year ──────────────────────────────────────────────
    start_span = tree.css_first("span[itemprop='startDate']")
    if start_span:
        data['year'] = start_span.attributes.get('content', '')[:4]  # "2024-02-23" → "2024"

    # ── Season ────────────────────────────────────────────
    season_td = tree.css_first("tr.season td.value a")
    data['season_text'] = season_td.text(strip=True) if season_td else ''

    # ── Tags（只取 tagname，不要描述文字）────────────────
    data['tags'] = [n.text(strip=True) for n in tree.css("tr.tags span.tagname") if n.text(strip=True)]

    # ── Rating ────────────────────────────────────────────
    rating_node = tree.css_first("span[itemprop='ratingValue']")
    data['rating'] = rating_node.text(strip=True) if rating_node else ''
    votes_node = tree.css_first("span[itemprop='ratingCount']")
    if votes_node:
        data['votes'] = re.sub(r'\D', '', votes_node.text(strip=True))  # 只保留数字

    # ── Description ───────────────────────────────────────
    desc_node = tree.css_first("div[itemprop='description'], span[itemprop='description']")
    data['description'] = desc_node.text(strip=True) if desc_node else ''

    # ── Poster URL ────────────────────────────────────────
    poster_img = tree.css_first("div.image div.container img[itemprop='image']")
    if poster_img:
        data['poster_url'] = poster_img.attributes.get('src', '')
    if not data['poster_url']:
        meta_img = tree.css_first("meta[property='og:image']")
        if meta_img:
            data['poster_url'] = meta_img.attributes.get('content', '')

    # ── 剧集列表 ──────────────────────────────────────────
    for ep_tr in tree.css("tr[id^='eid_']"):
        # 集号
        ep_num_node = ep_tr.css_first("abbr[itemprop='episodeNumber']")
        ep_num_str = ep_num_node.text(strip=True) if ep_num_node else ''
        try:
            ep_num = int(ep_num_str)
        except ValueError:
            continue  # 跳过非正规集（Special、OP 等）

        # 集标题：主标题在 label，去掉 span.alternative 子节点的文字
        label_node = ep_tr.css_first("label[itemprop='name']")
        ep_title_en = ''
        ep_title_alt = ''
        if label_node:
            alt_node = label_node.css_first("span.alternative")
            if alt_node:
                ep_title_alt = alt_node.text(strip=True).strip('()')
            # 主标题 = label 全文 - alt 文字
            full = label_node.text(strip=True)
            ep_title_en = full.replace(alt_node.text(strip=True) if alt_node else '', '').strip()

        # 时长
        dur_node = ep_tr.css_first("td.duration")
        duration_str = dur_node.text(strip=True).replace('m', '').strip() if dur_node else ''
        try:
            duration_min = int(duration_str)
        except ValueError:
            duration_min = 0

        # 播出日期
        date_td = ep_tr.css_first("td.date.airdate")
        airdate = date_td.attributes.get('content', '') if date_td else ''

        # AniDB episode ID
        eid = ep_tr.attributes.get('data-anidb-eid', '')

        data['episodes'].append({
            'num': ep_num,
            'eid': eid,
            'title_en': ep_title_en,
            'title_alt': ep_title_alt,      # 通常是日语
            'title_lang': detect_lang(ep_title_alt),
            'duration': duration_min,
            'airdate': airdate,
        })

    data['episodes'].sort(key=lambda e: e['num'])
    return data


# ─────────────────────────────────────────────────────────
# NFO XML 生成（Kodi / Jellyfin 标准）
# ─────────────────────────────────────────────────────────

def _indent_xml(elem: ET.Element) -> str:
    """返回格式化后的 XML 字符串（含声明头）。"""
    rough = ET.tostring(elem, encoding='unicode')
    dom = minidom.parseString(f'<?xml version="1.0" encoding="utf-8"?>{rough}')
    lines = dom.toprettyxml(indent='  ', encoding=None).splitlines()
    # minidom 会自己加声明行，去掉重复的
    result = '\n'.join(l for l in lines if l.strip() and not l.startswith('<?xml'))
    return '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n' + result


def _sub(parent: ET.Element, tag: str, text: str = '') -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


def generate_tvshow_nfo(data: dict) -> str:
    root = ET.Element('tvshow')

    _sub(root, 'title', data['selected_title'])
    _sub(root, 'originaltitle', data['original_title'] or data['main_title'])
    _sub(root, 'sorttitle', data['selected_title'])
    _sub(root, 'year', data['year'])
    _sub(root, 'season', '1')
    _sub(root, 'episode', str(data['episode_count']))
    _sub(root, 'plot', data['description'])
    _sub(root, 'genre', data['anime_type'])
    _sub(root, 'status', 'Ended' if data['episode_count'] > 0 else 'Continuing')

    # 标签（过滤掉描述性内容指示符）
    for tag in data['tags']:
        _sub(root, 'tag', tag)

    # 评分
    if data['rating']:
        ratings_el = ET.SubElement(root, 'ratings')
        rating_el = ET.SubElement(ratings_el, 'rating', name='anidb', max='10', default='true')
        _sub(rating_el, 'value', data['rating'])
        if data['votes']:
            _sub(rating_el, 'votes', data['votes'])

    # 缩略图
    thumb = ET.SubElement(root, 'thumb', aspect='poster')
    thumb.text = 'poster.jpg'
    fanart_el = ET.SubElement(root, 'fanart')
    fanart_thumb = ET.SubElement(fanart_el, 'thumb')
    fanart_thumb.text = 'fanart.jpg'

    # 唯一 ID
    uid = ET.SubElement(root, 'uniqueid', type='anidb', default='true')
    uid.text = data['anime_id']

    # 所有标题（供媒体库识别多语言）
    titles_el = ET.SubElement(root, 'titles')
    for t in data['titles']:
        t_el = ET.SubElement(titles_el, 'title', lang=t['lang'], source=t['source'])
        t_el.text = t['title']

    return _indent_xml(root)


def generate_episode_nfo(ep: dict, show_title: str, season: int = 1) -> str:
    root = ET.Element('episodedetails')

    # 集标题：优先用 alt（通常是日语），按语言优先级选
    alt_titles = []
    if ep['title_en']:
        alt_titles.append({'title': ep['title_en'], 'lang': detect_lang(ep['title_en'])})
    if ep['title_alt']:
        alt_titles.append({'title': ep['title_alt'], 'lang': ep['title_lang']})
    chosen_ep_title = select_best_title(alt_titles) if alt_titles else ep['title_en']

    _sub(root, 'title', chosen_ep_title)
    _sub(root, 'showtitle', show_title)
    _sub(root, 'season', str(season))
    _sub(root, 'episode', str(ep['num']))
    if ep['airdate']:
        _sub(root, 'aired', ep['airdate'])
    if ep['duration']:
        _sub(root, 'runtime', str(ep['duration']))
    _sub(root, 'plot', '')  # AniDB 主页不提供每集简介，留空

    # 备选标题（两种语言都保留）
    if ep['title_en'] or ep['title_alt']:
        titles_el = ET.SubElement(root, 'titles')
        if ep['title_en']:
            t = ET.SubElement(titles_el, 'title', lang=detect_lang(ep['title_en']))
            t.text = ep['title_en']
        if ep['title_alt']:
            t = ET.SubElement(titles_el, 'title', lang=ep['title_lang'])
            t.text = ep['title_alt']

    uid = ET.SubElement(root, 'uniqueid', type='anidb')
    uid.text = ep['eid']

    return _indent_xml(root)


def safe_filename(s: str) -> str:
    """替换文件名中的非法字符。"""
    return re.sub(r'[\\/:*?"<>|]', '_', s).strip('. ')


# ─────────────────────────────────────────────────────────
# 网络请求（复用 scrape_anidb.py 的浏览器逻辑）
# ─────────────────────────────────────────────────────────

def looks_like_blocked_page(html: str) -> bool:
    lower = (html or '').lower()
    return any(m in lower for m in (
        'attention required! | cloudflare', 'cloudflare ray id',
        'cf-challenge', 'cf-turnstile', 'just a moment',
        'checking your browser', 'verify you are human',
    ))


def has_real_anime_data(html: str) -> bool:
    lower = (html or '').lower()
    return (
        any(m in lower for m in ('g_definitionlist', 'itemprop="numberofpisodes"', 'eid_', 'itemprop="episode"'))
        and 'adult content warning' not in lower
    )


def is_adult_warning_page(html: str) -> bool:
    lower = (html or '').lower()
    return 'adult content warning' in lower and 'you have to be logged in' in lower


def is_browser_closed_error(exc: BaseException) -> bool:
    try:
        from playwright.async_api import TargetClosedError
        if isinstance(exc, TargetClosedError):
            return True
    except ImportError:
        pass
    msg = str(exc).lower()
    return any(p in msg for p in ('target closed', 'browser has been closed', 'browser closed',
                                   'connection closed', 'page has been closed'))


def _available_channels() -> list[str]:
    import shutil, os
    result = []
    for name, exe in (('msedge', 'msedge.exe'), ('chrome', 'chrome.exe')):
        if shutil.which(name) or shutil.which(exe):
            result.append(name)
            continue
        for key in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
            root = os.environ.get(key, '')
            paths = {'msedge.exe': 'Microsoft/Edge/Application/msedge.exe',
                     'chrome.exe': 'Google/Chrome/Application/chrome.exe'}
            if exe in paths and (Path(root) / paths[exe]).exists():
                result.append(name)
                break
    result.append('chromium')
    return list(dict.fromkeys(result))


async def fetch_html_with_browser(url: str, anime_id: str) -> str:
    """完全复用 scrape_anidb.py 的 AnidbScraper 浏览器逻辑。"""
    from playwright.async_api import async_playwright

    data_dir = ROOT / '.playwright_data_anidb'
    channels = _available_channels()
    context = None

    async with async_playwright() as pw:
        last_err = None
        for ch in channels:
            try:
                kwargs = {} if ch == 'chromium' else {'channel': ch}
                context = await pw.chromium.launch_persistent_context(
                    str(data_dir), headless=False,
                    args=['--disable-blink-features=AutomationControlled', '--start-minimized'],
                    **kwargs,
                )
                break
            except Exception as e:
                last_err = e
        if context is None:
            raise last_err

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto('https://anidb.net/', wait_until='domcontentloaded', timeout=60000)

        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        deadline = time.monotonic() + 180

        async def safe_content() -> str:
            for _ in range(5):
                try:
                    return await page.content()
                except Exception:
                    await asyncio.sleep(1)
            return await page.content()

        html = await safe_content()
        while looks_like_blocked_page(html) and time.monotonic() < deadline:
            print('[+] 等待 Cloudflare 验证…')
            await asyncio.sleep(2)
            html = await safe_content()

        if is_adult_warning_page(html):
            print()
            print('=' * 60)
            print('[!] 需要 AniDB 登录并开启成人内容权限。')
            print('    请在浏览器中：1.登录  2.设置允许成人内容')
            print(f'    3.导航到 {url}')
            print('=' * 60)
            data_deadline = time.monotonic() + 600
            while time.monotonic() < data_deadline:
                await asyncio.sleep(4)
                html = await safe_content()
                if has_real_anime_data(html):
                    print('[+] 检测到动漫数据，继续！')
                    break
                if not is_adult_warning_page(html):
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(2)
                    html = await safe_content()

        await context.close()
    return html


async def download_image(url: str, dest: Path) -> bool:
    """下载图片到指定路径。"""
    if not url:
        return False
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers={'Referer': 'https://anidb.net/'})
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            print(f'[+] 已下载: {dest.name} ({len(resp.content)//1024} KB)')
            return True
    except Exception as e:
        print(f'[!] 图片下载失败 ({url}): {e}')
        return False


# ─────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────

async def main() -> None:
    # 修复 Windows 控制台编码（输出中文/日文等）
    import sys as _sys
    if hasattr(_sys.stdout, 'reconfigure'):
        try:
            _sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    arg = sys.argv[1] if len(sys.argv) > 1 else '18184'

    # 解析 anime_id
    if arg.startswith('http'):
        m = re.search(r'/anime/(\d+)', arg)
        anime_id = m.group(1) if m else arg.split('/')[-1]
        url = arg
    else:
        anime_id = arg.strip('/')
        url = f'https://anidb.net/anime/{anime_id}'

    # 优先使用已有 HTML（减少重复抓取）
    cached_html = ROOT / f'anidb_{anime_id}.html'
    if cached_html.exists():
        print(f'[+] 使用缓存 HTML: {cached_html}')
        html = cached_html.read_text(encoding='utf-8')
        if not has_real_anime_data(html):
            print('[!] 缓存 HTML 不包含完整数据，重新抓取…')
            html = await fetch_html_with_browser(url, anime_id)
            cached_html.write_text(html, encoding='utf-8')
    else:
        print(f'[+] 抓取: {url}')
        html = await fetch_html_with_browser(url, anime_id)
        cached_html.write_text(html, encoding='utf-8')
        print(f'[+] HTML 已缓存: {cached_html}')

    # 解析数据
    print('[+] 解析 AniDB 数据…')
    data = parse_anidb_html(html, anime_id)

    # ── 打印解析摘要 ─────────────────────────────────────
    print()
    print('=' * 60)
    print(f'  主标题:    {data["main_title"]}')
    print(f'  选定标题:  {data["selected_title"]}')
    print(f'  日语标题:  {data["original_title"]}')
    print(f'  所有标题:')
    for t in data['titles']:
        print(f'    [{t["lang"]:5}|{t["source"]:8}] {t["title"]}')
    print(f'  类型:      {data["anime_type"]}')
    print(f'  集数:      {data["episode_count"]}')
    print(f'  年份:      {data["year"]}')
    print(f'  季节:      {data["season_text"]}')
    print(f'  评分:      {data["rating"]} ({data["votes"]} 票)')
    print(f'  标签数:    {len(data["tags"])}')
    print(f'  解析剧集:  {len(data["episodes"])} 集')
    print(f'  封面图:    {data["poster_url"]}')
    print('=' * 60)

    # ── 创建目录结构 ──────────────────────────────────────
    show_dir = ROOT / safe_filename(data['selected_title'])
    season_dir = show_dir / 'Season 01'
    show_dir.mkdir(exist_ok=True)
    season_dir.mkdir(exist_ok=True)
    print(f'\n[+] 输出目录: {show_dir}')

    # ── tvshow.nfo ────────────────────────────────────────
    tvshow_nfo_path = show_dir / 'tvshow.nfo'
    tvshow_nfo_path.write_text(generate_tvshow_nfo(data), encoding='utf-8')
    print(f'[+] 生成: tvshow.nfo')

    # ── poster.jpg & fanart.jpg ───────────────────────────
    await download_image(data['poster_url'], show_dir / 'poster.jpg')
    await download_image(data['poster_url'], show_dir / 'fanart.jpg')

    # ── 每集 .nfo ─────────────────────────────────────────
    if data['episodes']:
        for ep in data['episodes']:
            ep_title_safe = safe_filename(ep['title_en'] or ep['title_alt'] or f'Episode {ep["num"]}')
            nfo_name = f'S01E{ep["num"]:02d} - {ep_title_safe}.nfo'
            nfo_path = season_dir / nfo_name
            nfo_path.write_text(
                generate_episode_nfo(ep, data['selected_title']),
                encoding='utf-8'
            )
        print(f'[+] 生成: {len(data["episodes"])} 个集 NFO → Season 01/')
    else:
        print('[!] 未解析到剧集列表，跳过集 NFO 生成')
        print('    （AniDB 需登录后才显示剧集，或该番只有 1 集无列表）')

    # ── 打印目录树 ────────────────────────────────────────
    print()
    print('生成的文件结构:')
    for f in sorted(show_dir.rglob('*')):
        rel = f.relative_to(show_dir)
        depth = len(rel.parts) - 1
        print('  ' + '  ' * depth + ('📁 ' if f.is_dir() else '📄 ') + f.name)


if __name__ == '__main__':
    asyncio.run(main())
