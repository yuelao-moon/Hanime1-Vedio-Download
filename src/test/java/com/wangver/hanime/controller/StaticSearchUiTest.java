package com.wangver.hanime.controller;

import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertTrue;

class StaticSearchUiTest {

    private static final Path STATIC_ROOT = Path.of("src/main/resources/static");

    @Test
    void searchUiExposesClickableTypeFilterAndBrowseToolbar() throws Exception {
        String html = Files.readString(STATIC_ROOT.resolve("index.html"));
        String css = Files.readString(STATIC_ROOT.resolve("style.css"));
        String js = Files.readString(STATIC_ROOT.resolve("app.js"));

        assertTrue(html.contains("id=\"globalSearchTypeSelect\""));
        assertTrue(html.contains("id=\"browseSearchToolbar\""));
        assertTrue(html.contains("style.css?v=2.3"));
        assertTrue(html.contains("app.js?v=2.3"));
        assertTrue(html.contains("<option value=\"本日排行\">本日排行</option>"));
        assertTrue(html.contains("<option value=\"過去 24 小時\">過去 24 小時</option>"));
        assertTrue(html.contains("<option value=\"1 分鐘 +\">1 分鐘 +</option>"));
        assertTrue(css.contains(".global-search-shell"));
        assertTrue(css.contains("radial-gradient(circle at 10% 0%"));
        assertTrue(js.contains("syncSearchTypeControls"));
    }

    @Test
    void downloadCenterExposesBulkControlsAndParallelSetting() throws Exception {
        String html = Files.readString(STATIC_ROOT.resolve("index.html"));
        String css = Files.readString(STATIC_ROOT.resolve("style.css"));
        String js = Files.readString(STATIC_ROOT.resolve("app.js"));

        assertTrue(html.contains("id=\"pauseAllDownloadsBtn\""));
        assertTrue(html.contains("id=\"cancelAllDownloadsBtn\""));
        assertTrue(html.contains("id=\"maxConcurrentDownloads\""));
        assertTrue(css.contains(".download-center-controls"));
        assertTrue(js.contains("performDownloadBulkAction(\"pause-all\")"));
        assertTrue(js.contains("performDownloadBulkAction(\"cancel-all\")"));
        assertTrue(js.contains("maxConcurrentDownloads"));
    }
}
