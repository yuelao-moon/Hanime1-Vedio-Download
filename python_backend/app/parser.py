from __future__ import annotations

import re
from html import unescape
from urllib.parse import parse_qs, urljoin, urlparse

from selectolax.parser import HTMLParser, Node


BASE_URL = "https://hanime1.me"


def extract_video_page(page_url: str, html: str, download_html: str | None = None) -> dict:
    source_html = html or ""
    download_source = download_html or ""
    video_url = extract_first_stream(download_source) or extract_first_stream(source_html) or ""
    tree = HTMLParser(source_html)

    # Parse creator info
    creator_name = ""
    creator_avatar = ""
    creator_url = ""
    creator_id = ""
    
    user_link = tree.css_first('a[href*="/user/"]')
    if user_link:
        creator_url = clean_url(user_link.attributes.get("href", ""))
        if creator_url:
            match = re.search(r'/user/(\d+)', creator_url)
            if match:
                creator_id = match.group(1)
        
        imgs = user_link.css("img")
        if imgs:
            creator_avatar = imgs[-1].attributes.get("src", "")
            
        name_node = tree.css_first("#video-artist-name")
        if name_node:
            creator_name = name_node.text(strip=True)
        elif imgs:
            creator_name = imgs[-1].attributes.get("alt", "")

    return {
        "videoUrl": clean_url(video_url),
        "title": normalize_title(extract_title(tree)),
        "thumbnail": extract_thumbnail(tree),
        "videoId": extract_video_id(page_url),
        "playlist": extract_cards(tree.css("#video-playlist-wrapper a[href*='watch?v=']"), page_url),
        "relatedVideos": extract_related_videos(tree, page_url),
        "creator": {
            "name": creator_name,
            "avatar": creator_avatar,
            "url": creator_url,
            "id": creator_id
        } if (creator_name or creator_id) else None
    }



def parse_video_grid(html: str) -> list[dict[str, str]]:
    tree = HTMLParser(html or "")
    return extract_cards(tree.css("a[href*='watch?v=']"), BASE_URL)


def parse_home_hero(tree: HTMLParser) -> dict | None:
    wrapper = tree.css_first("#home-banner-wrapper")
    if not wrapper:
        return None
    
    title_node = wrapper.css_first("h1")
    title = title_node.text(strip=True) if title_node else ""
    
    meta_node = wrapper.css_first("h4")
    meta_text = meta_node.text(strip=True) if meta_node else ""
    
    creator = ""
    views = ""
    date = ""
    if meta_text:
        parts = [p.strip() for p in re.split(r'[•··]', meta_text)]
        if len(parts) >= 1:
            creator = parts[0]
        if len(parts) >= 2:
            views = parts[1]
        if len(parts) >= 3:
            date = parts[2]
            
    tags = []
    tags_div = wrapper.css_first("div")
    if tags_div:
        for span in tags_div.css("span"):
            tags.append(span.text(strip=True))
            
    thumbnail = ""
    desktop_bg_node = tree.css_first("div[style*='aspect-ratio: 21'] img")
    if desktop_bg_node:
        thumbnail = desktop_bg_node.attributes.get("src", "")
        
    if not thumbnail:
        mobile_bg_node = tree.css_first(".hidden-md.hidden-lg img[src*='files/']")
        if mobile_bg_node:
            thumbnail = mobile_bg_node.attributes.get("src", "")
            
    if not thumbnail:
        for img in tree.css("img"):
            src = img.attributes.get("src", "")
            if re.search(r'\d+h?\.(?:jpg|png|webp|jpeg)', src) and "user_default" not in src and "playlist" not in src:
                thumbnail = src
                break

    video_id = ""
    if thumbnail:
        match = re.search(r'(\d+)[hl]?\.(?:jpg|png|webp|jpeg)', thumbnail)
        if match:
            video_id = match.group(1)
            
    if not video_id:
        for script in tree.css("script"):
            script_text = script.text()
            if script_text:
                match = re.search(r"watch\?v=(\d+)", script_text)
                if match:
                    video_id = match.group(1)
                    break
                    
    watch_url = f"https://hanime1.me/watch?v={video_id}" if video_id else ""
    
    if not title and not watch_url:
        return None
        
    return {
        "title": title,
        "creator": creator,
        "views": views,
        "date": date,
        "tags": tags,
        "thumbnail": thumbnail,
        "watchUrl": watch_url,
        "videoId": video_id
    }


