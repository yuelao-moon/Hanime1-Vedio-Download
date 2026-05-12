package com.wangver.hanime.service;

import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

class HanimeParserServiceTest {

    private static String sampleDownloadPageHtml() {
        return "<html><body>"
                + "<table class='download-table'>"
                + "<tr><td></td><td>720p</td><td><a data-url='https://rapidgator.net/file/lower-quality'></a></td></tr>"
                + "<tr><td></td><td>1080p</td><td><a data-url='https://rapidgator.net/file/79865d10b7482c731a481421e4d2a35d'></a></td></tr>"
                + "</table>"
                + "</body></html>";
    }

    private static String sampleRealPlaylistHtml() {
        return "<html><body>"
                + "<div id='video-playlist-wrapper'>"
                + "  <div class='related-watch-wrap multiple-link-wrapper'>"
                + "    <a class='overlay' href='https://javchu.com/watch?v=166722'></a>"
                + "    <div class='card-mobile-panel inner'>"
                + "      <img src='https://vdownload.hembed.com/image/icon/card_doujin_background.jpg?secure=bg'>"
                + "      <img src='https://vdownload.hembed.com/image/thumbnail/166722l.jpg?secure=real' alt='JUR-556 我的新媽媽加奈就在我眼前被輪姦了-水戸かな'>"
                + "      <div class='card-mobile-title'>JUR-556 我的新媽媽加奈就在我眼前被輪姦了-水戸かな</div>"
                + "    </div>"
                + "  </div>"
                + "</div>"
                + "</body></html>";
    }

    private static String sampleRelatedVideosHtml() {
        return "<html><body>"
                + "<section class='home-rows-videos-wrapper'>"
                + "  <h3>新番资讯</h3>"
                + "  <a href='/watch?v=9001'>"
                + "    <img src='https://cdn.example.com/news-thumb.jpg'>"
                + "    <div class='home-rows-videos-title'>不該展示的新番资讯</div>"
                + "  </a>"
                + "</section>"
                + "<section class='home-rows-videos-wrapper'>"
                + "  <h3>评论</h3>"
                + "  <a href='/watch?v=9002'>"
                + "    <img src='https://cdn.example.com/comment-thumb.jpg'>"
                + "    <div class='home-rows-videos-title'>不該展示的评论卡片</div>"
                + "  </a>"
                + "</section>"
                + "<section class='home-rows-videos-wrapper'>"
                + "  <h3>相关视频</h3>"
                + "  <a href='/watch?v=4001'>"
                + "    <img src='https://cdn.example.com/related-1.jpg'>"
                + "    <div class='home-rows-videos-title'>相关视频一</div>"
                + "  </a>"
                + "  <a href='https://hanime1.me/watch?v=4002'>"
                + "    <img data-src='https://cdn.example.com/related-2.jpg'>"
                + "    <div class='home-rows-videos-title'>相关视频二</div>"
                + "  </a>"
                + "</section>"
                + "</body></html>";
    }

    private static String sampleRelatedTabContentHtml() {
        return "<html><body>"
                + "<div id='related-tabcontent'>"
                + "  <div class='row'>"
                + "    <div class='col-xs-6 col-sm-4 col-md-3'>"
                + "      <a href='/watch?v=143645' class='related-card'>"
                + "        <img data-src='https://cdn.example.com/tab-related-1.jpg' alt='相关卡片一'>"
                + "        <div class='card-mobile-title'>相关卡片一</div>"
                + "      </a>"
                + "    </div>"
                + "    <div class='col-xs-6 col-sm-4 col-md-3'>"
                + "      <a href='https://hanime1.me/watch?v=143646' class='related-card' title='相关卡片二'>"
                + "        <img src='https://cdn.example.com/tab-related-2.jpg'>"
                + "      </a>"
                + "    </div>"
                + "  </div>"
                + "</div>"
                + "</body></html>";
    }

    private static void injectHttpSessionService(HanimeParserService service, HanimeHttpSessionService httpSessionService) throws Exception {
        Field field = HanimeParserService.class.getDeclaredField("httpSessionService");
        field.setAccessible(true);
        field.set(service, httpSessionService);
    }

    @Test
    void extractsFirstDownloadUrlFromDownloadTable() throws Exception {
        HanimeParserService service = new HanimeParserService();
        Method method = HanimeParserService.class.getDeclaredMethod("extractFirstDownloadUrl", org.jsoup.nodes.Document.class);
        method.setAccessible(true);

        org.jsoup.nodes.Document doc = org.jsoup.Jsoup.parse(sampleDownloadPageHtml());
        String url = (String) method.invoke(service, doc);

        assertEquals("https://rapidgator.net/file/lower-quality", url);
    }

