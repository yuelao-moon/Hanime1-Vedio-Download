from app.parser import extract_video_page, parse_video_grid, build_file_name, looks_like_blocked_page, parse_home_page


def test_extract_video_page_prefers_download_table_url():
    html = """
    <html>
      <head>
        <meta property="og:title" content=" Sample Title - Hanime1.me ">
        <meta property="og:image" content="https://img.test/cover.jpg">
      </head>
      <body>
        <table class="download-table">
          <tr><td><a data-url="https://cdn.test/video.mp4?token=1&amp;x=2">download</a></td></tr>
        </table>
        <div id="video-playlist-wrapper">
          <a href="/watch?v=next"><img data-src="https://img.test/next.jpg"><div class="title">Next Ep</div></a>
        </div>
        <section><h3>相關影片</h3>
          <a href="/watch?v=rel"><img src="https://img.test/rel.jpg"><div class="title">Related</div></a>
        </section>
      </body>
    </html>
    """

    parsed = extract_video_page("https://hanime1.me/watch?v=abc", html)

    assert parsed["title"] == "Sample Title"
    assert parsed["thumbnail"] == "https://img.test/cover.jpg"
    assert parsed["videoUrl"] == "https://cdn.test/video.mp4?token=1&x=2"
    assert parsed["videoId"] == "abc"
    assert parsed["playlist"][0]["url"] == "https://hanime1.me/watch?v=next"
    assert parsed["relatedVideos"][0]["title"] == "Related"


def test_parse_video_grid_deduplicates_cards():
    html = """
    <a href="/watch?v=1"><img data-src="/a.jpg"><div class="home-rows-videos-title">One</div></a>
    <a href="/watch?v=1"><img data-src="/a.jpg"><div class="home-rows-videos-title">One again</div></a>
    <a href="https://hanime1.me/watch?v=2"><img src="/b.jpg"><div class="title">Two</div></a>
    """

    videos = parse_video_grid(html)

    assert [video["title"] for video in videos] == ["One", "Two"]
    assert videos[0]["url"] == "https://hanime1.me/watch?v=1"


def test_build_file_name_sanitizes_title_and_keeps_extension():
    assert build_file_name('A:B*C?"D', "https://cdn.test/file.m3u8?token=1") == "A_B_C__D.ts"
    assert build_file_name("Movie", "https://cdn.test/file.mp4?token=1") == "Movie.mp4"


def test_detects_cloudflare_attention_page():
    html = "<html><title>Attention Required! | Cloudflare</title><body>Cloudflare Ray ID</body></html>"

    assert looks_like_blocked_page(html)


def test_detects_turnstile_human_verification_page():
    html = "<html><body><div class='cf-turnstile'></div><p>Verify you are human</p></body></html>"

    assert looks_like_blocked_page(html)


def test_extract_video_page_sibling_overlay_playlist():
    html = """
    <html>
      <body>
        <div id="video-playlist-wrapper">
          <div class="related-watch-wrap">
            <a class="overlay" href="/watch?v=434"></a>
            <div class="card-mobile-panel inner">
              <img src="https://img.test/card_doujin_background.jpg">
              <img src="https://img.test/434l.jpg" alt="Episode 2 Title">
              <div class="card-mobile-title">Episode 2 Title</div>
            </div>
          </div>
          <div class="related-watch-wrap">
            <a class="overlay" href="/watch?v=433"></a>
            <div class="card-mobile-panel inner">
              <img src="https://img.test/433l.jpg" alt="Episode 1 Title">
              <div class="card-mobile-title">Episode 1 Title</div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """

    parsed = extract_video_page("https://hanime1.me/watch?v=434", html)

    assert len(parsed["playlist"]) == 2
    assert parsed["playlist"][0]["url"] == "https://hanime1.me/watch?v=434"
    assert parsed["playlist"][0]["title"] == "Episode 2 Title"
    assert parsed["playlist"][0]["thumbnail"] == "https://img.test/434l.jpg"
    assert parsed["playlist"][1]["url"] == "https://hanime1.me/watch?v=433"
    assert parsed["playlist"][1]["title"] == "Episode 1 Title"
    assert parsed["playlist"][1]["thumbnail"] == "https://img.test/433l.jpg"


def test_parse_home_page():
    html = """
    <html>
      <body>
        <div class="home-rows-section-margin-top">
          <a class="horizontal-row-title" href="/search?sort=latest">
            <h3>最新上市查看更多</h3>
          </a>
          <div class="home-rows-videos-wrapper">
            <div class="video-item-container">
              <div class="horizontal-card">
                <a href="/watch?v=111" class="video-link">
                  <div class="thumb-container">
                    <img class="main-thumb" src="/111l.jpg">
                    <div class="duration">10:00</div>
                    <div class="stats-container">
                      <div class="stat-item">thumb_up 95%</div>
                      <div class="stat-item">10.5万次</div>
                    </div>
                  </div>
                  <div class="title">Video One</div>
                </a>
                <div class="subtitle">
                  <a href="/search?query=CreatorOne">CreatorOne • 2小时前</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """
    parsed = parse_home_page(html)
    sections = parsed["sections"]
    assert len(sections) == 1
    assert sections[0]["sectionTitle"] == "最新上市"
    assert len(sections[0]["videos"]) == 1
    v = sections[0]["videos"][0]
    assert v["url"] == "https://hanime1.me/watch?v=111"
    assert v["title"] == "Video One"
    assert v["thumbnail"] == "/111l.jpg"
    assert v["duration"] == "10:00"
    assert v["likes"] == "95%"
    assert v["views"] == "10.5万次"
    assert v["creator"] == "CreatorOne • 2小时前"


def test_parse_home_hero():
    html = """
    <html>
      <body>
        <div style="position: relative; background-color: #141414; overflow: hidden; aspect-ratio: 21 / 9;">
            <img src="https://img.test/405850h.jpg" alt="Shirogane Kei">
        </div>
        <div id="home-banner-wrapper">
            <h1>Shirogane Kei</h1>
            <h4 class="hidden-xs">Ameng • 45.9万次 • 1个月前</h4>
            <div>
                <span>3P</span>
                <span>JK</span>
            </div>
            <a class="home-banner-play-btn">播放</a>
        </div>
      </body>
    </html>
    """
    parsed = parse_home_page(html)
    hero = parsed["hero"]
    assert hero is not None
    assert hero["title"] == "Shirogane Kei"
    assert hero["creator"] == "Ameng"
    assert hero["views"] == "45.9万次"
    assert hero["date"] == "1个月前"
    assert hero["tags"] == ["3P", "JK"]
    assert hero["thumbnail"] == "https://img.test/405850h.jpg"
    assert hero["videoId"] == "405850"
    assert hero["watchUrl"] == "https://hanime1.me/watch?v=405850"



