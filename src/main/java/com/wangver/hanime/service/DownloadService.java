package com.wangver.hanime.service;

import com.wangver.hanime.model.DownloadBatchRequest;
import com.wangver.hanime.model.DownloadProgress;
import com.wangver.hanime.model.DownloadRequestItem;
import com.wangver.hanime.model.DownloadSnapshot;
import com.wangver.hanime.model.DownloadStatus;
import com.wangver.hanime.model.DownloadTaskView;
import jakarta.annotation.PreDestroy;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Consumer;

@Service
public class DownloadService {

    private static final int DEFAULT_PARALLELISM = 8;
    private static final int MAX_DOWNLOAD_WORKERS = 12;
    private static final int MAX_HISTORY_SIZE = 50;
    private static final int MAX_RETRIES = 3;
    private static final int PROGRESS_TIMEOUT_SECONDS = 30;

    private final SettingsManager settingsManager;
    private final DownloadHistoryStore historyStore;
    private final LocalCoverService localCoverService;
    private final DownloadResolver downloadResolver;
    private final DownloadExecutor downloadExecutor;
    private final BlockingQueue<DownloadTaskState> queue = new LinkedBlockingQueue<>();
    private final Map<String, DownloadTaskState> tasks = new ConcurrentHashMap<>();
    private final Set<String> activeTaskIds = ConcurrentHashMap.newKeySet();
    private final CopyOnWriteArrayList<SseEmitter> emitters = new CopyOnWriteArrayList<>();
    private final List<DownloadTaskView> history = new CopyOnWriteArrayList<>();
    private final ExecutorService scheduler = Executors.newSingleThreadExecutor();
    private final ExecutorService downloadWorkers = Executors.newFixedThreadPool(MAX_DOWNLOAD_WORKERS);
    private final ScheduledExecutorService timeoutWatchdog = Executors.newSingleThreadScheduledExecutor();
    private final Object schedulerMonitor = new Object();
    private final AtomicLong sequence = new AtomicLong();

    private volatile boolean running = true;

    @Autowired
    public DownloadService(
            SettingsManager settingsManager,
            DownloadHistoryStore historyStore,
            HanimeParserService parserService,
            LocalCoverService localCoverService
    ) {
        this(
                settingsManager,
                historyStore,
                localCoverService,
                request -> resolveWithParser(request, parserService),
                createDefaultExecutor()
        );
    }

    DownloadService(
            SettingsManager settingsManager,
            DownloadHistoryStore historyStore,
            LocalCoverService localCoverService,
            DownloadResolver downloadResolver,
            DownloadExecutor downloadExecutor
    ) {
        this.settingsManager = settingsManager;
        this.historyStore = historyStore;
        this.localCoverService = localCoverService;
        this.downloadResolver = downloadResolver;
        this.downloadExecutor = downloadExecutor;
        this.history.addAll(historyStore.load());
        deduplicateHistory();
        this.scheduler.submit(this::runLoop);
    }

    public DownloadSnapshot enqueue(DownloadBatchRequest request) {
        if (request == null || request.getItems() == null || request.getItems().isEmpty()) {
            throw new IllegalArgumentException("至少需要一个下载任务");
        }

        int added = 0;
        for (DownloadRequestItem item : request.getItems()) {
            if (isAlreadyDownloaded(item.getPageUrl())) {
                continue;
            }
            DownloadTaskState state = new DownloadTaskState(item, sequence.incrementAndGet());
            tasks.put(state.id, state);
            queue.offer(state);
            added++;
        }

        if (added > 0) {
            signalScheduler();
            broadcastSnapshot();
        }
        return getSnapshot();
    }

    private boolean isAlreadyDownloaded(String pageUrl) {
        if (pageUrl == null || pageUrl.isBlank()) return false;

        for (DownloadTaskState task : tasks.values()) {
            String taskUrl = task.request != null ? task.request.getPageUrl() : null;
            if (pageUrl.equals(taskUrl)
                    && task.status != DownloadStatus.CANCELLED
                    && task.status != DownloadStatus.FAILED) {
                return true;
            }
        }

        for (DownloadTaskView h : history) {
            if (pageUrl.equals(h.getPageUrl()) && h.getStatus() == DownloadStatus.COMPLETED) {
                return true;
            }
        }

        return false;
    }

