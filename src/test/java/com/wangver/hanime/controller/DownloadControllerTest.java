package com.wangver.hanime.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.wangver.hanime.model.DownloadBatchRequest;
import com.wangver.hanime.model.DownloadRequestItem;
import com.wangver.hanime.model.DownloadSnapshot;
import com.wangver.hanime.model.DownloadStatus;
import com.wangver.hanime.model.DownloadTaskView;
import com.wangver.hanime.service.DownloadService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(DownloadController.class)
class DownloadControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private DownloadService downloadService;

    @Test
    void returnsCurrentDownloadSnapshot() throws Exception {
        when(downloadService.getSnapshot()).thenReturn(snapshot());

        mockMvc.perform(get("/api/downloads"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks[0].title").value("完成任务"));
    }

    @Test
    void enqueuesNewDownloadTasks() throws Exception {
        when(downloadService.enqueue(any(DownloadBatchRequest.class))).thenReturn(snapshot());

        DownloadBatchRequest request = new DownloadBatchRequest();
        DownloadRequestItem item = new DownloadRequestItem();
        item.setTitle("测试任务");
        item.setDownloadUrl("https://media.example.com/test.mp4");
        request.setItems(List.of(item));

        mockMvc.perform(post("/api/downloads")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsBytes(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks[0].title").value("完成任务"));

        verify(downloadService).enqueue(any(DownloadBatchRequest.class));
    }

    @Test
    void pausesTask() throws Exception {
        when(downloadService.pauseTask("task-1")).thenReturn(snapshot());

        mockMvc.perform(post("/api/downloads/task-1/pause"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks[0].title").value("完成任务"));

        verify(downloadService).pauseTask("task-1");
    }

    @Test
    void resumesTask() throws Exception {
        when(downloadService.resumeTask("task-1")).thenReturn(snapshot());

        mockMvc.perform(post("/api/downloads/task-1/resume"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks[0].title").value("完成任务"));

        verify(downloadService).resumeTask("task-1");
    }

    @Test
    void cancelsTask() throws Exception {
        when(downloadService.cancelTask("task-1")).thenReturn(snapshot());

        mockMvc.perform(post("/api/downloads/task-1/cancel"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks[0].title").value("完成任务"));

        verify(downloadService).cancelTask("task-1");
    }

    @Test
    void pausesAllLiveTasks() throws Exception {
        when(downloadService.pauseAll()).thenReturn(snapshot());

        mockMvc.perform(post("/api/downloads/pause-all"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks[0].title").value("完成任务"));

        verify(downloadService).pauseAll();
    }

    @Test
    void cancelsAllLiveTasks() throws Exception {
        when(downloadService.cancelAll()).thenReturn(snapshot());

        mockMvc.perform(post("/api/downloads/cancel-all"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks[0].title").value("完成任务"));

        verify(downloadService).cancelAll();
    }

    @Test
    void retriesTask() throws Exception {
        when(downloadService.retryTask("task-1")).thenReturn(snapshot());

        mockMvc.perform(post("/api/downloads/task-1/retry"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks[0].title").value("完成任务"));

        verify(downloadService).retryTask("task-1");
    }

    @Test
    void clearsDownloadHistory() throws Exception {
        when(downloadService.clearHistory()).thenReturn(new DownloadSnapshot(List.of(), List.of(), List.of()));

        mockMvc.perform(delete("/api/downloads/history"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks").isEmpty());

        verify(downloadService).clearHistory();
    }

    @Test
    void clearsDownloadHistoryWithPostFallback() throws Exception {
        when(downloadService.clearHistory()).thenReturn(new DownloadSnapshot(List.of(), List.of(), List.of()));

        mockMvc.perform(post("/api/downloads/history/clear"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.historyTasks").isEmpty());

        verify(downloadService).clearHistory();
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
