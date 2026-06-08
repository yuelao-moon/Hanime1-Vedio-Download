from __future__ import annotations

from pathlib import Path


def test_frontend_restores_route_from_hash_on_initial_load():
    app_js = Path("src/main/resources/static/app.js").read_text(encoding="utf-8")

    assert "function restoreInitialRouteFromHash()" in app_js
    assert "restoreInitialRouteFromHash();" in app_js
    assert "#parse?v=" in app_js
    assert "handleStateRestore" in app_js


def test_frontend_supports_mouse_history_buttons():
    app_js = Path("src/main/resources/static/app.js").read_text(encoding="utf-8")

    assert "function handleMouseHistoryNavigation(event)" in app_js
    assert 'document.addEventListener("mouseup", handleMouseHistoryNavigation)' in app_js
    assert "event.button === 3" in app_js
    assert "event.button === 4" in app_js
    assert "history.back();" in app_js
    assert "history.forward();" in app_js


def test_index_uses_no_referrer_policy_for_direct_media():
    index_html = Path("src/main/resources/static/index.html").read_text(encoding="utf-8")

    assert '<meta name="referrer" content="no-referrer">' in index_html


def test_frontend_uses_direct_images_without_image_proxy():
    app_js = Path("src/main/resources/static/app.js").read_text(encoding="utf-8")

    assert "function imageUrl(url)" in app_js
    assert "return directImageUrl(url);" in app_js
    assert "proxyImageUrl" not in app_js
    assert "fallbackProxyImage" not in app_js
    assert "fallbackImage" not in app_js
    assert "preloadImageCache" not in app_js
    assert "/api/proxy/image" not in app_js
    assert "/api/proxy/images/preload" not in app_js
    assert "/api/proxy/history-cover" not in app_js
    assert 'referrerpolicy="no-referrer"' in app_js
    assert 'referrerPolicy = "no-referrer"' in app_js


def test_frontend_video_player_uses_direct_media_url():
    app_js = Path("src/main/resources/static/app.js").read_text(encoding="utf-8")

    assert "function directMediaUrl(url)" in app_js
    assert "currentVideoUrl = directMediaUrl(currentRawVideoUrl);" in app_js
    assert "proxyVideoUrl" not in app_js
    assert "currentProxiedVideoUrl" not in app_js
    assert "fallbackToProxyVideo" not in app_js
    assert "/api/proxy/video" not in app_js
    assert 'videoPlayer.referrerPolicy = "no-referrer"' in app_js


def test_profile_watch_later_and_likes_have_bulk_delete_controls():
    app_js = Path("src/main/resources/static/app.js").read_text(encoding="utf-8")

    assert "function renderProfileBulkToolbar" in app_js
    assert "function toggleProfileBulkMode" in app_js
    assert "function deleteSelectedProfileItems" in app_js
    assert "profile-bulk-delete" in app_js
    assert "watchLater" in app_js
    assert "likes" in app_js
