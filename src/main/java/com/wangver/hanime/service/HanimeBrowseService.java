package com.wangver.hanime.service;

import com.microsoft.playwright.*;
import com.microsoft.playwright.options.WaitUntilState;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.*;

@Service
public class HanimeBrowseService {

    @Autowired
    private PlaywrightBrowserService browserService;

    private static final Map<String, String> CATEGORY_GENRE_MAP = createCategoryGenreMap();
    private volatile Map<String, Object> cachedSearchOptions;

    public Map<String, Object> fetchCategory(String category, int pageNum) throws Exception {
        return browserService.runSerialized(() -> {
            String url = buildCategoryUrl(category, pageNum);
            System.out.println("Browse: " + category + " Page: " + pageNum + " -> URL: " + url);

            return fetchResultPage(url, pageNum, false);
        });
    }

    public Map<String, Object> fetchSearch(
            String query,
            String type,
            String genre,
            List<String> tags,
            String sort,
            String date,
            String duration,
            int pageNum) throws Exception {
        return browserService.runSerialized(() -> {
            String url = buildSearchUrl(query, type, genre, tags, sort, date, duration, pageNum);
            System.out.println("Search Page: " + pageNum + " -> URL: " + url);
            return fetchResultPage(url, pageNum, true);
        });
    }

    public Map<String, Object> fetchSearchOptions() {
        Map<String, Object> cached = cachedSearchOptions;
        if (cached != null) {
            return cached;
        }

        if (browserService == null) {
            cachedSearchOptions = defaultSearchOptions();
            return cachedSearchOptions;
        }

        try {
            cachedSearchOptions = browserService.runSerialized(() -> {
                Page page = browserService.createPage();
                try {
                    page.navigate("https://hanime1.me/search",
                            new Page.NavigateOptions().setWaitUntil(WaitUntilState.DOMCONTENTLOADED).setTimeout(60000));
                    page.waitForLoadState(com.microsoft.playwright.options.LoadState.NETWORKIDLE);
                    Map<String, Object> parsed = parseSearchOptions(page.content());
                    return hasUsefulSearchOptions(parsed) ? parsed : defaultSearchOptions();
                } finally {
                    closePageQuietly(page);
                }
            });
        } catch (Exception exception) {
            System.out.println("Search options fetch failed, using defaults: " + exception.getMessage());
            cachedSearchOptions = defaultSearchOptions();
        }
        return cachedSearchOptions;
    }

    private Map<String, Object> fetchResultPage(String url, int pageNum, boolean allowEmptyResults) {
        Page page = browserService.createPage();
        try {
            page.navigate(url, new Page.NavigateOptions().setWaitUntil(WaitUntilState.DOMCONTENTLOADED).setTimeout(60000));
            try {
                page.waitForSelector("a[href*='watch?v=']",
                        new Page.WaitForSelectorOptions().setState(com.microsoft.playwright.options.WaitForSelectorState.ATTACHED).setTimeout(20000));
            } catch (Exception exception) {
                if (!allowEmptyResults) {
                    throw exception;
                }
                System.out.println("Search returned no visible video cards: " + exception.getMessage());
            }
            page.waitForLoadState(com.microsoft.playwright.options.LoadState.NETWORKIDLE);

            String html = page.content();
            return buildCategoryResult(html, pageNum);
        } finally {
            closePageQuietly(page);
        }
    }

    private Map<String, Object> buildCategoryResult(String html, int pageNum) {
        Map<String, Object> result = new HashMap<>();
        result.put("videos", parseVideoGrid(html));
        result.put("currentPage", pageNum);
        result.put("totalPages", parseTotalPages(html, pageNum));
        return result;
    }

    private String buildCategoryUrl(String category, int pageNum) {
        String genre = CATEGORY_GENRE_MAP.getOrDefault(category, category);
        String encodedCat = URLEncoder.encode(genre, StandardCharsets.UTF_8);
        return "https://hanime1.me/search?genre=" + encodedCat + "&page=" + pageNum;
    }