    @Test
    void prefersDownloadPageSourceOverHomepageStreamWhenBothExist() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String pageHtml = "<html><body><source src='https://cdn.example.com/video.m3u8'></body></html>";

        Method method = HanimeParserService.class.getDeclaredMethod("buildParseResult", String.class, String.class, String.class);
        method.setAccessible(true);

        @SuppressWarnings("unchecked")
        Map<String, Object> result = (Map<String, Object>) method.invoke(service, "https://hanime1.me/watch?v=test", pageHtml, sampleDownloadPageHtml());

        assertEquals("https://rapidgator.net/file/lower-quality", result.get("videoUrl"));
    }

    @Test
    void prefersDirectDownloadUrlWhenPlaywrightFindsLinkEarly() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String pageHtml = "<html><body><source src='https://cdn.example.com/video.m3u8'></body></html>";

        Method method = HanimeParserService.class.getDeclaredMethod("buildParseResult", String.class, String.class, String.class, String.class);
        method.setAccessible(true);

        @SuppressWarnings("unchecked")
        Map<String, Object> result = (Map<String, Object>) method.invoke(
                service,
                "https://hanime1.me/watch?v=test",
                pageHtml,
                null,
                "https://rapidgator.net/file/direct"
        );

        assertEquals("https://rapidgator.net/file/direct", result.get("videoUrl"));
    }

    @Test
    void takesFirstStreamFromSourceTagWhenNoDownloadTable() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String html = "<html><body><video><source src='https://cdn.example.com/video-720p.mp4'></video></body></html>";

        Method method = HanimeParserService.class.getDeclaredMethod("extractFirstStream", String.class);
        method.setAccessible(true);

        String stream = (String) method.invoke(service, html);
        assertEquals("https://cdn.example.com/video-720p.mp4", stream);
    }

    @Test
    void takesFirstStreamFromMp4RegexWhenNoSourceTag() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String html = "<html><body><a href='https://cdn.example.com/video-1080p.mp4'>download</a></body></html>";

        Method method = HanimeParserService.class.getDeclaredMethod("extractFirstStream", String.class);
        method.setAccessible(true);

        String stream = (String) method.invoke(service, html);
        assertEquals("https://cdn.example.com/video-1080p.mp4", stream);
    }

    @Test
    void takesFirstM3u8StreamWhenNoMp4Found() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String html = "<html><body><a href='https://cdn.example.com/video.m3u8'>hls</a></body></html>";

        Method method = HanimeParserService.class.getDeclaredMethod("extractFirstStream", String.class);
        method.setAccessible(true);

        String stream = (String) method.invoke(service, html);
        assertEquals("https://cdn.example.com/video.m3u8", stream);
    }

    @SuppressWarnings("unchecked")
    @Test
    void extractsPlaylistItemsFromOverlayBasedSeriesMarkup() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String html = "<html><body>"
                + "<div id='video-playlist-wrapper'>"
                + "  <div class='related-watch-wrap multiple-link-wrapper current'>"
                + "    <a class='overlay' href='/watch?v=2001'></a>"
                + "    <div class='card-mobile-panel inner'>"
                + "      <img src='https://cdn.example.com/current-background.jpg'>"
                + "      <img src='https://cdn.example.com/thumb-2001.jpg' alt='系列第1集'>"
                + "      <div class='card-mobile-title'>系列第1集</div>"
                + "    </div>"
                + "  </div>"
                + "</div>"
                + "<div id='video-playlist-wrapper'>"
                + "  <div class='related-watch-wrap multiple-link-wrapper'>"
                + "    <a class='overlay' href='/watch?v=2002'></a>"
                + "    <div class='card-mobile-panel inner'>"
                + "      <img src='https://cdn.example.com/thumb-2002.jpg' alt='系列第2集'>"
                + "      <div class='card-mobile-title'>系列第2集</div>"
                + "    </div>"
                + "  </div>"
                + "  <div class='related-watch-wrap multiple-link-wrapper'>"
                + "    <a class='overlay' href='https://hanime1.me/watch?v=2003'></a>"
                + "    <div class='card-mobile-panel inner'>"
                + "      <img data-src='https://cdn.example.com/thumb-2003.jpg' alt='系列第3集'>"
                + "      <div class='card-mobile-title'>系列第3集</div>"
                + "    </div>"
                + "  </div>"
                + "</div>"
                + "</body></html>";

        Method method = HanimeParserService.class.getDeclaredMethod("extractPlaylist", String.class, String.class);
        method.setAccessible(true);

        List<Map<String, String>> playlist = (List<Map<String, String>>) method.invoke(service, html, "https://hanime1.me/watch?v=2001");

        assertEquals(3, playlist.size());
        assertEquals("https://hanime1.me/watch?v=2001", playlist.get(0).get("url"));
        assertEquals("系列第1集", playlist.get(0).get("title"));
        assertEquals("https://cdn.example.com/thumb-2001.jpg", playlist.get(0).get("thumbnail"));
        assertEquals("https://hanime1.me/watch?v=2002", playlist.get(1).get("url"));
        assertEquals("系列第2集", playlist.get(1).get("title"));
        assertEquals("https://cdn.example.com/thumb-2002.jpg", playlist.get(1).get("thumbnail"));
        assertEquals("https://hanime1.me/watch?v=2003", playlist.get(2).get("url"));
        assertEquals("系列第3集", playlist.get(2).get("title"));
        assertEquals("https://cdn.example.com/thumb-2003.jpg", playlist.get(2).get("thumbnail"));
    }

    @SuppressWarnings("unchecked")
    @Test
    void prefersRealThumbnailOverBackgroundPlaceholderInPlaylist() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String html = "<html><body>"
                + "<div id='video-playlist-wrapper'>"
                + "  <div class='related-watch-wrap multiple-link-wrapper'>"
                + "    <a class='overlay' href='/watch?v=3001'></a>"
                + "    <div class='card-mobile-panel inner'>"
                + "      <img src='https://vdownload.hembed.com/image/icon/card_doujin_background.jpg?secure=abc'>"
                + "      <img src='https://vdownload.hembed.com/image/thumbnail/3001l.jpg?secure=thumb'>"
                + "      <div class='card-mobile-title'>真實封面項</div>"
                + "    </div>"
                + "  </div>"
                + "</div>"
                + "</body></html>";

        Method method = HanimeParserService.class.getDeclaredMethod("extractPlaylist", String.class, String.class);
        method.setAccessible(true);

        List<Map<String, String>> playlist = (List<Map<String, String>>) method.invoke(service, html, "https://hanime1.me/watch?v=3001");

        assertEquals(1, playlist.size());
        assertEquals("https://vdownload.hembed.com/image/thumbnail/3001l.jpg?secure=thumb", playlist.get(0).get("thumbnail"));
    }

    @SuppressWarnings("unchecked")
    @Test
    void extractsSeriesListFromRealPlaylistHtmlSample() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String html = sampleRealPlaylistHtml();

        Method method = HanimeParserService.class.getDeclaredMethod("extractPlaylist", String.class, String.class);
        method.setAccessible(true);

        List<Map<String, String>> playlist = (List<Map<String, String>>) method.invoke(service, html, "https://javchu.com/watch?v=92205");

        assertFalse(playlist.isEmpty());
        assertTrue(playlist.stream().anyMatch(item -> "https://javchu.com/watch?v=166722".equals(item.get("url"))
                && "JUR-556 我的新媽媽加奈就在我眼前被輪姦了-水戸かな".equals(item.get("title"))));
    }

    @SuppressWarnings("unchecked")
    @Test
    void extractsRelatedVideosWithoutCommentsOrNewsCards() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String html = sampleRelatedVideosHtml();

        Method method = HanimeParserService.class.getDeclaredMethod("extractRelatedVideos", String.class, String.class);
        method.setAccessible(true);

        List<Map<String, String>> relatedVideos = (List<Map<String, String>>) method.invoke(service, html, "https://hanime1.me/watch?v=166763");

        assertEquals(2, relatedVideos.size());
        assertEquals("https://hanime1.me/watch?v=4001", relatedVideos.get(0).get("url"));
        assertEquals("相关视频一", relatedVideos.get(0).get("title"));
        assertEquals("https://cdn.example.com/related-1.jpg", relatedVideos.get(0).get("thumbnail"));
        assertEquals("https://hanime1.me/watch?v=4002", relatedVideos.get(1).get("url"));
        assertEquals("相关视频二", relatedVideos.get(1).get("title"));
        assertEquals("https://cdn.example.com/related-2.jpg", relatedVideos.get(1).get("thumbnail"));
    }

    @SuppressWarnings("unchecked")
    @Test
    void extractsRelatedVideosFromRelatedTabContentRow() throws Exception {
        HanimeParserService service = new HanimeParserService();
        String html = sampleRelatedTabContentHtml();

        Method method = HanimeParserService.class.getDeclaredMethod("extractRelatedVideos", String.class, String.class);
        method.setAccessible(true);

        List<Map<String, String>> relatedVideos = (List<Map<String, String>>) method.invoke(service, html, "https://hanime1.me/watch?v=143644");

        assertEquals(2, relatedVideos.size());
        assertEquals("https://hanime1.me/watch?v=143645", relatedVideos.get(0).get("url"));
        assertEquals("相关卡片一", relatedVideos.get(0).get("title"));
        assertEquals("https://cdn.example.com/tab-related-1.jpg", relatedVideos.get(0).get("thumbnail"));
        assertEquals("https://hanime1.me/watch?v=143646", relatedVideos.get(1).get("url"));
        assertEquals("相关卡片二", relatedVideos.get(1).get("title"));
        assertEquals("https://cdn.example.com/tab-related-2.jpg", relatedVideos.get(1).get("thumbnail"));
    }

    @Test
    void usesHttpForParseAndReturnsFirstDownloadLink() throws Exception {
        HanimeParserService service = new HanimeParserService();
        HanimeHttpSessionService httpSessionService = mock(HanimeHttpSessionService.class);
        injectHttpSessionService(service, httpSessionService);

        when(httpSessionService.fetchHtml("https://hanime1.me/watch?v=166763", "https://hanime1.me/"))
                .thenReturn("<html><head><title>Test</title></head><body><h1 class='title'>Test Video</h1><source src='https://cdn.example.com/video-720p.mp4'></body></html>");
        when(httpSessionService.fetchHtml("https://hanime1.me/download?v=166763", "https://hanime1.me/watch?v=166763"))
                .thenReturn(sampleDownloadPageHtml());

        Map<String, Object> result = service.parse("https://hanime1.me/watch?v=166763");

        assertEquals("https://rapidgator.net/file/lower-quality", result.get("videoUrl"));
        assertEquals("Test Video", result.get("title"));
        verify(httpSessionService).fetchHtml("https://hanime1.me/watch?v=166763", "https://hanime1.me/");
        verify(httpSessionService).fetchHtml("https://hanime1.me/download?v=166763", "https://hanime1.me/watch?v=166763");
    }

    @Test
    void returnsEmptyVideoUrlWhenNoDownloadLinkFound() throws Exception {
        HanimeParserService service = new HanimeParserService();
        HanimeHttpSessionService httpSessionService = mock(HanimeHttpSessionService.class);
        injectHttpSessionService(service, httpSessionService);

        when(httpSessionService.fetchHtml("https://hanime1.me/watch?v=166763", "https://hanime1.me/"))
                .thenReturn("<html><head><title>Test</title></head><body><h1 class='title'>Test</h1></body></html>");
        when(httpSessionService.fetchHtml("https://hanime1.me/download?v=166763", "https://hanime1.me/watch?v=166763"))
                .thenReturn("<html><body>no links</body></html>");

        Map<String, Object> result = service.parse("https://hanime1.me/watch?v=166763");

        assertEquals("", result.get("videoUrl"));
    }

    @Test
    void rethrowsWhenNoBrowserFallbackAvailable() throws Exception {
        HanimeParserService service = new HanimeParserService();
        HanimeHttpSessionService httpSessionService = mock(HanimeHttpSessionService.class);
        injectHttpSessionService(service, httpSessionService);

        when(httpSessionService.fetchHtml(anyString(), anyString())).thenThrow(new HttpSessionExpiredException("session expired"));

        assertThrows(IllegalStateException.class, () ->
                service.parse("https://hanime1.me/watch?v=166763"));
    }

    @Test
    void fallsBackToPlaywrightWhenHttpFails() throws Exception {
        HanimeParserService service = new HanimeParserService();
        HanimeHttpSessionService httpSessionService = mock(HanimeHttpSessionService.class);
        PlaywrightBrowserService browserService = mock(PlaywrightBrowserService.class);
        com.microsoft.playwright.Page page = mock(com.microsoft.playwright.Page.class);
        injectHttpSessionService(service, httpSessionService);

        java.lang.reflect.Field bf = HanimeParserService.class.getDeclaredField("browserService");
        bf.setAccessible(true);
        bf.set(service, browserService);

        when(httpSessionService.fetchHtml(anyString(), anyString())).thenThrow(new HttpSessionExpiredException("session expired"));
        when(browserService.runSerialized(any())).thenAnswer(inv -> {
            PlaywrightBrowserService.CheckedSupplier<?> supplier = inv.getArgument(0);
            return supplier.get();
        });
        when(browserService.createPage()).thenReturn(page);
        when(page.content()).thenReturn("<html><head><title>Test</title></head><body><h1 class='title'>Fallback</h1><source src='https://cdn.example.com/video.m3u8'></body></html>");

        Map<String, Object> result = service.parse("https://hanime1.me/watch?v=166763");

        assertEquals("Fallback", result.get("title"));
        assertEquals("https://cdn.example.com/video.m3u8", result.get("videoUrl"));
    }
}
