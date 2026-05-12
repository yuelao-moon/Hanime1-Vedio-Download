package com.wangver.hanime.service;

import com.microsoft.playwright.Page;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class HanimeBrowseServiceTest {

    private static String sampleBrowseHtml() {
        return "<html><body>"
                + "<div title='[ぬるぬるアニメ] JK200人の巨乳がぶるん揺れ！運動部のムチムチ女子と汗だく乱交中出しセックス！【133分】' class='video-item-container'>"
                + "  <div class='horizontal-card'>"
                + "    <a href='https://hanime1.me/watch?v=404781' class='video-link'>"
                + "      <div class='thumb-container'><img class='main-thumb' src='https://vdownload.hembed.com/image/thumbnail/404781l.jpg'></div>"
                + "      <div class='title'>JK200人の巨乳がぶるん揺れ！運動部のムチムチ女子と汗だく乱交中出しセックス！【133分】</div>"
                + "    </a>"
                + "  </div>"
                + "</div>"
                + "</body></html>";
    }

    private static void injectBrowserService(HanimeBrowseService service, PlaywrightBrowserService browserService) throws Exception {
        Field field = HanimeBrowseService.class.getDeclaredField("browserService");
        field.setAccessible(true);
        field.set(service, browserService);
    }

    private static void stubSerializedExecution(PlaywrightBrowserService browserService) throws Exception {
        when(browserService.runSerialized(any())).thenAnswer(invocation -> {
            PlaywrightBrowserService.CheckedSupplier<?> supplier = invocation.getArgument(0);
            return supplier.get();
        });
    }

    @SuppressWarnings("unchecked")
    @Test
    void parsesMotionAnimeGridCardsUsingCurrentSiteMarkup() throws Exception {
        HanimeBrowseService service = new HanimeBrowseService();
        String html = sampleBrowseHtml();

        Method method = HanimeBrowseService.class.getDeclaredMethod("parseVideoGrid", String.class);
        method.setAccessible(true);

        List<Map<String, String>> videos = (List<Map<String, String>>) method.invoke(service, html);

        assertFalse(videos.isEmpty());
        List<String> urls = videos.stream().map(video -> video.get("url")).collect(Collectors.toList());
        assertTrue(urls.contains("https://hanime1.me/watch?v=404781"));
        Map<String, String> firstVideo = videos.stream()
                .filter(video -> "https://hanime1.me/watch?v=404781".equals(video.get("url")))
                .findFirst()
                .orElseThrow();
        assertEquals("JK200人の巨乳がぶるん揺れ！運動部のムチムチ女子と汗だく乱交中出しセックス！【133分】", firstVideo.get("title"));
    }

    @Test
    void fetchesCategoryViaPlaywrightAndReturnsContent() throws Exception {
        HanimeBrowseService service = new HanimeBrowseService();
        PlaywrightBrowserService browserService = mock(PlaywrightBrowserService.class);
        Page page = mock(Page.class);
        injectBrowserService(service, browserService);
        stubSerializedExecution(browserService);

        when(browserService.createPage()).thenReturn(page);
        when(page.content()).thenReturn(sampleBrowseHtml());

        Map<String, Object> result = service.fetchCategory("Motion Anime", 1);

        @SuppressWarnings("unchecked")
        List<Map<String, String>> videos = (List<Map<String, String>>) result.get("videos");
        assertFalse(videos.isEmpty());
        assertEquals(1, result.get("currentPage"));
        verify(browserService).createPage();
        verify(page).close();
    }

    @SuppressWarnings("unchecked")
    @Test
    void prefersContainerTitleAttributeWhenVisibleTitleIsMojibake() throws Exception {
        HanimeBrowseService service = new HanimeBrowseService();
        String html = "<html><body>"
                + "<div title='[Shikikat] ぺどいさん ♠BBC♠' class='video-item-container'>"
                + "<a href='https://hanime1.me/watch?v=404948'>"
                + "<img src='https://cdn.example.com/thumb.jpg'>"
                + "<div class='title'>ãºã©ããã â BBCâ </div>"
                + "</a></div>"
                + "</body></html>";

        Method method = HanimeBrowseService.class.getDeclaredMethod("parseVideoGrid", String.class);
        method.setAccessible(true);

        List<Map<String, String>> videos = (List<Map<String, String>>) method.invoke(service, html);

        assertEquals("[Shikikat] ぺどいさん ♠BBC♠", videos.get(0).get("title"));
    }

    @Test
    void resolvesExplicitSearchUrlFor2dAnimationCategory() throws Exception {
        HanimeBrowseService service = new HanimeBrowseService();

        Method method = HanimeBrowseService.class.getDeclaredMethod("buildCategoryUrl", String.class, int.class);
        method.setAccessible(true);

        String url = (String) method.invoke(service, "2D動畫", 3);

        assertEquals("https://hanime1.me/search?genre=2D%E5%8B%95%E7%95%AB&page=3", url);
    }

    @Test
    void buildsSearchUrlWithKeywordTagsAndFilters() throws Exception {
        HanimeBrowseService service = new HanimeBrowseService();

        Method method = HanimeBrowseService.class.getDeclaredMethod(
                "buildSearchUrl",
                String.class,
                String.class,
                String.class,
                List.class,
                String.class,
                String.class,
                String.class,
                int.class
        );
        method.setAccessible(true);

        String url = (String) method.invoke(
                service,
                "巨乳",
                "",
                "",
                List.of("魅魔", "中文配音"),
                "本日排行",
                "過去 24 小時",
                "1 分鐘 +",
                2
        );

        assertEquals("https://hanime1.me/search?query=%E5%B7%A8%E4%B9%B3&type=&genre=&tags%5B%5D=%E9%AD%85%E9%AD%94&tags%5B%5D=%E4%B8%AD%E6%96%87%E9%85%8D%E9%9F%B3&sort=%E6%9C%AC%E6%97%A5%E6%8E%92%E8%A1%8C&date=%E9%81%8E%E5%8E%BB+24+%E5%B0%8F%E6%99%82&duration=1+%E5%88%86%E9%90%98+%2B&page=2", url);
    }

    @Test
    void fallbackSearchOptionsContainCommonHanimeFilters() throws Exception {
        HanimeBrowseService service = new HanimeBrowseService();

        Map<String, Object> options = service.fetchSearchOptions();

        @SuppressWarnings("unchecked")
        List<String> durations = (List<String>) options.get("durations");
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> tagGroups = (List<Map<String, Object>>) options.get("tagGroups");

        assertTrue(durations.contains("1 分鐘 +"));
        assertTrue(tagGroups.stream()
                .flatMap(group -> ((List<String>) group.get("tags")).stream())
                .anyMatch("魅魔"::equals));
    }

    @SuppressWarnings("unchecked")
    @Test
    void searchReturnsEmptyResultInsteadOfFailingWhenNoCardsArePresent() throws Exception {
        HanimeBrowseService service = new HanimeBrowseService();
        PlaywrightBrowserService browserService = mock(PlaywrightBrowserService.class);
        Page page = mock(Page.class);
        injectBrowserService(service, browserService);
        stubSerializedExecution(browserService);

        when(browserService.createPage()).thenReturn(page);
        doThrow(new RuntimeException("no cards")).when(page).waitForSelector(any(String.class), any(Page.WaitForSelectorOptions.class));
        when(page.content()).thenReturn("<html><body><div class='empty'>沒有結果</div></body></html>");

        Map<String, Object> result = service.fetchSearch("巨乳", "", "", List.of("魅魔"), "本日排行", "過去 24 小時", "1 分鐘 +", 1);

        assertEquals(List.of(), result.get("videos"));
        assertEquals(1, result.get("currentPage"));
        verify(page).close();
    }

    @Test
    void handlesPageTimeoutGracefully() throws Exception {
        HanimeBrowseService service = new HanimeBrowseService();
        PlaywrightBrowserService browserService = mock(PlaywrightBrowserService.class);
        Page page = mock(Page.class);
        injectBrowserService(service, browserService);
        stubSerializedExecution(browserService);

        when(browserService.createPage()).thenReturn(page);
        doThrow(new RuntimeException("timeout")).when(page).waitForSelector(any(String.class), any(Page.WaitForSelectorOptions.class));

        assertThrows(Exception.class, () -> service.fetchCategory("Motion Anime", 1));
        verify(page).close();
    }
}