    private String buildSearchUrl(
            String query,
            String type,
            String genre,
            List<String> tags,
            String sort,
            String date,
            String duration,
            int pageNum) {
        List<String> params = new ArrayList<>();
        params.add(param("query", query));
        params.add(param("type", type));
        params.add(param("genre", genre));
        if (tags != null) {
            tags.stream()
                    .filter(Objects::nonNull)
                    .map(String::trim)
                    .filter(value -> !value.isEmpty())
                    .forEach(tag -> params.add(param("tags[]", tag)));
        }
        params.add(param("sort", sort));
        params.add(param("date", date));
        params.add(param("duration", duration));
        params.add(param("page", String.valueOf(Math.max(pageNum, 1))));
        return "https://hanime1.me/search?" + String.join("&", params);
    }

    private String param(String name, String value) {
        String safeValue = value == null ? "" : value;
        return URLEncoder.encode(name, StandardCharsets.UTF_8) + "=" + URLEncoder.encode(safeValue, StandardCharsets.UTF_8);
    }

    private static Map<String, String> createCategoryGenreMap() {
        Map<String, String> categories = new LinkedHashMap<>();
        categories.put("裏番", "裏番");
        categories.put("泡麵番", "泡麵番");
        categories.put("Motion Anime", "Motion Anime");
        categories.put("3DCG", "3DCG");
        categories.put("2.5D", "2.5D");
        categories.put("2D動畫", "2D動畫");
        categories.put("2D动画", "2D動畫");
        categories.put("AI生成", "AI生成");
        categories.put("MMD", "MMD");
        categories.put("Cosplay", "Cosplay");
        return Collections.unmodifiableMap(categories);
    }

    private Map<String, Object> parseSearchOptions(String html) {
        Document doc = Jsoup.parse(html);
        Map<String, Object> defaults = defaultSearchOptions();
        Map<String, Object> options = new LinkedHashMap<>();
        options.put("types", withFallback(selectOptions(doc, "type"), defaults.get("types")));
        options.put("genres", withFallback(selectOptions(doc, "genre"), defaults.get("genres")));
        options.put("sorts", withFallback(selectOptions(doc, "sort"), defaults.get("sorts")));
        options.put("dates", withFallback(selectOptions(doc, "date"), defaults.get("dates")));
        options.put("durations", withFallback(selectOptions(doc, "duration"), defaults.get("durations")));
        options.put("tagGroups", withFallback(parseTagGroups(doc), defaults.get("tagGroups")));
        return options;
    }

    private List<String> selectOptions(Document doc, String name) {
        List<String> values = new ArrayList<>();
        for (Element option : doc.select("select[name='" + name + "'] option")) {
            String value = option.hasAttr("value") && !option.attr("value").isBlank()
                    ? option.attr("value")
                    : option.text();
            if (!value.isBlank() && !"全部".equals(value.trim())) {
                values.add(value.trim());
            }
        }
        return values.stream().distinct().toList();
    }

    private List<Map<String, Object>> parseTagGroups(Document doc) {
        List<Map<String, Object>> groups = new ArrayList<>();
        for (Element section : doc.select(".modal-body section, .search-tags-section, .tags-group, fieldset")) {
            String name = section.select("h1, h2, h3, h4, legend, .title").text().trim();
            List<String> tags = section.select("input[name='tags[]'], button, .tag, .badge").stream()
                    .map(element -> element.hasAttr("value") && !element.attr("value").isBlank()
                            ? element.attr("value")
                            : element.text())
                    .map(String::trim)
                    .filter(value -> !value.isBlank())
                    .distinct()
                    .toList();
            if (!name.isBlank() && !tags.isEmpty()) {
                groups.add(Map.of("name", name, "tags", tags));
            }
        }
        return groups;
    }

