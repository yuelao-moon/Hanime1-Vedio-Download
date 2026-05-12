package com.wangver.hanime.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.wangver.hanime.model.AppSettings;
import com.wangver.hanime.model.DownloadBatchRequest;
import com.wangver.hanime.model.DownloadProgress;
import com.wangver.hanime.model.DownloadRequestItem;
import com.wangver.hanime.model.DownloadSnapshot;
import com.wangver.hanime.model.DownloadStatus;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DownloadServiceTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @TempDir
    Path tempDir;

    @Test
    void processesQueuedTasksInOrderAndMovesThemToHistory() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        AppSettings settings = settingsManager.getSettings();
        settings.setMaxConcurrentDownloads(1);
        settingsManager.saveSettings(settings);
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        CountDownLatch completed = new CountDownLatch(2);
        List<String> executionOrder = new CopyOnWriteArrayList<>();

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService service = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                request -> new DownloadService.ResolvedDownload(
                        request.getTitle(),
                        request.getPageUrl(),
                        request.getDownloadUrl(),
                        request.getThumbnail(),
                        request.getTitle() + ".mp4"
                ),
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    executionOrder.add(resolvedDownload.title());
                    progressConsumer.accept(new DownloadProgress(1, 2));
                    Files.writeString(targetFile, resolvedDownload.title());
                    progressConsumer.accept(new DownloadProgress(2, 2));
                    completed.countDown();
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(
                    item("Alpha", null, "https://media.example.com/a.mp4"),
                    item("Beta", null, "https://media.example.com/b.mp4")
            ));

            service.enqueue(request);

            assertTrue(completed.await(5, TimeUnit.SECONDS));
            assertTrue(waitUntil(() -> service.getSnapshot().historyTasks().size() == 2));

            DownloadSnapshot snapshot = service.getSnapshot();
            assertEquals(List.of("Alpha", "Beta"), executionOrder);
            assertEquals(0, snapshot.activeTasks().size());
            assertEquals(0, snapshot.queuedTasks().size());
            assertEquals(2, snapshot.historyTasks().size());
            assertEquals(DownloadStatus.COMPLETED, snapshot.historyTasks().get(0).getStatus());
            assertTrue(Files.exists(tempDir.resolve("download-history.json")));
        } finally {
            service.shutdown();
        }
    }

    @Test
    void resolvesPageUrlWhenDirectDownloadUrlIsMissing() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        CountDownLatch completed = new CountDownLatch(1);
        AtomicInteger resolverCalls = new AtomicInteger();

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService service = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                request -> {
                    resolverCalls.incrementAndGet();
                    return new DownloadService.ResolvedDownload(
                            "Resolved Title",
                            request.getPageUrl(),
                            "https://media.example.com/resolved.mp4",
                            request.getThumbnail(),
                            "Resolved Title.mp4"
                    );
                },
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    Files.writeString(targetFile, resolvedDownload.title());
                    progressConsumer.accept(new DownloadProgress(1, 1));
                    completed.countDown();
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(item("待解析任务", "https://hanime1.me/watch?v=123", null)));

            service.enqueue(request);

            assertTrue(completed.await(5, TimeUnit.SECONDS));
            assertTrue(waitUntil(() -> service.getSnapshot().historyTasks().size() == 1));

            assertEquals(1, resolverCalls.get());
            assertEquals("Resolved Title", service.getSnapshot().historyTasks().get(0).getTitle());
        } finally {
            service.shutdown();
        }
    }

    @Test
    void loadsPersistedHistoryWhenServiceRestarts() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        CountDownLatch completed = new CountDownLatch(1);

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService firstService = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                request -> new DownloadService.ResolvedDownload(
                        request.getTitle(),
                        request.getPageUrl(),
                        request.getDownloadUrl(),
                        request.getThumbnail(),
                        request.getTitle() + ".mp4"
                ),
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    Files.writeString(targetFile, resolvedDownload.title());
                    progressConsumer.accept(new DownloadProgress(1, 1));
                    completed.countDown();
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(item("历史任务", null, "https://media.example.com/history.mp4")));
            firstService.enqueue(request);

            assertTrue(completed.await(5, TimeUnit.SECONDS));
            assertTrue(waitUntil(() -> firstService.getSnapshot().historyTasks().size() == 1));
        } finally {
            firstService.shutdown();
        }

        DownloadService secondService = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                request -> {
                    throw new IllegalStateException("本测试不会执行到这里");
                },
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    throw new IllegalStateException("本测试不会执行到这里");
                }
        );

        try {
            assertEquals(1, secondService.getSnapshot().historyTasks().size());
            assertEquals("历史任务", secondService.getSnapshot().historyTasks().get(0).getTitle());
        } finally {
            secondService.shutdown();
        }
    }

    @Test
    void pausesAndResumesActiveTask() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        CountDownLatch started = new CountDownLatch(1);
        CountDownLatch finished = new CountDownLatch(1);

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService service = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                request -> new DownloadService.ResolvedDownload(
                        request.getTitle(),
                        request.getPageUrl(),
                        request.getDownloadUrl(),
                        request.getThumbnail(),
                        request.getTitle() + ".mp4"
                ),
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    started.countDown();
                    progressConsumer.accept(new DownloadProgress(1, 4));
                    Thread.sleep(200);
                    control.awaitIfPaused();
                    progressConsumer.accept(new DownloadProgress(2, 4));
                    control.awaitIfPaused();
                    Files.writeString(targetFile, resolvedDownload.title());
                    progressConsumer.accept(new DownloadProgress(4, 4));
                    finished.countDown();
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(item("可暂停任务", null, "https://media.example.com/pause.mp4")));

            service.enqueue(request);

            assertTrue(started.await(5, TimeUnit.SECONDS));
            String taskId = service.getSnapshot().activeTasks().get(0).getId();
            service.pauseTask(taskId);
            assertTrue(waitUntil(() -> service.getSnapshot().activeTasks().stream()
                    .anyMatch(task -> task.getId().equals(taskId) && task.getStatus() == DownloadStatus.PAUSED)));

            service.resumeTask(taskId);
            assertTrue(finished.await(5, TimeUnit.SECONDS));
            assertTrue(waitUntil(() -> service.getSnapshot().historyTasks().stream()
                    .anyMatch(task -> task.getId().equals(taskId) && task.getStatus() == DownloadStatus.COMPLETED)));
        } finally {
            service.shutdown();
        }
    }

    @Test
    void cancelsQueuedTaskBeforeItStarts() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        AppSettings settings = settingsManager.getSettings();
        settings.setMaxConcurrentDownloads(1);
        settingsManager.saveSettings(settings);
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        CountDownLatch blocker = new CountDownLatch(1);
        AtomicBoolean secondTaskRan = new AtomicBoolean(false);

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService service = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                request -> new DownloadService.ResolvedDownload(
                        request.getTitle(),
                        request.getPageUrl(),
                        request.getDownloadUrl(),
                        request.getThumbnail(),
                        request.getTitle() + ".mp4"
                ),
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    if (resolvedDownload.title().equals("第一个任务")) {
                        blocker.await(5, TimeUnit.SECONDS);
                    } else {
                        secondTaskRan.set(true);
                    }
                    Files.writeString(targetFile, resolvedDownload.title());
                    progressConsumer.accept(new DownloadProgress(1, 1));
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(
                    item("第一个任务", null, "https://media.example.com/1.mp4"),
                    item("待取消任务", null, "https://media.example.com/2.mp4")
            ));

            DownloadSnapshot snapshot = service.enqueue(request);
            String cancelledTaskId = snapshot.queuedTasks().stream()
                    .filter(task -> "待取消任务".equals(task.getTitle()))
                    .findFirst()
                    .orElseThrow()
                    .getId();

            assertTrue(waitUntil(() -> service.getSnapshot().activeTasks().stream()
                    .anyMatch(task -> "第一个任务".equals(task.getTitle()))));

            service.cancelTask(cancelledTaskId);
            blocker.countDown();

            assertTrue(waitUntil(() -> service.getSnapshot().historyTasks().stream()
                    .anyMatch(task -> task.getId().equals(cancelledTaskId) && task.getStatus() == DownloadStatus.CANCELLED)));
            assertEquals(false, secondTaskRan.get());
        } finally {
            blocker.countDown();
            service.shutdown();
        }
    }

    @Test
    void startsThreeDownloadsInParallelByDefault() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        CountDownLatch started = new CountDownLatch(3);
        CountDownLatch release = new CountDownLatch(1);

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService service = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                this::resolved,
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    started.countDown();
                    release.await(5, TimeUnit.SECONDS);
                    Files.writeString(targetFile, resolvedDownload.title());
                    progressConsumer.accept(new DownloadProgress(1, 1));
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(
                    item("并行任务 1", null, "https://media.example.com/1.mp4"),
                    item("并行任务 2", null, "https://media.example.com/2.mp4"),
                    item("并行任务 3", null, "https://media.example.com/3.mp4"),
                    item("并行任务 4", null, "https://media.example.com/4.mp4")
            ));

            service.enqueue(request);

            assertTrue(started.await(5, TimeUnit.SECONDS));
            assertTrue(waitUntil(() -> service.getSnapshot().activeTasks().size() == 3));
            assertEquals(1, service.getSnapshot().queuedTasks().size());
        } finally {
            release.countDown();
            service.shutdown();
        }
    }

    @Test
    void honorsConfiguredParallelDownloadLimit() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        AppSettings settings = settingsManager.getSettings();
        settings.setMaxConcurrentDownloads(2);
        settingsManager.saveSettings(settings);
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        CountDownLatch started = new CountDownLatch(2);
        CountDownLatch release = new CountDownLatch(1);

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService service = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                this::resolved,
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    started.countDown();
                    release.await(5, TimeUnit.SECONDS);
                    Files.writeString(targetFile, resolvedDownload.title());
                    progressConsumer.accept(new DownloadProgress(1, 1));
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(
                    item("限制任务 1", null, "https://media.example.com/1.mp4"),
                    item("限制任务 2", null, "https://media.example.com/2.mp4"),
                    item("限制任务 3", null, "https://media.example.com/3.mp4")
            ));

            service.enqueue(request);

            assertTrue(started.await(5, TimeUnit.SECONDS));
            assertTrue(waitUntil(() -> service.getSnapshot().activeTasks().size() == 2));
            assertEquals(1, service.getSnapshot().queuedTasks().size());
        } finally {
            release.countDown();
            service.shutdown();
        }
    }

    @Test
    void pausesAndCancelsAllLiveTasks() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        CountDownLatch started = new CountDownLatch(2);
        CountDownLatch release = new CountDownLatch(1);

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService service = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                this::resolved,
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    started.countDown();
                    progressConsumer.accept(new DownloadProgress(1, 10));
                    release.await(5, TimeUnit.SECONDS);
                    control.throwIfCancelled();
                    Files.writeString(targetFile, resolvedDownload.title());
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(
                    item("批量任务 1", null, "https://media.example.com/1.mp4"),
                    item("批量任务 2", null, "https://media.example.com/2.mp4"),
                    item("批量任务 3", null, "https://media.example.com/3.mp4")
            ));

            service.enqueue(request);

            assertTrue(started.await(5, TimeUnit.SECONDS));
            DownloadSnapshot paused = service.pauseAll();
            assertEquals(3, paused.activeTasks().size() + paused.queuedTasks().size());
            assertTrue(paused.activeTasks().stream().allMatch(task -> task.getStatus() == DownloadStatus.PAUSED));
            assertTrue(paused.queuedTasks().stream().allMatch(task -> task.getStatus() == DownloadStatus.PAUSED));

            DownloadSnapshot cancelled = service.cancelAll();
            assertEquals(0, cancelled.queuedTasks().size());

            release.countDown();
            assertTrue(waitUntil(() -> service.getSnapshot().historyTasks().stream()
                    .filter(task -> task.getStatus() == DownloadStatus.CANCELLED)
                    .count() == 3));
        } finally {
            release.countDown();
            service.shutdown();
        }
    }

    @Test
    void cancellingActiveTaskUpdatesSnapshotImmediately() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        CountDownLatch started = new CountDownLatch(1);
        CountDownLatch release = new CountDownLatch(1);

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService service = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                request -> new DownloadService.ResolvedDownload(
                        request.getTitle(),
                        request.getPageUrl(),
                        request.getDownloadUrl(),
                        request.getThumbnail(),
                        request.getTitle() + ".mp4"
                ),
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    started.countDown();
                    progressConsumer.accept(new DownloadProgress(1, 10));
                    release.await(5, TimeUnit.SECONDS);
                    control.throwIfCancelled();
                    Files.writeString(targetFile, resolvedDownload.title());
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(item("可取消任务", null, "https://media.example.com/cancel.mp4")));

            service.enqueue(request);

            assertTrue(started.await(5, TimeUnit.SECONDS));
            String taskId = service.getSnapshot().activeTasks().get(0).getId();
            DownloadSnapshot snapshot = service.cancelTask(taskId);

            assertEquals(DownloadStatus.CANCELLED, snapshot.activeTasks().get(0).getStatus());

            release.countDown();
            assertTrue(waitUntil(() -> service.getSnapshot().historyTasks().stream()
                    .anyMatch(task -> task.getId().equals(taskId) && task.getStatus() == DownloadStatus.CANCELLED)));
        } finally {
            release.countDown();
            service.shutdown();
        }
    }

    @Test
    void retriesFailedHistoryTaskAsNewQueuedTask() throws Exception {
        SettingsManager settingsManager = createSettingsManager(tempDir.resolve("downloads"));
        DownloadHistoryStore historyStore = new DownloadHistoryStore(tempDir.resolve("download-history.json"), objectMapper);
        AtomicInteger attempts = new AtomicInteger();

        LocalCoverService localCoverService = createLocalCoverService();
        DownloadService service = new DownloadService(
                settingsManager,
                historyStore,
                localCoverService,
                request -> new DownloadService.ResolvedDownload(
                        request.getTitle(),
                        request.getPageUrl(),
                        request.getDownloadUrl(),
                        request.getThumbnail(),
                        request.getTitle() + ".mp4"
                ),
                (resolvedDownload, targetFile, progressConsumer, control) -> {
                    int currentAttempt = attempts.incrementAndGet();
                    if (currentAttempt == 1) {
                        throw new IllegalStateException("首次失败");
                    }
                    Files.writeString(targetFile, resolvedDownload.title());
                    progressConsumer.accept(new DownloadProgress(1, 1));
                }
        );

        try {
            DownloadBatchRequest request = new DownloadBatchRequest();
            request.setItems(List.of(item("失败后重试", null, "https://media.example.com/retry.mp4")));
            service.enqueue(request);

            assertTrue(waitUntil(() -> service.getSnapshot().historyTasks().stream()
                    .anyMatch(task -> "失败后重试".equals(task.getTitle()) && task.getStatus() == DownloadStatus.FAILED)));

            String failedTaskId = service.getSnapshot().historyTasks().get(0).getId();
            service.retryTask(failedTaskId);
            assertTrue(waitUntil(() -> service.getSnapshot().historyTasks().stream()
                    .anyMatch(task -> "失败后重试".equals(task.getTitle()) && task.getStatus() == DownloadStatus.COMPLETED)));
            assertEquals(2, attempts.get());
        } finally {
            service.shutdown();
        }
    }

    private LocalCoverService createLocalCoverService() {
        return new LocalCoverService(tempDir.resolve("covers"), null, null);
    }

    private DownloadService.ResolvedDownload resolved(DownloadRequestItem request) {
        return new DownloadService.ResolvedDownload(
                request.getTitle(),
                request.getPageUrl(),
                request.getDownloadUrl(),
                request.getThumbnail(),
                request.getTitle() + ".mp4"
        );
    }

    private SettingsManager createSettingsManager(Path downloadDirectory) {
        SettingsManager settingsManager = new SettingsManager(
                tempDir.resolve("settings.json"),
                tempDir.resolve("config.json"),
                objectMapper
        );
        AppSettings settings = new AppSettings();
        settings.setDownloadDirectory(downloadDirectory.toString());
        settingsManager.saveSettings(settings);
        return settingsManager;
    }

    private DownloadRequestItem item(String title, String pageUrl, String downloadUrl) {
        DownloadRequestItem item = new DownloadRequestItem();
        item.setTitle(title);
        item.setPageUrl(pageUrl);
        item.setDownloadUrl(downloadUrl);
        item.setThumbnail("");
        return item;
    }

    private boolean waitUntil(Check check) throws InterruptedException {
        long deadline = System.currentTimeMillis() + 5000;
        while (System.currentTimeMillis() < deadline) {
            if (check.matches()) {
                return true;
            }
            Thread.sleep(50);
        }
        return false;
    }

    @FunctionalInterface
    private interface Check {
        boolean matches();
    }
}
