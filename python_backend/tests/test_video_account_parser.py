from __future__ import annotations

from python_backend.app.parser import extract_video_page


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
    assert result["creator"]["post"] == {
        "userId": "42",
        "artistId": "99",
        "isSubscribed": True,
    }