    @SuppressWarnings("unchecked")
    private Object withFallback(Object parsed, Object fallback) {
        if (parsed instanceof Collection<?> collection && !collection.isEmpty()) {
            return parsed;
        }
        return fallback;
    }

    @SuppressWarnings("unchecked")
    private boolean hasUsefulSearchOptions(Map<String, Object> options) {
        Object durations = options.get("durations");
        Object tagGroups = options.get("tagGroups");
        return durations instanceof List<?> durationList && !durationList.isEmpty()
                && tagGroups instanceof List<?> groupList && !groupList.isEmpty();
    }

    private Map<String, Object> defaultSearchOptions() {
        Map<String, Object> options = new LinkedHashMap<>();
        options.put("types", List.of("裏番", "泡麵番", "Motion Anime", "3DCG", "2.5D", "2D動畫", "AI生成", "MMD", "Cosplay"));
        options.put("genres", List.of("裏番", "泡麵番", "Motion Anime", "3DCG", "2.5D", "2D動畫", "AI生成", "MMD", "Cosplay"));
        options.put("sorts", List.of("最新上市", "最新上傳", "本日排行", "本周排行", "本月排行", "觀看次數", "點讚比例", "時長最長", "他們在看"));
        options.put("dates", List.of("過去 24 小時", "過去 2 天", "過去 1 周", "過去 1 個月", "過去 3 個月", "過去 1 年"));
        options.put("durations", List.of("1 分鐘 +", "5 分鐘 +", "10 分鐘 +", "20 分鐘 +", "30 分鐘 +", "60 分鐘 +", "0 - 10 分鐘", "0 - 20 分鐘"));
        options.put("tagGroups", List.of(
                tagGroup("影片屬性", "无码", "AI解码", "中文字幕", "中文配音", "同人作品", "斷面圖", "ASMR", "1080p", "60FPS"),
                tagGroup("人物關係", "近亲", "姐", "妹", "母", "女儿", "师生", "情侣", "青梅竹马", "同事"),
                tagGroup("角色設定", "JK", "处女", "御姐", "熟女", "人妻", "女教师", "男教师", "女医生", "护士", "OL", "女警", "大小姐", "偶像", "女仆", "巫女", "魔女", "修女", "風俗娘", "公主", "女忍者", "女战士", "魔法少女", "异种族", "天使", "妖精", "魔物娘", "魅魔", "吸血鬼", "女鬼", "兽娘", "福瑞", "乳牛"),
                tagGroup("外貌身材", "短发", "马尾", "双马尾", "丸子头", "巨乳", "乳环", "舌环", "贫乳", "黑皮肤", "晒痕", "眼镜娘", "兽耳", "尖耳朵", "异色瞳", "美人痣", "肌肉女", "白虎", "阴毛", "腋毛", "大屌", "着衣", "水手服", "体操服", "泳装", "比基尼", "死库水", "和服", "兔女郎", "围裙", "啦啦队", "丝袜", "吊袜带", "热裤", "迷你裙", "性感内衣", "紧身衣", "丁字裤", "高跟鞋", "睡衣", "婚纱", "旗袍", "古装", "哥德", "口罩", "刺青", "淫纹", "身体写字"),
                tagGroup("情境場所", "校园", "教室", "图书馆", "保健室", "游泳池", "爱情宾馆", "医院", "办公室", "浴室", "窗边", "公共厕所", "公众场合", "户外野战", "电车", "车震", "游艇", "露营帐篷", "电影院", "健身房", "沙滩", "温泉", "夜店", "监狱", "教堂"),
                tagGroup("故事劇情", "纯爱", "恋爱喜剧", "后宫", "十指紧扣", "开大车", "NTR", "精神控制", "药物", "痴汉", "阿嘿颜", "精神崩溃", "猎奇", "BDSM", "捆绑", "眼罩", "项圈", "调教", "异物插入", "寻欢洞", "肉便器", "性奴隶", "胃凸", "强制", "轮奸", "凌辱", "性暴力", "逆强制", "女王样", "榨精", "母女丼", "姐妹丼", "出轨", "醉酒", "摄影", "睡眠奸", "机械奸", "虫奸", "性转换", "百合", "耽美", "时间停止", "异世界", "怪兽", "哥布林", "世界末日"),
                tagGroup("性交体位", "手交", "指交", "乳交", "乳头交", "肛交", "双洞齐下", "脚交", "素股", "拳交", "3P", "群交", "口交", "跪舔", "深喉咙", "口爆", "吞精", "舔蛋蛋", "舔穴", "69", "自慰", "腋交", "舔腋下", "发交", "舔耳朵", "舔脚", "内射", "外射", "颜射", "潮吹", "怀孕", "喷奶", "放尿", "排便", "骑乘位", "背后位", "颜面骑乘", "火车便当", "一字马", "性玩具", "飞机杯", "跳蛋", "毒龙钻", "触手", "兽交", "颈手枷", "扯头发", "掐脖子", "打屁股", "肉棒打脸", "阴道外翻", "男乳首责", "接吻", "舌吻", "POV")
        ));
        return options;
    }