def parse_home_page(html: str) -> dict:
    tree = HTMLParser(html or "")
    sections = []
    for a_title in tree.css("a.horizontal-row-title"):
        h3 = a_title.css_first("h3")
        if not h3:
            continue
        title_text = h3.text(strip=True)
        title_text = title_text.replace("查看更多", "").replace("arrow_forward_ios", "").replace("chevron_right", "").strip()

        # Extract the section link from the anchor href
        raw_href = a_title.attributes.get("href", "") or ""
        section_link = urljoin(BASE_URL, raw_href) if raw_href else ""
        
        # Find next sibling that contains .home-rows-videos-wrapper
        videos_wrapper = None
        curr = a_title.next
        while curr:
            if curr.tag == "div":
                wrapper = curr.css_first(".home-rows-videos-wrapper")
                if wrapper:
                    videos_wrapper = wrapper
                    break
                if curr.attributes.get("class") and "home-rows-videos-wrapper" in curr.attributes["class"]:
                    videos_wrapper = curr
                    break
            # Stop if we hit another section title to avoid scanning too far
            if curr.tag == "a" and curr.attributes.get("class") and "horizontal-row-title" in curr.attributes["class"]:
                break
            curr = curr.next
            
        nodes = []
        if videos_wrapper:
            nodes = videos_wrapper.css("a[href*='watch?v=']")
        else:
            # Fallback to parent just in case
            parent = a_title.parent
            if parent:
                nodes = parent.css("a[href*='watch?v=']")
            
        cards = extract_cards(nodes, BASE_URL)
        if cards:
            sections.append({
                "sectionTitle": title_text,
                "sectionLink": section_link,
                "videos": cards
            })
            
    hero = parse_home_hero(tree)
    return {
        "sections": sections,
        "hero": hero
    }


def looks_like_blocked_page(html: str) -> bool:
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


def parse_total_pages(html: str, default_page: int) -> int:
    tree = HTMLParser(html or "")
    max_page = max(default_page, 1)
    for node in tree.css(".pagination a, ul.pagination li a"):
        text = node.text(strip=True)
        if text.isdigit():
            max_page = max(max_page, int(text))
            continue
        href = node.attributes.get("href", "")
        page = parse_qs(urlparse(href).query).get("page", [""])[0]
        if page.isdigit():
            max_page = max(max_page, int(page))
    return max_page


def build_file_name(title: str | None, download_url: str | None) -> str:
    safe_title = re.sub(r'[\\/:*?"<>|]', "_", (title or "video").strip()) or "video"
    lower_url = (download_url or "").lower()
    extension = ".ts" if ".m3u8" in lower_url else ".mp4"
    path = urlparse(lower_url).path
    suffix = ""
    if "." in path.rsplit("/", 1)[-1]:
        suffix = "." + path.rsplit(".", 1)[-1]
    if suffix and len(suffix) <= 5 and suffix != ".m3u8":
        extension = suffix
    return f"{safe_title}{extension}"


def extract_first_stream(html: str) -> str | None:
    if not html:
        return None
    tree = HTMLParser(html)
    for row in tree.css("table.download-table tr"):
        link = row.css_first("a[data-url]")
        if link:
            candidate = clean_url(link.attributes.get("data-url", ""))
            if candidate and "juicyads" not in candidate.lower():
                return candidate
    for link in tree.css("a[data-url]"):
        candidate = clean_url(link.attributes.get("data-url", ""))
        if candidate and "juicyads" not in candidate.lower():
            return candidate
    for source in tree.css("source[src]"):
        candidate = source.attributes.get("src", "")
        if ".m3u8" in candidate or ".mp4" in candidate:
            return clean_url(candidate)
    for pattern in (r"https?://[^\s'\"<>]+\.mp4[^\s'\"<>]*", r"https?://[^\s'\"<>]+\.m3u8[^\s'\"<>]*"):
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match and "juicyads" not in match.group(0).lower():
            return clean_url(match.group(0))
    return None


def extract_title(tree: HTMLParser) -> str:
    for selector in (
        ".video-details-wrapper h1.title",
        ".video-details-wrapper h3.title",
        ".video-description h1",
        ".video-description .title",
        ".video-info h1.title",
        "h1.title",
        "meta[property='og:title']",
        "meta[name='title']",
    ):
        node = tree.css_first(selector)
        if not node:
            continue
        content = node.attributes.get("content") if node.tag == "meta" else node.text(strip=True)
        if content:
            return content
    title = tree.css_first("title")
    return title.text(strip=True) if title else ""


def extract_thumbnail(tree: HTMLParser) -> str:
    for selector, attr in (
        ("meta[itemprop='thumbnailUrl']", "content"),
        ("meta[property='og:image']", "content"),
        ("video#player", "poster"),
    ):
        node = tree.css_first(selector)
        if node and node.attributes.get(attr):
            return node.attributes[attr]
    return ""


