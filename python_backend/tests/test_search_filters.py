from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from python_backend.app.main import create_app
from python_backend.app import parser as parser_module
from python_backend.app.scraper import HanimeScraper


parse_search_options = getattr(parser_module, "parse_search_options", lambda _html: {})


SEARCH_OPTIONS_HTML = """
<div id="genre-modal">
  <div class="genre-option" data-value="全部">全部</div>
  <div class="genre-option" data-value="裏番">里番</div>
  <div class="genre-option" data-value="3DCG">3DCG</div>
</div>
<div id="sort-modal">
  <div class="hentai-sort-options-wrapper" data-value="本週排行">本周排行</div>
  <div class="hentai-sort-options-wrapper" data-value="讚好比例">赞好比例</div>
</div>
<div id="date-modal">
  <div class="hentai-date-options-wrapper" data-value="">全部</div>
  <div class="hentai-date-options-wrapper" data-value="過去 1 週">过去 1 周</div>
</div>
<div id="duration-modal">
  <div class="hentai-duration-options-wrapper" data-value="60 分鐘 +">60 分钟 +</div>
</div>
<div id="tags">
  <label><input name="tags[]" value="中文字幕"></label>
  <label><input name="tags[]" value="無碼"></label>
</div>
"""


def test_search_options_use_upstream_submit_values_and_include_tags():
    options = parse_search_options(SEARCH_OPTIONS_HTML)

    assert options == {
        "types": ["裏番", "3DCG"],
        "genres": ["裏番", "3DCG"],
        "sorts": ["本週排行", "讚好比例"],
        "dates": ["過去 1 週"],
        "durations": ["60 分鐘 +"],
        "tagGroups": [{"name": "內容標籤", "tags": ["中文字幕", "無碼"]}],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("incoming", "expected"),
    [
        ({"type": "裏番"}, {"genre": ["裏番"]}),
        ({"sort": "本周排行"}, {"sort": ["本週排行"]}),
        ({"sort": "點讚比例"}, {"sort": ["讚好比例"]}),
        ({"date": "過去 1 周"}, {"date": ["過去 1 週"]}),
    ],
)
async def test_search_translates_ui_filters_to_upstream_contract(tmp_path, incoming, expected):
    scraper = HanimeScraper(home=tmp_path)
    requested_url = ""

    async def capture_fetch(url: str, referer: str) -> str:
        nonlocal requested_url
        requested_url = url
        return "<html></html>"

    scraper.fetch_html = capture_fetch
    try:
        await scraper.search(page=1, **incoming)
    finally:
        await scraper.close()

    query = parse_qs(urlparse(requested_url).query)
    assert query | expected == query
    assert query.get("type") is None


class SearchOptionsScraper:
    async def search_options(self) -> dict:
        return parse_search_options(SEARCH_OPTIONS_HTML)


@pytest.mark.asyncio
async def test_search_options_api_returns_current_upstream_filter_values(tmp_path):
    app = create_app(tmp_path, scraper=SearchOptionsScraper(), account_client=object())
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/search/options")

    assert response.status_code == 200
    assert response.json()["sorts"] == ["本週排行", "讚好比例"]
    assert response.json()["tagGroups"] == [{"name": "內容標籤", "tags": ["中文字幕", "無碼"]}]