    private Map<String, Object> tagGroup(String name, String... tags) {
        return Map.of("name", name, "tags", List.of(tags));
    }

    private void closePageQuietly(Page page) {
        if (page == null) return;
        try {
            page.close();
        } catch (PlaywrightException ignored) {}
    }

    private int parseTotalPages(String html, int defaultPage) {
        Document doc = Jsoup.parse(html);
        Elements pageLinks = doc.select(".pagination a, ul.pagination li a");
        int maxPage = defaultPage;
        for (Element a : pageLinks) {
            try {
                int p = Integer.parseInt(a.text().trim());
                if (p > maxPage) maxPage = p;
            } catch (NumberFormatException e) {
                String href = a.attr("href");
                if (href != null && href.contains("page=")) {
                    try {
                        String pageStr = href.substring(href.indexOf("page=") + 5);
                        int ampIndex = pageStr.indexOf("&");
                        if (ampIndex > 0) pageStr = pageStr.substring(0, ampIndex);
                        int p = Integer.parseInt(pageStr);
                        if (p > maxPage) maxPage = p;
                    } catch (Exception ignored) {}
                }
            }
        }
        return Math.max(maxPage, 1);
    }

    private List<Map<String, String>> parseVideoGrid(String html) {
        List<Map<String, String>> videos = new ArrayList<>();
        Document doc = Jsoup.parse(html);

        Elements cards = doc.select("a[href*=\"watch?v=\"]");
        Set<String> seen = new HashSet<>();

        for (Element a : cards) {
            String link = a.attr("href");
            if (link.startsWith("/")) {
                link = "https://hanime1.me" + link;
            }
            if (seen.contains(link)) continue;

            Element img = a.selectFirst("img");
            Element titleDiv = a.selectFirst(".home-rows-videos-title, .video-title, .card-mobile-title, .search-result-title, .title");
            Element titleContainer = a.closest("[title]");

            if (img != null && titleDiv != null) {
                Map<String, String> item = new HashMap<>();
                String thumbUrl = img.hasAttr("data-src") ? img.attr("data-src") : img.attr("src");
                item.put("thumbnail", thumbUrl);
                item.put("url", link);
                String visibleTitle = titleDiv.text();
                String rawTitle = visibleTitle;
                if (TitleTextNormalizer.looksBroken(visibleTitle)
                        && titleContainer != null
                        && titleContainer.hasAttr("title")) {
                    rawTitle = titleContainer.attr("title");
                }
                item.put("title", TitleTextNormalizer.normalize(rawTitle));
                videos.add(item);
                seen.add(link);
            }
        }
        return videos;
    }
}
