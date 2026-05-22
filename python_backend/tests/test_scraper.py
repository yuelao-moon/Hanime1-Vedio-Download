import asyncio

import pytest
import httpx

from app.scraper import HanimeScraper, parse_comments
from app.settings import AppSettings


class FakePage:
    def __init__(self, content_str=""):
        self.content_str = content_str
        self.closed_calls = []

    async def goto(self, *args, **kwargs):
        return None

    async def content(self):
        return self.content_str

    async def close(self):
        self.closed_calls.append(True)

    async def evaluate(self, script, *args):
        if "navigator.userAgent" in script:
            return "fake-user-agent"
        return None


class FakeContext:
    def __init__(self, pages=None):
        self.pages = pages or []
        self.closed_calls = []

    async def new_page(self):
        page = FakePage()
        self.pages.append(page)
        return page

    async def close(self):
        self.closed_calls.append(True)

    async def cookies(self):
        return [{"name": "cf_clearance", "value": "test", "domain": "hanime1.me", "path": "/"}]


@pytest.mark.asyncio
async def test_scraper_uses_selected_browser_channel(monkeypatch, tmp_path):
    launched = []

    class FakeChromium:
        async def launch_persistent_context(self, _path, **kwargs):
            launched.append(kwargs["channel"])
            return FakeContext([FakePage()])

    class FakePlaywright:
        chromium = FakeChromium()

        async def stop(self):
            return None

    async def fake_start():
        return FakePlaywright()

    monkeypatch.setattr("app.scraper.start_playwright", fake_start)
    scraper = HanimeScraper(home=tmp_path, settings_provider=lambda: AppSettings(browserChannel="chrome"))

    await scraper.ensure_browser()

    assert launched[0] == "chrome"


@pytest.mark.asyncio
async def test_scraper_keeps_browser_open_after_successful_verification(monkeypatch, tmp_path):
    page = FakePage("<html><a href='/watch?v=ok'>ok</a></html>")
    context = FakeContext([page])

    class FakeChromium:
        async def launch_persistent_context(self, _path, **kwargs):
            return context

    class FakePlaywright:
        chromium = FakeChromium()

        async def stop(self):
            return None

    async def fake_start():
        return FakePlaywright()

    monkeypatch.setattr("app.scraper.start_playwright", fake_start)
    scraper = HanimeScraper(home=tmp_path, settings_provider=lambda: AppSettings(browserChannel="chrome"))

    html = await scraper.fetch_with_playwright("https://hanime1.me/")

    assert "watch?v=ok" in html
    assert context.closed_calls == []
    # With the new behavior, we reuse the page and do not close it
    assert page.closed_calls == []


@pytest.mark.asyncio
async def test_scraper_keeps_browser_open_when_verification_is_not_finished(monkeypatch, tmp_path):
    page = FakePage("<html><title>Just a moment...</title><body>Verify you are human</body></html>")
    context = FakeContext([page])

    class FakeChromium:
        async def launch_persistent_context(self, _path, **kwargs):
            return context

    class FakePlaywright:
        chromium = FakeChromium()

        async def stop(self):
            return None

    async def fake_start():
        return FakePlaywright()

    monkeypatch.setattr("app.scraper.start_playwright", fake_start)
    times = iter([0, 31])
    monkeypatch.setattr("app.scraper.time.monotonic", lambda: next(times, 31))

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr("app.scraper.asyncio.sleep", no_sleep)
    scraper = HanimeScraper(
        home=tmp_path,
        settings_provider=lambda: AppSettings(
            browserChannel="chrome",
            browserVerificationTimeoutSeconds=30,
        ),
    )

    html = await scraper.fetch_with_playwright("https://hanime1.me/")

    assert "Verify you are human" in html
    assert context.closed_calls == []
    assert page.closed_calls == []


@pytest.mark.asyncio
async def test_scraper_keeps_browser_open_when_page_has_no_hanime_content(monkeypatch, tmp_path):
    page = FakePage("<html><body><main>Please wait</main></body></html>")
    context = FakeContext([page])

    class FakeChromium:
        async def launch_persistent_context(self, _path, **kwargs):
            return context

    class FakePlaywright:
        chromium = FakeChromium()

        async def stop(self):
            return None

    async def fake_start():
        return FakePlaywright()

    monkeypatch.setattr("app.scraper.start_playwright", fake_start)
    scraper = HanimeScraper(home=tmp_path, settings_provider=lambda: AppSettings(browserChannel="chrome"))

    await scraper.fetch_with_playwright("https://hanime1.me/search")

    assert context.closed_calls == []
    assert page.closed_calls == []


