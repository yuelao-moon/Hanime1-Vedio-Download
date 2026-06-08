from __future__ import annotations

from python_backend.app.parser import extract_video_page, parse_playlist_grid, parse_video_grid


def test_extract_video_page_includes_account_action_fields():
    html = """
    <html>
      <body>
        <input name="_token" value="csrf-123">
        <input name="like-user-id" value="42">
        <input name="like-status" value="1">
        <input name="likes-count" value="12">
        <input name="unlikes-count" value="3">
        <h1 id="shareBtn-title">Example Title</h1>
        <meta property="og:image" content="https://img.test/cover.jpg">
        <div id="playlist-save-checkbox"><input id="WL" checked></div>
        <div class="playlist-checkbox-wrapper">
          <input id="playlist-7" checked>
          <span>My List</span>
        </div>
        <div id="video-subscribe-form">
          <input name="subscribe-user-id" value="42">
          <input name="subscribe-artist-id" value="99">
          <input name="subscribe-status" value="1">
        </div>
        <a href="/user/99"><img src="https://img.test/avatar.jpg"></a>
        <span id="video-artist-name">Creator</span>
      </body>
    </html>
    """

    result = extract_video_page("https://hanime1.me/watch?v=123", html)

    assert result["csrfToken"] == "csrf-123"
    assert result["currentUserId"] == "42"
    assert result["isFav"] is True
    assert result["favTimes"] == 12
    assert result["unlikesCount"] == 3
    assert result["myList"]["isWatchLater"] is True
    assert result["myList"]["watchLaterCode"] == "WL"
    assert result["myList"]["items"] == [{"code": "playlist-7", "title": "My List", "isSelected": True}]
    assert result["creator"]["avatar"] == "https://img.test/avatar.jpg"
    assert result["creator"]["post"] == {
        "userId": "42",
        "artistId": "99",
        "isSubscribed": True,
    }


def test_extract_video_page_prefers_subscribe_artist_avatar_over_first_user_link():
    html = """
    <html>
      <body>
        <h1 id="shareBtn-title">Example Title</h1>
        <meta property="og:image" content="https://img.test/cover.jpg">
        <a href="/user/664762"><img src="https://img.test/logged-user.jpg"></a>
        <div id="video-subscribe-form">
          <input name="subscribe-user-id" value="664762">
          <input name="subscribe-artist-id" value="99">
          <input name="subscribe-status" value="">
        </div>
        <a href="/user/99"><img data-src="https://img.test/real-creator.jpg" alt="AnimationAkt"></a>
        <span id="video-artist-name">AnimationAkt</span>
      </body>
    </html>
    """

    result = extract_video_page("https://hanime1.me/watch?v=123", html)

    assert result["creator"]["id"] == "99"
    assert result["creator"]["avatar"] == "https://img.test/real-creator.jpg"


def test_extract_video_page_absolutizes_relative_cover_and_creator_avatar():
    html = """
    <html>
      <head><meta property="og:image" content="/image/thumbnail/406536h.jpg"></head>
      <body>
        <h1 id="shareBtn-title">Example Title</h1>
        <div id="video-subscribe-form">
          <input name="subscribe-user-id" value="42">
          <input name="subscribe-artist-id" value="99">
        </div>
        <a href="/user/99"><img data-src="/user/avatar/99.jpg" alt="Creator"></a>
        <span id="video-artist-name">Creator</span>
      </body>
    </html>
    """

    result = extract_video_page("https://hanime1.me/watch?v=406536", html)

    assert result["thumbnail"] == "https://hanime1.me/image/thumbnail/406536h.jpg"
    assert result["creator"]["avatar"] == "https://hanime1.me/user/avatar/99.jpg"


def test_video_and_playlist_grids_absolutize_relative_thumbnails():
    video_html = """
    <a href="/watch?v=406536">
      <img src="/image/thumbnail/406536h.jpg">
      <div class="home-rows-videos-title">Video Title</div>
    </a>
    """
    playlist_html = """
    <a href="/playlist?list=ABC">
      <img data-src="/playlist/cover.jpg">
      <div class="title">Playlist Title</div>
    </a>
    """

    assert parse_video_grid(video_html)[0]["thumbnail"] == "https://hanime1.me/image/thumbnail/406536h.jpg"
    assert parse_playlist_grid(playlist_html)[0]["thumbnail"] == "https://hanime1.me/playlist/cover.jpg"
