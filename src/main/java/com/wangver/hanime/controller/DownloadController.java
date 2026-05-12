package com.wangver.hanime.controller;

import com.wangver.hanime.model.DownloadBatchRequest;
import com.wangver.hanime.model.DownloadSnapshot;
import com.wangver.hanime.service.DownloadService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/api/downloads")
public class DownloadController {

    private final DownloadService downloadService;

    public DownloadController(DownloadService downloadService) {
        this.downloadService = downloadService;
    }

    @GetMapping
    public ResponseEntity<DownloadSnapshot> getSnapshot() {
        return ResponseEntity.ok(downloadService.getSnapshot());
    }

    @PostMapping
    public ResponseEntity<DownloadSnapshot> enqueue(@RequestBody DownloadBatchRequest request) {
        return ResponseEntity.ok(downloadService.enqueue(request));
    }

    @PostMapping("/{taskId}/pause")
    public ResponseEntity<DownloadSnapshot> pause(@PathVariable String taskId) {
        return ResponseEntity.ok(downloadService.pauseTask(taskId));
    }

    @PostMapping("/{taskId}/resume")
    public ResponseEntity<DownloadSnapshot> resume(@PathVariable String taskId) {
        return ResponseEntity.ok(downloadService.resumeTask(taskId));
    }

    @PostMapping("/{taskId}/cancel")
    public ResponseEntity<DownloadSnapshot> cancel(@PathVariable String taskId) {
        return ResponseEntity.ok(downloadService.cancelTask(taskId));
    }

    @PostMapping("/pause-all")
    public ResponseEntity<DownloadSnapshot> pauseAll() {
        return ResponseEntity.ok(downloadService.pauseAll());
    }

    @PostMapping("/cancel-all")
    public ResponseEntity<DownloadSnapshot> cancelAll() {
        return ResponseEntity.ok(downloadService.cancelAll());
    }

    @PostMapping("/{taskId}/retry")
    public ResponseEntity<DownloadSnapshot> retry(@PathVariable String taskId) {
        return ResponseEntity.ok(downloadService.retryTask(taskId));
    }

    @PostMapping("/retry-all-failed")
    public ResponseEntity<DownloadSnapshot> retryAllFailed() {
        return ResponseEntity.ok(downloadService.retryAllFailed());
    }

    @DeleteMapping("/history")
    public ResponseEntity<DownloadSnapshot> clearHistory() {
        return ResponseEntity.ok(downloadService.clearHistory());
    }

    @PostMapping("/history/clear")
    public ResponseEntity<DownloadSnapshot> clearHistoryWithPost() {
        return ResponseEntity.ok(downloadService.clearHistory());
    }

    @GetMapping("/stream")
    public SseEmitter stream() {
        return downloadService.subscribe();
    }
}