    public synchronized DownloadSnapshot getSnapshot() {
        deduplicateHistory();
        List<DownloadTaskView> activeTasks = tasks.values().stream()
                .filter(task -> activeTaskIds.contains(task.id))
                .sorted(Comparator.comparingLong(task -> task.sequence))
                .map(DownloadTaskState::toView)
                .toList();

        List<DownloadTaskView> queuedTasks = tasks.values().stream()
                .filter(task -> !activeTaskIds.contains(task.id))
                .sorted(Comparator.comparingLong(task -> task.sequence))
                .map(DownloadTaskState::toView)
                .toList();

        return new DownloadSnapshot(activeTasks, queuedTasks, List.copyOf(history));
    }

    public DownloadSnapshot pauseTask(String taskId) {
        DownloadTaskState state = requireTask(taskId);
        state.control.pause();
        if (activeTaskIds.contains(taskId)) {
            state.status = DownloadStatus.PAUSED;
        } else if (state.status == DownloadStatus.QUEUED) {
            state.status = DownloadStatus.PAUSED;
        }
        broadcastSnapshot();
        return getSnapshot();
    }

    public DownloadSnapshot resumeTask(String taskId) {
        DownloadTaskState state = requireTask(taskId);
        state.control.resume();
        if (activeTaskIds.contains(taskId)) {
            state.status = DownloadStatus.DOWNLOADING;
        } else if (state.status == DownloadStatus.PAUSED) {
            state.status = DownloadStatus.QUEUED;
        }
        signalScheduler();
        broadcastSnapshot();
        return getSnapshot();
    }

    public synchronized DownloadSnapshot cancelTask(String taskId) {
        DownloadTaskState state = requireTask(taskId);
        // 强制从队列移除
        queue.remove(state);
        state.status = DownloadStatus.CANCELLED;
        state.finishedAt = now();
        activeTaskIds.remove(taskId);
        // 清理部分下载的文件
        if (state.filePath != null) {
            try {
                Files.deleteIfExists(Path.of(state.filePath));
            } catch (IOException ignored) {
            }
        }
        state.filePath = null;
        // 立即放入历史记录（不等待下载线程响应）
        addHistory(state.toView());
        historyStore.save(history);
        tasks.remove(taskId);
        // 通知下载线程停止
        state.control.cancel();
        signalScheduler();
        broadcastSnapshot();
        return getSnapshot();
    }

    public synchronized DownloadSnapshot pauseAll() {
        for (DownloadTaskState state : tasks.values()) {
            state.control.pause();
            if (activeTaskIds.contains(state.id) || state.status == DownloadStatus.QUEUED) {
                state.status = DownloadStatus.PAUSED;
            }
        }
        broadcastSnapshot();
        return getSnapshot();
    }

    public synchronized DownloadSnapshot cancelAll() {
        List<DownloadTaskState> allTasks = new ArrayList<>(tasks.values());
        for (DownloadTaskState state : allTasks) {
            queue.remove(state);
            state.status = DownloadStatus.CANCELLED;
            state.finishedAt = now();
            activeTaskIds.remove(state.id);
            if (state.filePath != null) {
                try {
                    Files.deleteIfExists(Path.of(state.filePath));
                } catch (IOException ignored) {}
            }
            state.filePath = null;
            addHistory(state.toView());
            tasks.remove(state.id);
            state.control.cancel();
        }
        historyStore.save(history);
        signalScheduler();
        broadcastSnapshot();
        return getSnapshot();
    }

    public DownloadSnapshot retryTask(String taskId) {
        DownloadTaskView task = history.stream()
                .filter(item -> item.getId().equals(taskId))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("未找到可重试的历史任务"));

        if (task.getStatus() == DownloadStatus.COMPLETED) {
            throw new IllegalStateException("已完成的任务不能重试");
        }

        DownloadRequestItem requestItem = new DownloadRequestItem();
        requestItem.setTitle(task.getTitle());
        requestItem.setPageUrl(task.getPageUrl());
        requestItem.setDownloadUrl(task.getDownloadUrl());
        requestItem.setThumbnail(task.getThumbnail());