def extract_related_videos(tree: HTMLParser, page_url: str) -> list[dict[str, str]]:
    direct = extract_cards(tree.css("#related-tabcontent a[href*='watch?v=']"), page_url)
    if direct:
        return direct
    for section in tree.css("section, .home-rows-videos-wrapper, .home-rows-videos, .video-section, .content-section, .container"):
        heading = section.css_first("h1, h2, h3, h4, .section-title, .home-rows-title")
        text = heading.text(strip=True) if heading else ""
        compact = re.sub(r"\s+", "", text)
        if any(word in compact for word in ("相关", "相關", "推荐", "推薦")) and not any(word in compact for word in ("评论", "評論")):
            cards = extract_cards(section.css("a[href*='watch?v=']"), page_url)
            if cards:
                return cards
    return extract_cards(tree.css(".home-rows-videos-wrapper a[href*='watch?v='], .home-rows-videos a[href*='watch?v=']"), page_url)


def extract_cards(nodes: list[Node], current_url: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for node in nodes:
        href = node.attributes.get("href", "")
        url = absolutize_watch_url(href, current_url)
        if not url or url in seen:
            continue
        title = extract_card_title(node)
        image = best_image(node)
        if not title or not image:
            continue
            
        # Parse extra fields
        duration = ""
        duration_node = node.css_first(".duration")
        if duration_node:
            duration = duration_node.text(strip=True)
            
        likes = ""
        views = ""
        stats_items = node.css(".stats-container .stat-item, .stat-item")
        for item in stats_items:
            text = item.text(strip=True)
            # Remove icon text if present
            text = text.replace("thumb_up", "").strip()
            if "%" in text:
                likes = text
            elif any(u in text for u in ["次", "views", "觀看"]):
                views = text
            elif not likes:
                likes = text
            else:
                views = text
                
        creator = ""
        parent = node.parent
        if parent:
            subtitle_node = parent.css_first(".subtitle")
            if not subtitle_node and parent.parent:
                subtitle_node = parent.parent.css_first(".subtitle")
            if subtitle_node:
                creator = subtitle_node.text(strip=True)
                # Normalize spaces
                creator = re.sub(r"\s+", " ", creator).strip()
            
        items.append({
            "url": url, 
            "thumbnail": image, 
            "title": normalize_title(title),
            "duration": duration,
            "likes": likes,
            "views": views,
            "creator": creator
        })
        seen.add(url)
    return items


def extract_card_title(node: Node) -> str:
    for selector in (".home-rows-videos-title", ".card-mobile-title", ".video-title", ".search-result-title", ".title", "[title]"):
        title_node = node.css_first(selector)
        if title_node:
            value = title_node.attributes.get("title") or title_node.text(strip=True)
            if value:
                return value
    curr = node.parent
    for _ in range(3):
        if not curr:
            break
        for selector in (".home-rows-videos-title", ".card-mobile-title", ".video-title", ".search-result-title", ".title", "[title]"):
            title_node = curr.css_first(selector)
            if title_node:
                value = title_node.attributes.get("title") or title_node.text(strip=True)
                if value:
                    return value
        curr = curr.parent
    return node.attributes.get("title", "")


def best_image(node: Node) -> str:
    for image in node.css("img[data-src], img[src]"):
        value = image.attributes.get("data-src") or image.attributes.get("src") or ""
        if value and "card_doujin_background" not in value.lower():
            return value
    curr = node.parent
    for _ in range(3):
        if not curr:
            break
        for image in curr.css("img[data-src], img[src]"):
            value = image.attributes.get("data-src") or image.attributes.get("src") or ""
            if value and "card_doujin_background" not in value.lower():
                return value
        curr = curr.parent
    return ""


def normalize_title(value: str) -> str:
    value = unescape(value or "").replace(" - Hanime1.me", "")
    return re.sub(r"\s+", " ", value).strip()


def clean_url(value: str) -> str:
    return unescape(value or "").replace("&amp;", "&").strip()


def extract_video_id(url: str) -> str:
    parsed = urlparse(url or "")
    return parse_qs(parsed.query).get("v", [""])[0]


def absolutize_watch_url(href: str, current_url: str) -> str | None:
    if not href or "watch?v=" not in href:
        return None
    return urljoin(current_url if current_url.startswith("http") else BASE_URL, href)


def parse_playlist_grid(html: str) -> list[dict[str, str]]:
    tree = HTMLParser(html or "")
    nodes = tree.css("a[href*='playlist?list=']")
    items = []
    seen = set()
    for node in nodes:
        href = node.attributes.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)
        
        # Absolute URL
        url = urljoin(BASE_URL, href)
        
        # Title
        title_node = node.css_first(".title")
        title = title_node.text(strip=True) if title_node else ""
        if not title:
            title = node.attributes.get("title", "")
            
        # Thumbnail
        img_node = node.css_first("img")
        thumbnail = ""
        if img_node:
            thumbnail = img_node.attributes.get("src") or img_node.attributes.get("data-src") or ""
            
        # Video count / stat
        stat_node = node.css_first(".stats-container .stat-item, .stat-item")
        video_count = stat_node.text(strip=True) if stat_node else ""
        
        items.append({
            "url": url,
            "thumbnail": thumbnail,
            "title": title,
            "videoCount": video_count,
            "isPlaylist": True
        })
    return items