@pytest.mark.asyncio
async def test_scraper_falls_back_to_chromium_when_selected_channel_fails(monkeypatch, tmp_path):
    launched = []

    class FakeChromium:
        async def launch_persistent_context(self, _path, **kwargs):
            launched.append(kwargs.get("channel", "chromium"))
            if kwargs.get("channel") in {"msedge", "chrome"}:
                raise RuntimeError("missing browser")
            return FakeContext([FakePage()])

    class FakePlaywright:
        chromium = FakeChromium()

        async def stop(self):
            return None

    async def fake_start():
        return FakePlaywright()

    monkeypatch.setattr("app.scraper.start_playwright", fake_start)
    monkeypatch.setattr("app.scraper.available_browser_channels", lambda: ["chromium"])
    scraper = HanimeScraper(home=tmp_path, settings_provider=lambda: AppSettings(browserChannel="msedge"))

    await scraper.ensure_browser()

    assert launched == ["msedge", "chromium"]


@pytest.mark.asyncio
async def test_fetch_html_reuses_short_lived_cache(tmp_path):
    calls = 0

    async def handler(_request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, text="<html><a href='/watch?v=ok'>ok</a></html>")

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://hanime1.me",
    )
    scraper = HanimeScraper(client=client, home=tmp_path)

    first = await scraper.fetch_html("https://hanime1.me/", "https://hanime1.me/")
    second = await scraper.fetch_html("https://hanime1.me/", "https://hanime1.me/")

    assert first == second
    assert calls == 1
    await scraper.close()


@pytest.mark.asyncio
async def test_home_browse_does_not_wait_for_slow_watching_section(monkeypatch, tmp_path):
    scraper = HanimeScraper(home=tmp_path)

    async def fake_fetch_html(url, _referer):
        if "sort=" in url:
            await asyncio.sleep(10)
            return "<html><a href='/watch?v=watching'><img src='w.jpg'><span class='title'>Watching</span></a></html>"
        return """
        <html>
          <a class="horizontal-row-title" href="/search?genre=x"><h3>最新</h3></a>
          <div class="home-rows-videos-wrapper">
            <a href="/watch?v=home"><img src="h.jpg"><span class="home-rows-videos-title">Home</span></a>
          </div>
        </html>
        """

    monkeypatch.setattr(scraper, "fetch_html", fake_fetch_html)

    result = await asyncio.wait_for(scraper.browse("首页", 1), timeout=0.5)

    assert result["isHome"] is True
    assert [section["sectionTitle"] for section in result["sections"]] == ["最新"]
    await scraper.close()


def test_parse_comments_extracts_avatar_likes_and_reply_count():
    html = """
    <div class="comment-avatar-wrap">
      <img class="img-circle" src="https://i.example.test/avatar.jpg">
    </div>
    <div class="report-btn-wrapper">
      <div class="comment-index-text"><a>Niko <span>3週前</span></a></div>
      <div class="comment-index-text">哎呦我，我看这里男主才是硬脚蟹啊</div>
      <input name="comment-likes-sum" value="514">
      <input name="comment-likes-count" value="536">
      <button class="comment-reply-btn" data-comment-id="355202">回复</button>
      <div class="load-replies-btn no-select" data-commentid="355202">查看 35 則回覆</div>
      <span class="report-btn" data-reportable-type="comment" data-reportable-id="355202"></span>
    </div>
    """

    comments = parse_comments(html)

    assert comments == [{
        "commentId": "355202",
        "userName": "Niko",
        "avatarUrl": "https://i.example.test/avatar.jpg",
        "content": "哎呦我，我看这里男主才是硬脚蟹啊",
        "timeText": "3週前",
        "likeCount": 514,
        "likeTotal": 536,
        "hasReplies": True,
        "replyCount": 35,
    }]


def test_parse_comments_finds_actions_after_comment_wrapper():
    html = """
    <div><img class="img-circle" src="https://i.example.test/avatar.jpg"></div>
    <div class="report-btn-wrapper">
      <div class="comment-index-text"><a>Niko <span>3週前</span></a></div>
      <div class="comment-index-text">comment text</div>
      <span class="report-btn" data-reportable-type="comment" data-reportable-id="368756"></span>
    </div>
    <div class="comment-actions-row">
      <input name="comment-likes-sum" value="514">
      <input name="comment-likes-count" value="536">
      <div class="load-replies-btn no-select" data-commentid="368756">查看 35 則回覆</div>
    </div>
    """

    comments = parse_comments(html)

    assert comments[0]["likeCount"] == 514
    assert comments[0]["likeTotal"] == 536
    assert comments[0]["hasReplies"] is True
    assert comments[0]["replyCount"] == 35


def test_parse_comments_finds_avatar_from_parent_previous_sibling():
    html = """
    <div class="reply-avatar"><img class="img-circle" src="https://i.example.test/reply-avatar.jpg"></div>
    <div class="reply-content">
      <div class="report-btn-wrapper">
        <div class="comment-index-text"><a>Reply User <span>3週前</span></a></div>
        <div class="comment-index-text">reply text</div>
        <span class="report-btn" data-reportable-type="comment" data-reportable-id="195967"></span>
      </div>
    </div>
    """

    comments = parse_comments(html)

    assert comments[0]["avatarUrl"] == "https://i.example.test/reply-avatar.jpg"
