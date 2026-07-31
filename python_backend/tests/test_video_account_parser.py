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


def test_extract_video_page_includes_comic_original_link():
    html = """
    <html>
      <body>
        <h1 id="shareBtn-title">Example Title</h1>
        <a class="video-show-action-btn video-comic-btn" href="https://hanimeone.me/comic/81505" target="_blank">
          <i class="material-icons-outlined">import_contacts</i>漫画原作
        </a>
      </body>
    </html>
    """

    result = extract_video_page("https://hanime1.me/watch?v=39123", html)

    assert result["comicOriginal"] == {
        "title": "漫画原作",
        "url": "https://hanimeone.me/comic/81505",
    }


def test_extract_video_page_reads_new_sidebar_playlist_layout():
    html = """
    <html>
      <body>
        <h1 id="shareBtn-title">關於同組的染谷同學是性感女優這件事。 4</h1>
        <meta property="og:image" content="https://img.test/current.jpg">
        <div class="right-sidebar-sticky no-scrollbar-style">
          <div class="hidden-xs hidden-sm desktop-playlist-flex">
            <div class="video-playlist-wrapper">
              <div id="playlist-scroll" class="playlist-scroll-node hover-video-playlist">
                <div class="playlist-hover-wrap clickable-row videos-scroll" data-href="https://hanime1.me/watch?v=407444">
                  <div class="playlist-video-card video-item-container no-select">
                    <div class="video-thumb-container horizontal-card">
                      <div class="thumb-container">
                        <a href="https://hanime1.me/watch?v=407444">
                          <img class="main-thumb" src="https://vdownload.hembed.com/image/thumbnail/407444l.jpg">
                          <div class="duration">06:39</div>
                          <div class="stats-container">
                            <div class="stat-item"><i class="material-icons">thumb_up</i> 99%</div>
                            <div class="stat-item">2.6万次</div>
                          </div>
                        </a>
                      </div>
                    </div>
                    <div class="video-info-container">
                      <h4 class="video-title"><a href="https://hanime1.me/watch?v=407444">關於同組的染谷同學是性感女優這件事。 4</a></h4>
                    </div>
                  </div>
                </div>
                <div class="playlist-hover-wrap clickable-row" data-href="https://hanime1.me/watch?v=407325">
                  <div class="playlist-video-card video-item-container no-select">
                    <div class="video-thumb-container horizontal-card">
                      <div class="thumb-container">
                        <a href="https://hanime1.me/watch?v=407325">
                          <img class="main-thumb" src="https://vdownload.hembed.com/image/thumbnail/407325l.jpg">
                          <div class="duration">06:41</div>
                        </a>
                      </div>
                    </div>
                    <div class="video-info-container">
                      <h4 class="video-title"><a href="https://hanime1.me/watch?v=407325">關於同組的染谷同學是性感女優這件事。 3</a></h4>
                    </div>
                  </div>
                </div>
                <div class="playlist-hover-wrap clickable-row" data-href="https://hanime1.me/watch?v=407315">
                  <div class="playlist-video-card video-item-container no-select">
                    <div class="video-thumb-container horizontal-card">
                      <div class="thumb-container">
                        <a href="https://hanime1.me/watch?v=407315">
                          <img class="main-thumb" src="https://vdownload.hembed.com/image/thumbnail/407315l.jpg">
                        </a>
                      </div>
                    </div>
                    <div class="video-info-container">
                      <h4 class="video-title"><a href="https://hanime1.me/watch?v=407315">關於同組的染谷同學是性感女優這件事。 2</a></h4>
                    </div>
                  </div>
                </div>
                <div class="playlist-hover-wrap clickable-row" data-href="https://hanime1.me/watch?v=407103">
                  <div class="playlist-video-card video-item-container no-select">
                    <div class="video-thumb-container horizontal-card">
                      <div class="thumb-container">
                        <a href="https://hanime1.me/watch?v=407103">
                          <img class="main-thumb" src="https://vdownload.hembed.com/image/thumbnail/407103l.jpg">
                        </a>
                      </div>
                    </div>
                    <div class="video-info-container">
                      <h4 class="video-title"><a href="https://hanime1.me/watch?v=407103">關於同組的染谷同學是性感女優這件事。 1</a></h4>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """

    result = extract_video_page("https://hanime1.me/watch?v=407444", html)

    assert [item["videoId"] for item in result["playlist"]] == ["407444", "407325", "407315", "407103"]
    assert result["playlist"][0]["title"] == "關於同組的染谷同學是性感女優這件事。 4"
    assert result["playlist"][0]["thumbnail"] == "https://vdownload.hembed.com/image/thumbnail/407444l.jpg"
    assert result["playlist"][0]["duration"] == "06:39"
    assert result["playlist"][0]["likes"] == "99%"
    assert result["playlist"][0]["views"] == "2.6万次"


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
