package com.wangver.hanime.service;

import com.microsoft.playwright.*;
import com.microsoft.playwright.options.WaitUntilState;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class HanimeParserService {

    @Autowired
    private HanimeHttpSessionService httpSessionService;

    @Autowired
    private PlaywrightBrowserService browserService;

    public Map<String, Object> parse(String url) throws Exception {
        String videoId = extractVideoId(url);

        if (httpSessionService != null) {
            try {
                String html = httpSessionService.fetchHtml(url, "https://hanime1.me/");
                String downloadHtml = fetchDownloadPageHtml(videoId);
                return buildParseResult(url, html, downloadHtml);
            } catch (HttpSessionExpiredException e) {
                System.out.println("HTTP session rejected for parse, falling back to Playwright: " + e.getMessage());
            }
        }

        if (browserService == null) {
            throw new IllegalStateException("No HTTP session or browser service available");
        }

        return parseWithPlaywright(url, videoId);
    }

    public String fetchThumbnail(String url) throws Exception {
        String html = fetchVideoPageHtml(url);
        return extractThumbnail(html);
    }

    private String fetchVideoPageHtml(String url) throws Exception {
        if (httpSessionService != null) {
            try {
                return httpSessionService.fetchHtml(url, "https://hanime1.me/");
            } catch (HttpSessionExpiredException e) {
                System.out.println("HTTP session rejected for thumbnail, falling back to Playwright: " + e.getMessage());
            }
        }

        if (browserService == null) {
            throw new IllegalStateException("No HTTP session or browser service available");
        }

        return browserService.runSerialized(() -> {
            Page page = browserService.createPage();
            try {
                page.navigate(url, new Page.NavigateOptions().setWaitUntil(WaitUntilState.DOMCONTENTLOADED).setTimeout(60000));
                page.waitForSelector("meta[itemprop=thumbnailUrl], meta[property=og:image], video#player",
                        new Page.WaitForSelectorOptions().setTimeout(20000));
                return page.content();
            } finally {
                closePageQuietly(page);
            }
        });
    }

    private Map<String, Object> parseWithPlaywright(String url, String videoId) throws Exception {
        return browserService.runSerialized(() -> {
            Page page = browserService.createPage();
            try {
                page.navigate(url, new Page.NavigateOptions().setWaitUntil(WaitUntilState.DOMCONTENTLOADED).setTimeout(60000));
                page.waitForSelector(".video-details-wrapper, #player, .title, h1.title, h3.title",
                        new Page.WaitForSelectorOptions().setTimeout(20000));

                String html = page.content();
                String downloadUrl = null;

                if (videoId != null && !videoId.isBlank()) {
                    try {
                        downloadUrl = fetchFirstDownloadUrlWithPlaywright(page, videoId);
                    } catch (Exception e) {
                        System.out.println("下载页获取失败: " + e.getMessage());
                    }
                }

                return buildParseResult(url, html, null, downloadUrl);
            } finally {
                closePageQuietly(page);
            }
        });
    }

    private String fetchFirstDownloadUrlWithPlaywright(Page page, String videoId) {
        page.navigate("https://hanime1.me/download?v=" + videoId,
                new Page.NavigateOptions().setWaitUntil(WaitUntilState.DOMCONTENTLOADED).setTimeout(60000));
        ElementHandle downloadButton = page.waitForSelector("table.download-table a[data-url], a[data-url]",
                new Page.WaitForSelectorOptions().setTimeout(10000));
        if (downloadButton == null) {
            return null;
        }
        String url = downloadButton.getAttribute("data-url");
        if (url == null || url.isBlank() || url.toLowerCase(Locale.ROOT).contains("juicyads")) {
            return null;
        }
        return url.replace("&amp;", "&");
    }

    private void closePageQuietly(Page page) {
        if (page == null) return;
        try {
            page.close();
        } catch (PlaywrightException ignored) {}
    }

    private Map<String, Object> buildParseResult(String url, String html, String downloadHtml) {
        return buildParseResult(url, html, downloadHtml, null);
    }

    private Map<String, Object> buildParseResult(String url, String html, String downloadHtml, String directDownloadUrl) {
        Map<String, Object> result = new HashMap<>();
        String videoUrl = directDownloadUrl;
        if ((videoUrl == null || videoUrl.isBlank()) && downloadHtml != null && !downloadHtml.isBlank()) {
            videoUrl = extractFirstStream(downloadHtml);
        }
        if (videoUrl == null || videoUrl.isBlank()) {
            videoUrl = extractFirstStream(html);
        }

        result.put("videoUrl", videoUrl != null ? videoUrl.replace("&amp;", "&") : "");

        Document doc = Jsoup.parse(html);
        Element titleEl = doc.selectFirst("h3.title, h1.title, .title, .video-title");
        if (titleEl != null) {
            result.put("title", TitleTextNormalizer.normalize(titleEl.text()));
        } else {
            Element ogTitle = doc.selectFirst("meta[property=og:title], meta[name=title]");
            String fallbackTitle = ogTitle != null ? ogTitle.attr("content") : doc.title();
            result.put("title", TitleTextNormalizer.normalize(fallbackTitle));
        }

        result.put("thumbnail", extractThumbnail(html));

        result.put("playlist", extractPlaylist(html, url));
        result.put("relatedVideos", extractRelatedVideos(html, url));
        return result;
    }

    private String extractThumbnail(String html) {
        Document doc = Jsoup.parse(html);
        Element thumbMeta = doc.selectFirst("meta[itemprop=thumbnailUrl]");
        if (thumbMeta != null) {
            return thumbMeta.attr("content");
        }

        Element ogImg = doc.selectFirst("meta[property=og:image]");
        if (ogImg != null) {
            return ogImg.attr("content");
        }

        Element videoEl = doc.selectFirst("video#player");
        if (videoEl != null && videoEl.hasAttr("poster")) {
            return videoEl.attr("poster");
        }

        return "";
    }

    private String extractFirstStream(String html) {
        Document doc = Jsoup.parse(html);

        String downloadUrl = extractFirstDownloadUrl(doc);
        if (downloadUrl != null) {
            return downloadUrl;
        }

        Elements sources = doc.select("source[src]");
        for (Element s : sources) {
            String src = s.attr("src");
            if (src.contains(".m3u8") || src.contains(".mp4")) return src;
        }

        List<String> mp4Links = extractLinksByRegex(html, "(https?://[^\\s'\"]+\\.mp4[^\\s'\"]*)");
        if (!mp4Links.isEmpty()) {
            return mp4Links.get(0);
        }

        List<String> m3u8Links = extractLinksByRegex(html, "(https?://[^\\s'\"]+\\.m3u8[^\\s'\"]*)");
        if (!m3u8Links.isEmpty()) {
            return m3u8Links.get(0);
        }

        return null;
    }

    private String extractFirstDownloadUrl(Document doc) {
        Elements rows = doc.select("table.download-table tr");
        for (Element row : rows) {
            Element downloadButton = row.selectFirst("a[data-url]");
            if (downloadButton == null) continue;

            String url = downloadButton.attr("data-url").replace("&amp;", "&");
            if (url.isBlank() || url.toLowerCase(Locale.ROOT).contains("juicyads")) continue;

            return url;
        }
        return null;
    }

    private String fetchDownloadPageHtml(String videoId) {
        if (videoId == null || videoId.isBlank()) return null;

        String url = "https://hanime1.me/download?v=" + videoId;
        try {
            String html = httpSessionService.fetchHtml(url, "https://hanime1.me/watch?v=" + videoId);
            if (extractFirstDownloadUrl(Jsoup.parse(html)) != null) {
                return html;
            }
        } catch (Exception e) {
            System.out.println("下载页获取失败: " + url + " -> " + e.getMessage());
        }
        return null;
    }

    private List<String> extractLinksByRegex(String html, String regexStr) {
        List<String> links = new ArrayList<>();
        Pattern pattern = Pattern.compile(regexStr, Pattern.CASE_INSENSITIVE);
        Matcher matcher = pattern.matcher(html);
        while (matcher.find()) {
            String link = matcher.group(1);
            if (!link.toLowerCase(Locale.ROOT).contains("juicyads")) {
                links.add(link);
            }
        }
        return links;
    }

    private String extractVideoId(String url) {
        try {
            return url.split("v=")[1].split("&")[0];
        } catch (Exception e) {
            return "";
        }
    }

    private List<Map<String, String>> extractPlaylist(String html, String currentUrl) {
        Document doc = Jsoup.parse(html);
        return extractVideoCards(doc.select("#video-playlist-wrapper .related-watch-wrap, #video-playlist-wrapper .multiple-link-wrapper, .related-watch-wrap.multiple-link-wrapper"), currentUrl);
    }

    private List<Map<String, String>> extractRelatedVideos(String html, String currentUrl) {
        Document doc = Jsoup.parse(html);
        List<Map<String, String>> relatedVideos = new ArrayList<>();

        Elements relatedTabCards = doc.select("#related-tabcontent > div.row a[href*='watch?v='], #related-tabcontent div.row a[href*='watch?v=']");
        relatedVideos.addAll(extractVideoCards(relatedTabCards, currentUrl));
        if (!relatedVideos.isEmpty()) {
            return relatedVideos;
        }

        Elements sectionRoots = doc.select("section, .home-rows-videos-wrapper, .home-rows-videos, .video-section, .content-section, .container");
        for (Element section : sectionRoots) {
            if (!looksLikeRelatedSection(section) || shouldExcludeSection(section)) {
                continue;
            }
            relatedVideos.addAll(extractVideoCards(section.select("a[href*='watch?v=']"), currentUrl));
            if (!relatedVideos.isEmpty()) {
                break;
            }
        }

        if (!relatedVideos.isEmpty()) {
            return relatedVideos;
        }

        Elements fallbackCards = doc.select(".home-rows-videos-wrapper a[href*='watch?v='], .home-rows-videos a[href*='watch?v=']");
        return extractVideoCards(fallbackCards, currentUrl);
    }

    private Map<String, String> buildPlaylistItem(String link, String thumbnail, String title) {
        Map<String, String> item = new HashMap<>();
        item.put("url", link);
        item.put("thumbnail", thumbnail);
        item.put("title", title);
        return item;
    }

    private String extractImageUrl(Element imgEl) {
        if (imgEl == null) {
            return "";
        }
        if (imgEl.hasAttr("data-src") && !imgEl.attr("data-src").isBlank()) {
            return imgEl.attr("data-src");
        }
        return imgEl.attr("src");
    }

    private Element selectBestPlaylistImage(Elements images) {
        Element fallback = null;
        for (Element image : images) {
            String imageUrl = extractImageUrl(image);
            if (imageUrl.isBlank()) {
                continue;
            }
            if (fallback == null) {
                fallback = image;
            }
            String normalized = imageUrl.toLowerCase(Locale.ROOT);
            if (normalized.contains("/image/thumbnail/") || normalized.contains("thumbnail")) {
                return image;
            }
            if (image.hasAttr("alt") && !image.attr("alt").isBlank()
                    && !normalized.contains("card_doujin_background")
                    && !normalized.contains("/image/icon/")) {
                return image;
            }
        }

        for (Element image : images) {
            String imageUrl = extractImageUrl(image);
            if (imageUrl.isBlank()) {
                continue;
            }
            String normalized = imageUrl.toLowerCase(Locale.ROOT);
            if (!normalized.contains("card_doujin_background") && !normalized.contains("/image/icon/")) {
                return image;
            }
        }
        return fallback;
    }

    private List<Map<String, String>> extractVideoCards(Elements cardElements, String currentUrl) {
        List<Map<String, String>> items = new ArrayList<>();
        Set<String> seenUrls = new HashSet<>();

        for (Element card : cardElements) {
            Element linkEl = "a".equals(card.tagName()) ? card : card.selectFirst("a[href*='watch?v=']");
            if (linkEl == null) {
                continue;
            }

            String link = absolutizeWatchUrl(linkEl.attr("href"), currentUrl);
            if (link == null || seenUrls.contains(link)) {
                continue;
            }

            Element scope = "a".equals(card.tagName()) ? card : linkEl;
            Element titleEl = card.selectFirst(".home-rows-videos-title, .card-mobile-title, .video-title, .title, [title]");
            if (titleEl == null) {
                titleEl = scope.selectFirst(".home-rows-videos-title, .card-mobile-title, .video-title, .title, [title]");
            }
            Element imgEl = selectBestPlaylistImage(card.select("img[data-src], img[src]"));
            if (imgEl == null) {
                imgEl = selectBestPlaylistImage(scope.select("img[data-src], img[src]"));
            }

            String title = extractCardTitle(titleEl, scope);
            String thumbnail = extractImageUrl(imgEl);
            if (title.isBlank() || thumbnail.isBlank()) {
                continue;
            }

            items.add(buildPlaylistItem(link, thumbnail, title));
            seenUrls.add(link);
        }

        return items;
    }

    private String extractCardTitle(Element titleEl, Element fallbackScope) {
        if (titleEl != null) {
            if (titleEl.hasAttr("title") && !titleEl.attr("title").isBlank()) {
                return TitleTextNormalizer.normalize(titleEl.attr("title"));
            }
            String text = titleEl.text();
            if (!text.isBlank()) {
                return TitleTextNormalizer.normalize(text);
            }
        }

        if (fallbackScope != null && fallbackScope.hasAttr("title") && !fallbackScope.attr("title").isBlank()) {
            return TitleTextNormalizer.normalize(fallbackScope.attr("title"));
        }
        return "";
    }

    private boolean looksLikeRelatedSection(Element section) {
        String heading = section.select("h1, h2, h3, h4, .section-title, .home-rows-title").text();
        String normalized = heading == null ? "" : heading.replaceAll("\\s+", "");
        return normalized.contains("相关") || normalized.contains("相關") || normalized.contains("推荐") || normalized.contains("推薦");
    }

    private boolean shouldExcludeSection(Element section) {
        String heading = section.select("h1, h2, h3, h4, .section-title, .home-rows-title").text();
        String normalized = heading == null ? "" : heading.replaceAll("\\s+", "");
        return normalized.contains("评论") || normalized.contains("評論") || normalized.contains("新番资讯") || normalized.contains("新番資訊");
    }

    private String absolutizeWatchUrl(String href, String currentUrl) {
        if (href == null || href.isBlank() || !href.contains("watch?v=")) {
            return null;
        }
        if (href.startsWith("http://") || href.startsWith("https://")) {
            return href;
        }
        try {
            return java.net.URI.create(currentUrl).resolve(href).toString();
        } catch (Exception exception) {
            if (href.startsWith("/")) {
                return "https://hanime1.me" + href;
            }
            return null;
        }
    }
}
