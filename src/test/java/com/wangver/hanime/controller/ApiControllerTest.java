package com.wangver.hanime.controller;

import com.wangver.hanime.model.AppSettings;
import com.wangver.hanime.model.DownloadSnapshot;
import com.wangver.hanime.model.DownloadStatus;
import com.wangver.hanime.model.DownloadTaskView;
import com.wangver.hanime.service.DownloadService;
import com.wangver.hanime.service.HanimeBrowseService;
import com.wangver.hanime.service.HanimeParserService;
import com.wangver.hanime.service.HistoryCoverService;
import com.wangver.hanime.service.ImageProxyService;
import com.wangver.hanime.service.LocalCoverService;
import com.wangver.hanime.service.PlaywrightBrowserService;
import com.wangver.hanime.service.SettingsManager;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ApiController.class)
class ApiControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private HanimeParserService parserService;

    @MockBean
    private SettingsManager settingsManager;

    @MockBean
    private HanimeBrowseService browseService;

    @MockBean
    private PlaywrightBrowserService playwrightService;

    @MockBean
    private DownloadService downloadService;

    @MockBean
    private ImageProxyService imageProxyService;

    @MockBean
    private HistoryCoverService historyCoverService;

    @MockBean
    private LocalCoverService localCoverService;

    @Test
    void clearsCacheAlsoClearsDownloadHistory() throws Exception {
        when(downloadService.clearHistory()).thenReturn(snapshot());

        mockMvc.perform(post("/api/settings/clear-cache"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks[0].title").value("完成任务"));

        verify(playwrightService).forceCloseAndClearCache();
        verify(downloadService).clearHistory();
    }

    @Test
    void proxiesImageWithContentTypeFromImageService() throws Exception {
        when(imageProxyService.fetchImage("https://cdn.example.com/cover.webp"))
                .thenReturn(new ImageProxyService.ImageResponse(new byte[]{1, 2, 3}, "image/webp"));

        mockMvc.perform(get("/api/proxy/image").param("url", "https://cdn.example.com/cover.webp"))
                .andExpect(status().isOk())
                .andExpect(header().string("Content-Type", "image/webp"))
                .andExpect(content().bytes(new byte[]{1, 2, 3}));

        verify(imageProxyService).fetchImage("https://cdn.example.com/cover.webp");
    }

    @Test
    void proxiesHistoryCoverByResolvingThumbnailFromVideoPageUrl() throws Exception {
        when(historyCoverService.fetchCover("https://hanime1.me/watch?v=102579", null))
                .thenReturn(new ImageProxyService.ImageResponse(new byte[]{4, 5, 6}, "image/jpeg"));

        mockMvc.perform(get("/api/proxy/history-cover").param("url", "https://hanime1.me/watch?v=102579"))
                .andExpect(status().isOk())
                .andExpect(header().string("Content-Type", "image/jpeg"))
                .andExpect(header().string("Cache-Control", "public, max-age=86400"))
                .andExpect(content().bytes(new byte[]{4, 5, 6}));

        verify(historyCoverService).fetchCover("https://hanime1.me/watch?v=102579", null);
    }

    @Test
    void searchesWithKeywordTagsAndFilters() throws Exception {
        when(browseService.fetchSearch(
                "巨乳",
                "",
                "",
                List.of("魅魔"),
                "本日排行",
                "過去 24 小時",
                "1 分鐘 +",
                2
        )).thenReturn(Map.of(
                "videos", List.of(Map.of(
                        "title", "搜索结果",
                        "url", "https://hanime1.me/watch?v=1",
                        "thumbnail", "https://cdn.example.com/1.jpg"
                )),
                "currentPage", 2,
                "totalPages", 5
        ));

        mockMvc.perform(get("/api/search")
                        .param("query", "巨乳")
                        .param("type", "")
                        .param("genre", "")
                        .param("tags[]", "魅魔")
                        .param("sort", "本日排行")
                        .param("date", "過去 24 小時")
                        .param("duration", "1 分鐘 +")
                        .param("page", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.videos[0].title").value("搜索结果"))
                .andExpect(jsonPath("$.currentPage").value(2))
                .andExpect(jsonPath("$.totalPages").value(5));

        verify(browseService).fetchSearch(
                eq("巨乳"),
                eq(""),
                eq(""),
                eq(List.of("魅魔")),
                eq("本日排行"),
                eq("過去 24 小時"),
                eq("1 分鐘 +"),
                eq(2)
        );
    }

    @Test
    void returnsSearchOptions() throws Exception {
        when(browseService.fetchSearchOptions()).thenReturn(Map.of(
                "types", List.of("裏番"),
                "sorts", List.of("本日排行"),
                "dates", List.of("過去 24 小時"),
                "durations", List.of("1 分鐘 +"),
                "tagGroups", List.of(Map.of("name", "角色設定", "tags", List.of("魅魔")))
        ));

        mockMvc.perform(get("/api/search/options"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.durations[0]").value("1 分鐘 +"))
                .andExpect(jsonPath("$.tagGroups[0].tags[0]").value("魅魔"));

        verify(browseService).fetchSearchOptions();
    }

    private DownloadSnapshot snapshot() {
        DownloadTaskView historyTask = new DownloadTaskView(
                "1",
                "完成任务",
                "https://hanime1.me/watch?v=1",
                "https://media.example.com/1.mp4",
                "https://image.example.com/1.jpg",
                "完成任务.mp4",
                "D:/Downloads/完成任务.mp4",
                DownloadStatus.COMPLETED,
                100.0,
                100,
                100,
                null,
                "2026-03-07T10:00:00Z",
                "2026-03-07T10:00:01Z",
                "2026-03-07T10:01:00Z"
        );
        return new DownloadSnapshot(List.of(), List.of(), List.of(historyTask));
    }
}