        history.remove(task);
        historyStore.save(history);
        DownloadBatchRequest request = new DownloadBatchRequest();
        request.setItems(List.of(requestItem));
        return enqueue(request);
    }


    public synchronized DownloadSnapshot retryAllFailed() {
        List<DownloadTaskView> failedTasks = history.stream()
                .filter(item -> item.getStatus() != DownloadStatus.COMPLETED)
                .toList();

        if (failedTasks.isEmpty()) {
            throw new IllegalStateException("没有可重试的任务");
        }

        history.removeAll(failedTasks);
        historyStore.save(history);

        List<DownloadRequestItem> items = failedTasks.stream()
                .map(task -> {
                    DownloadRequestItem requestItem = new DownloadRequestItem();
                    requestItem.setTitle(task.getTitle());
                    requestItem.setPageUrl(task.getPageUrl());
                    requestItem.setDownloadUrl(task.getDownloadUrl());
                    requestItem.setThumbnail(task.getThumbnail());
                    return requestItem;
                })
                .toList();

        DownloadBatchRequest request = new DownloadBatchRequest();
        request.setItems(items);
        return enqueue(request);
    }

    public DownloadSnapshot clearHistory() {
        history.clear();
        historyStore.save(history);
        broadcastSnapshot();
        return getSnapshot();
    }

    public SseEmitter subscribe() {
        SseEmitter emitter = new SseEmitter(0L);
        emitters.add(emitter);
        emitter.onCompletion(() -> emitters.remove(emitter));
        emitter.onTimeout(() -> emitters.remove(emitter));
        sendSnapshot(emitter, getSnapshot());
        return emitter;
    }

    public void shutdown() {
        running = false;
        signalScheduler();
        scheduler.shutdownNow();
        downloadWorkers.shutdownNow();
        timeoutWatchdog.shutdownNow();
        try {
            scheduler.awaitTermination(5, TimeUnit.SECONDS);
            downloadWorkers.awaitTermination(5, TimeUnit.SECONDS);
        } catch (InterruptedException interruptedException) {
            Thread.currentThread().interrupt();
        }
        emitters.forEach(SseEmitter::complete);
        emitters.clear();
    }

    @PreDestroy
    public void close() {
        shutdown();
    }

    private void runLoop() {
        while (running) {
            try {
                launchAvailableTasks();
                synchronized (schedulerMonitor) {
                    schedulerMonitor.wait(250);
                }
            } catch (InterruptedException interruptedException) {
                Thread.currentThread().interrupt();
                return;
            }
        }
    }

    private void launchAvailableTasks() {
        int limit = settingsManager.getSettings().getMaxConcurrentDownloads();
        while (running && activeTaskIds.size() < limit) {
            DownloadTaskState state = pollNextStartableTask();
            if (state == null) {
                return;
            }
            activeTaskIds.add(state.id);
            downloadWorkers.submit(() -> process(state));
        }
    }

    private DownloadTaskState pollNextStartableTask() {
        for (DownloadTaskState state : queue) {
            if (state.control.isCancelled()) {
                queue.remove(state);
                continue;
            }
            if (state.control.isPaused() || state.status == DownloadStatus.PAUSED) {
                continue;
            }
            if (queue.remove(state)) {
                return state;
            }
        }
        return null;
    }

    private void process(DownloadTaskState state) {
        boolean cleanup = true;
        try {
            if (state.control.isPaused()) {
                state.status = DownloadStatus.PAUSED;
                broadcastSnapshot();
                state.control.awaitIfPaused();
            }
            state.status = DownloadStatus.PREPARING;
            state.startedAt = now();
            broadcastSnapshot();

            state.control.throwIfCancelled();
            ResolvedDownload resolvedDownload = resolve(state.request);
            state.control.awaitIfPaused();
            state.control.throwIfCancelled();
            state.title = resolvedDownload.title();
            state.pageUrl = resolvedDownload.pageUrl();
            state.downloadUrl = resolvedDownload.downloadUrl();
            state.thumbnail = resolvedDownload.thumbnail();
            state.fileName = resolvedDownload.fileName();

            localCoverService.save(state.id, state.thumbnail);

            Path targetFile = Path.of(settingsManager.getSettings().getDownloadDirectory()).resolve(resolvedDownload.fileName());
            Path parent = targetFile.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            state.filePath = targetFile.toString();

            // 检查文件是否已存在，存在则跳过下载直接完成
            boolean fileAlreadyExists = Files.exists(targetFile) && Files.size(targetFile) > 0;
            if (fileAlreadyExists) {
                state.status = DownloadStatus.COMPLETED;
                state.totalAmount = Files.size(targetFile);
                state.completedAmount = Files.size(targetFile);
                state.progressPercent = 100;
            } else {
                state.status = DownloadStatus.DOWNLOADING;
            broadcastSnapshot();

            // 进度超时检测（30秒无进度则判定为下载失败）
            state.timedOut = false;
            final java.util.concurrent.ScheduledFuture<?>[] watchdog = new java.util.concurrent.ScheduledFuture<?>[1];
            Runnable resetWatchdog = () -> {
                if (watchdog[0] != null && !watchdog[0].isDone()) {
                    watchdog[0].cancel(false);
                }
                watchdog[0] = timeoutWatchdog.schedule(() -> {
                    if (!state.control.isCancelled()) {
                        state.timedOut = true;
                        state.control.cancel();
                    }
                }, PROGRESS_TIMEOUT_SECONDS, TimeUnit.SECONDS);
            };
            resetWatchdog.run();

            downloadExecutor.download(resolvedDownload, targetFile, progress -> {
                updateProgress(state, progress);
                resetWatchdog.run();
            }, state.control);

            if (watchdog[0] != null) watchdog[0].cancel(false);
            }
            state.control.throwIfCancelled();
            state.status = DownloadStatus.COMPLETED;
            state.progressPercent = 100.0;
            state.finishedAt = now();
        } catch (DownloadCancelledException exception) {
            if (state.timedOut) {
                if (state.retryCount < MAX_RETRIES) {
                    cleanup = false;
                    state.retryCount++;
                    state.status = DownloadStatus.QUEUED;
                    state.errorMessage = "下载超时: 30秒内无进度，第" + state.retryCount + "次重试";
                    if (state.filePath != null) {
                        try { Files.deleteIfExists(Path.of(state.filePath)); } catch (IOException ignored) {}
                        state.filePath = null;
                    }
                    queue.add(state);
                    signalScheduler();
                    broadcastSnapshot();
                    return;
                } else {
                    state.status = DownloadStatus.FAILED;
                    state.errorMessage = "已重试" + MAX_RETRIES + "次，下载超时: 30秒内无进度";
                }
            } else {
                state.status = DownloadStatus.CANCELLED;
                state.errorMessage = "任务已取消";
            }
            state.finishedAt = now();
        } catch (Exception exception) {
            if (state.control.isCancelled()) {
                if (state.timedOut) {
                    if (state.retryCount < MAX_RETRIES) {
                        cleanup = false;
                        state.retryCount++;
                        state.status = DownloadStatus.QUEUED;
                        state.errorMessage = "下载超时: 30秒内无进度，第" + state.retryCount + "次重试";
                        if (state.filePath != null) {
                            try { Files.deleteIfExists(Path.of(state.filePath)); } catch (IOException ignored) {}
                            state.filePath = null;
                        }
                        queue.add(state);
                        signalScheduler();
                        broadcastSnapshot();
                        return;
                    } else {
                        state.status = DownloadStatus.FAILED;
                        state.errorMessage = "已重试" + MAX_RETRIES + "次，下载超时: 30秒内无进度";
                    }
                } else {
                state.status = DownloadStatus.CANCELLED;
                state.errorMessage = exception.getMessage();
                }
            } else {
                if (state.retryCount < MAX_RETRIES) {
                    cleanup = false;
                    state.retryCount++;
                    state.status = DownloadStatus.QUEUED;
                    state.errorMessage = "下载失败，第" + state.retryCount + "次重试中: " + exception.getMessage();
                    // 清除上次失败留下的部分文件，重试时重新下载
                    if (state.filePath != null) {
                        try {
                            Files.deleteIfExists(Path.of(state.filePath));
                        } catch (IOException ignored) {
                        }
                        state.filePath = null;
                    }
                    queue.add(state);
                    signalScheduler();
                    broadcastSnapshot();
                    return;
                } else {
                    state.status = DownloadStatus.FAILED;
                    state.errorMessage = "已重试" + MAX_RETRIES + "次，下载失败: " + exception.getMessage();
                }
            }
            state.finishedAt = now();
        } finally {
            // 如果任务已被外部取消并添加到历史（cancelTask强制剔除），跳过二次清理
            boolean alreadyInHistory = history.stream().anyMatch(h -> h.getId().equals(state.id));
            if (cleanup && !alreadyInHistory) {
            synchronized (this) {
                addHistory(state.toView());
                historyStore.save(history);
                tasks.remove(state.id);
                activeTaskIds.remove(state.id);
            }
            if (alreadyInHistory) {
                activeTaskIds.remove(state.id);
                tasks.remove(state.id);
            }
            signalScheduler();
            broadcastSnapshot();
            }
        }
    }

    private void updateProgress(DownloadTaskState state, DownloadProgress progress) {
        if (state.control.isCancelled()) {
            throw new DownloadCancelledException();
        }
        if (state.control.isPaused()) {
            state.status = DownloadStatus.PAUSED;
        } else {
            state.status = DownloadStatus.DOWNLOADING;
        }
        state.completedAmount = progress.completedAmount();
        state.totalAmount = progress.totalAmount();
        state.progressPercent = progress.percent();
        broadcastSnapshot();
    }

    private DownloadTaskState requireTask(String taskId) {
        DownloadTaskState state = tasks.get(taskId);
        if (state == null) {
            throw new IllegalArgumentException("任务不存在或已结束");
        }
        return state;
    }

    private void signalScheduler() {
        synchronized (schedulerMonitor) {
            schedulerMonitor.notifyAll();
        }
    }

    private ResolvedDownload resolve(DownloadRequestItem request) throws Exception {
        if (hasText(request.getDownloadUrl())) {
            return new ResolvedDownload(
                    firstText(request.getTitle(), buildTitleFromUrl(request.getDownloadUrl())),
                    request.getPageUrl(),
                    request.getDownloadUrl(),
                    request.getThumbnail(),
                    buildFileName(firstText(request.getTitle(), "video"), request.getDownloadUrl())
            );
        }
        return downloadResolver.resolve(request);
    }

    private void addHistory(DownloadTaskView view) {
        // 检查文件是否实际存在于磁盘
        boolean fileExistsOnDisk = false;
        String filePath = view.getFilePath();
        if (filePath != null && !filePath.isEmpty()) {
            Path path = Path.of(filePath);
            try {
                fileExistsOnDisk = Files.exists(path) && Files.size(path) > 0;
            } catch (IOException e) {
                fileExistsOnDisk = false;
            }
        }
        // 如果文件存在，标记为已完成（即使是 FAILED/CANCELLED 也覆盖）
        if (fileExistsOnDisk && view.getStatus() != DownloadStatus.COMPLETED) {
            DownloadTaskView corrected = new DownloadTaskView(
                    view.getId(), view.getTitle(), view.getPageUrl(), view.getDownloadUrl(),
                    view.getThumbnail(), view.getFileName(), view.getFilePath(),
                    DownloadStatus.COMPLETED, 100.0,
                    view.getCompletedAmount(), view.getTotalAmount(),
                    null, view.getCreatedAt(), view.getStartedAt(), view.getFinishedAt()
            );
            view = corrected;
        }
        // 去重：同一标题只留一条。文件存在则保留，否则保留失败的
        boolean fileExists = fileExistsOnDisk;
        String currentTitle = view.getTitle();
        history.removeIf(existing -> {
            if (!existing.getTitle().equals(currentTitle)) return false;
            if (fileExists) return true; // 文件存在的条目替代旧的
            return existing.getStatus() == DownloadStatus.FAILED; // 无文件时保留失败的
        });
        history.add(0, view);
        while (history.size() > MAX_HISTORY_SIZE) {
            history.remove(history.size() - 1);
        }
    }

    private synchronized void deduplicateHistory() {
        Map<String, List<DownloadTaskView>> grouped = new java.util.HashMap<>();
        for (DownloadTaskView item : history) {
            grouped.computeIfAbsent(item.getTitle(), k -> new ArrayList<>()).add(item);
        }

        boolean changed = false;
        List<DownloadTaskView> deduped = new ArrayList<>();
        for (List<DownloadTaskView> group : grouped.values()) {
            if (group.size() == 1) {
                deduped.add(group.get(0));
                continue;
            }
            changed = true;
            DownloadTaskView best = null;
            boolean bestHasFile = false;
            for (DownloadTaskView item : group) {
                String fp = item.getFilePath();
                boolean thisHasFile = fp != null && !fp.isEmpty();
                if (thisHasFile) {
                    try {
                        thisHasFile = Files.exists(Path.of(fp)) && Files.size(Path.of(fp)) > 0;
                    } catch (IOException e) {
                        thisHasFile = false;
                    }
                }
                if (thisHasFile) {
                    // 文件实际存在，优先保留 COMPLETED
                    if (!bestHasFile || item.getStatus() == DownloadStatus.COMPLETED) {
                        best = item;
                        bestHasFile = true;
                    }
                } else if (!bestHasFile) {
                    // 无文件时优先保留失败的（显示错误信息）
                    if (best == null || item.getStatus() == DownloadStatus.FAILED) {
                        best = item;
                    }
                }
            }
            if (best != null) deduped.add(best);
        }
        if (changed) {
            history.clear();
            history.addAll(deduped);
            historyStore.save(history);
        }
    }

    private void broadcastSnapshot() {
        DownloadSnapshot snapshot = getSnapshot();
        for (SseEmitter emitter : emitters) {
            sendSnapshot(emitter, snapshot);
        }
    }

    private void sendSnapshot(SseEmitter emitter, DownloadSnapshot snapshot) {
        try {
            emitter.send(SseEmitter.event().name("snapshot").data(snapshot));
        } catch (IOException exception) {
            emitters.remove(emitter);
            emitter.completeWithError(exception);
        }
    }

    private String now() {
        return Instant.now().toString();
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    private String firstText(String preferred, String fallback) {
        return hasText(preferred) ? preferred : fallback;
    }

    private String buildTitleFromUrl(String downloadUrl) {
        try {
            String path = URI.create(downloadUrl).getPath();
            if (path == null || path.isBlank()) {
                return "video";
            }
            String fileName = path.substring(path.lastIndexOf('/') + 1);
            int dotIndex = fileName.lastIndexOf('.');
            return dotIndex > 0 ? fileName.substring(0, dotIndex) : fileName;
        } catch (Exception exception) {
            return "video";
        }
    }

    private static ResolvedDownload resolveWithParser(DownloadRequestItem request, HanimeParserService parserService) throws Exception {
        if (request.getPageUrl() == null || request.getPageUrl().isBlank()) {
            throw new IOException("缺少可解析的页面地址");
        }

        Map<String, Object> parsed = parserService.parse(request.getPageUrl());
        String title = parsed.getOrDefault("title", request.getTitle()) == null
                ? "video"
                : String.valueOf(parsed.getOrDefault("title", request.getTitle()));
        String downloadUrl = parsed.get("videoUrl") == null ? "" : String.valueOf(parsed.get("videoUrl"));
        if (downloadUrl.isBlank()) {
            throw new IOException("解析成功，但未找到可下载的视频源");
        }

        String thumbnail = parsed.get("thumbnail") == null ? request.getThumbnail() : String.valueOf(parsed.get("thumbnail"));
        return new ResolvedDownload(
                title,
                request.getPageUrl(),
                downloadUrl,
                thumbnail,
                buildFileName(title, downloadUrl)
        );
    }

    private static DownloadExecutor createDefaultExecutor() {
        HttpClient httpClient = HttpClient.newBuilder()
                .followRedirects(HttpClient.Redirect.NORMAL)
                .build();
        SegmentedFileDownloader segmentedFileDownloader = new SegmentedFileDownloader(httpClient);
        HlsDownloader hlsDownloader = new HlsDownloader(httpClient);

        return (resolvedDownload, targetFile, progressConsumer, control) -> {
            URI uri = URI.create(resolvedDownload.downloadUrl());
            if (resolvedDownload.downloadUrl().toLowerCase().contains(".m3u8")) {
                hlsDownloader.download(uri, targetFile, DEFAULT_PARALLELISM, progressConsumer, control);
            } else {
                segmentedFileDownloader.download(uri, targetFile, DEFAULT_PARALLELISM, progressConsumer, control);
            }
        };
    }

    static String buildFileName(String title, String downloadUrl) {
        String safeTitle = title == null || title.isBlank() ? "video" : title;
        safeTitle = safeTitle.replaceAll("[\\\\/:*?\"<>|]", "_").trim();
        if (safeTitle.isBlank()) {
            safeTitle = "video";
        }

        String lowerUrl = downloadUrl == null ? "" : downloadUrl.toLowerCase();
        String extension = lowerUrl.contains(".m3u8") ? ".ts" : ".mp4";
        int queryIndex = lowerUrl.indexOf('?');
        String pathPart = queryIndex >= 0 ? lowerUrl.substring(0, queryIndex) : lowerUrl;
        int dotIndex = pathPart.lastIndexOf('.');
        if (dotIndex >= 0 && dotIndex > pathPart.lastIndexOf('/')) {
            String candidate = pathPart.substring(dotIndex);
            if (candidate.length() <= 5 && !candidate.equals(".m3u8")) {
                extension = candidate;
            }
        }

        return safeTitle + extension;
    }

    @FunctionalInterface
    interface DownloadResolver {
        ResolvedDownload resolve(DownloadRequestItem request) throws Exception;
    }

    @FunctionalInterface
    interface DownloadExecutor {
        void download(
                ResolvedDownload resolvedDownload,
                Path targetFile,
                Consumer<DownloadProgress> progressConsumer,
                DownloadTaskControl control
        ) throws Exception;
    }

    interface DownloadTaskControl {
        void pause();

        void resume();

        void cancel();

        boolean isPaused();

        boolean isCancelled();

        void awaitIfPaused() throws InterruptedException;

        void throwIfCancelled();
    }

    public record ResolvedDownload(
            String title,
            String pageUrl,
            String downloadUrl,
            String thumbnail,
            String fileName
    ) {
    }

    private static class DownloadTaskState {

        private final String id = UUID.randomUUID().toString();
        private int retryCount = 0;
        private volatile boolean timedOut;
        private final DownloadRequestItem request;
        private final long sequence;
        private final String createdAt = Instant.now().toString();
        private final TaskControl control = new TaskControl();

        private String title;
        private String pageUrl;
        private String downloadUrl;
        private String thumbnail;
        private String fileName;
        private String filePath;
        private DownloadStatus status = DownloadStatus.QUEUED;
        private double progressPercent;
        private long completedAmount;
        private long totalAmount;
        private String errorMessage;
        private String startedAt;
        private String finishedAt;

        private DownloadTaskState(DownloadRequestItem request, long sequence) {
            this.request = request;
            this.sequence = sequence;
            this.title = request.getTitle();
            this.pageUrl = request.getPageUrl();
            this.downloadUrl = request.getDownloadUrl();
            this.thumbnail = request.getThumbnail();
        }

        private DownloadTaskView toView() {
            return new DownloadTaskView(
                    id,
                    title,
                    pageUrl,
                    downloadUrl,
                    thumbnail,
                    fileName,
                    filePath,
                    status,
                    progressPercent,
                    completedAmount,
                    totalAmount,
                    errorMessage,
                    createdAt,
                    startedAt,
                    finishedAt
            );
        }
    }

    private static class TaskControl implements DownloadTaskControl {

        private final Object monitor = new Object();
        private volatile boolean paused;
        private volatile boolean cancelled;

        @Override
        public void pause() {
            paused = true;
        }

        @Override
        public void resume() {
            synchronized (monitor) {
                paused = false;
                monitor.notifyAll();
            }
        }

        @Override
        public void cancel() {
            cancelled = true;
            synchronized (monitor) {
                paused = false;
                monitor.notifyAll();
            }
        }

        @Override
        public boolean isPaused() {
            return paused;
        }

        @Override
        public boolean isCancelled() {
            return cancelled;
        }

        @Override
        public void awaitIfPaused() throws InterruptedException {
            synchronized (monitor) {
                while (paused && !cancelled) {
                    monitor.wait(100);
                }
            }
            throwIfCancelled();
        }

        @Override
        public void throwIfCancelled() {
            if (cancelled) {
                throw new DownloadCancelledException();
            }
        }
    }

    private static class DownloadCancelledException extends RuntimeException {
    }
}