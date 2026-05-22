from pathlib import Path


APP_JS = Path(__file__).resolve().parents[2] / "src" / "main" / "resources" / "static" / "app.js"
INDEX_HTML = Path(__file__).resolve().parents[2] / "src" / "main" / "resources" / "static" / "index.html"


def test_player_uses_direct_stream_with_proxy_fallback():
    source = APP_JS.read_text(encoding="utf-8")

    assert "currentVideoUrl = directMediaUrl(currentRawVideoUrl)" in source
    assert "currentProxiedVideoUrl = proxyVideoUrl(currentRawVideoUrl)" in source
    assert "const fallbackToProxyVideo = () => {" in source
    assert "function preloadCurrentVideo()" in source
    assert "preloadCurrentVideo();" in source
    assert "playerWrapper.classList.add(\"preloading\")" in source


def test_player_does_not_poison_direct_stream_before_fallback_is_armed():
    source = APP_JS.read_text(encoding="utf-8")

    assert "currentVideoUrl === currentRawVideoUrl" in source
    assert "videoPlayer.error" in source
    assert "playPromise.catch(fallbackToProxyVideo)" in source


def test_cards_use_cached_lazy_image_proxy():
    source = APP_JS.read_text(encoding="utf-8")

    assert "function imageUrl(url)" in source
    assert "loading=\"lazy\"" in source


def test_frontend_connects_comments_replies_and_history_cover_proxy():
    source = APP_JS.read_text(encoding="utf-8")

    assert "function loadComments(videoId)" in source
    assert 'fetch(`/api/comments?videoId=${encodeURIComponent(videoId)}`)' in source
    assert 'fetch(`/api/replies?commentId=${encodeURIComponent(commentId)}`)' in source
    assert "function historyCoverUrl(task)" in source
    assert "/api/proxy/history-cover" in source


def test_static_asset_version_bumped_for_comment_ui():
    source = INDEX_HTML.read_text(encoding="utf-8")

    assert 'href="style.css?v=3.3"' in source
    assert 'src="app.js?v=3.3"' in source


def test_related_and_comments_share_tabbed_panel():
    html = INDEX_HTML.read_text(encoding="utf-8")
    source = APP_JS.read_text(encoding="utf-8")

    assert 'id="mediaDetailTabs"' in html
    assert 'data-detail-tab="related"' in html
    assert 'data-detail-tab="comments"' in html
    assert 'id="detailPanelRelated"' in html
    assert 'id="detailPanelComments"' in html
    assert "function setDetailTab(tabName)" in source
    assert 'querySelectorAll("[data-detail-tab]")' in source
    assert "commentsSection" not in source


def test_frontend_has_lru_page_cache_and_clear_control():
    html = INDEX_HTML.read_text(encoding="utf-8")
    source = APP_JS.read_text(encoding="utf-8")

    assert "let pageCacheLimit = 20" in source
    assert "const PAGE_CACHE_STORAGE_KEY" in source
    assert "function setPageCacheEntry(key, data)" in source
    assert "while (pageCache.size > pageCacheLimit)" in source
    assert "function applyPageCacheLimit(value)" in source
    assert "getParserCacheKey(url)" in source
    assert "function restoreCachedBrowsePage(key)" in source
    assert "function restoreCachedParserPage(url)" in source
    assert "function clearPageCache()" in source
    assert 'id="pageCacheLimit"' in html
    assert 'id="clearPageCacheBtn"' in html
    assert 'id="pageCacheStatus"' in html
    assert "clearPageCacheBtn.addEventListener" in source


def test_static_asset_version_bumped_for_page_cache_ui():
    source = INDEX_HTML.read_text(encoding="utf-8")

    assert 'href="style.css?v=3.3"' in source
    assert 'src="app.js?v=3.3"' in source


def test_replies_render_avatar_images():
    source = APP_JS.read_text(encoding="utf-8")

    assert "function renderCommentAvatar" in source
    assert "comment-reply-avatar" in source
    assert "reply.avatarUrl" in source
