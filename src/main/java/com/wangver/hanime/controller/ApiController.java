package com.wangver.hanime.controller;

import com.wangver.hanime.service.HanimeParserService;
import com.wangver.hanime.service.HistoryCoverService;
import com.wangver.hanime.service.HttpSessionExpiredException;
import com.wangver.hanime.service.ImageProxyService;
import com.wangver.hanime.service.LocalCoverService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import com.wangver.hanime.model.AppSettings;
import com.wangver.hanime.service.SettingsManager;
import com.wangver.hanime.service.HanimeBrowseService;
import com.wangver.hanime.service.DownloadService;

import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class ApiController {

    @Autowired
    private HanimeParserService parserService;

    @Autowired
    private SettingsManager settingsManager;

    @Autowired
    private HanimeBrowseService browseService;

    @Autowired
    private com.wangver.hanime.service.PlaywrightBrowserService playwrightService;

    @Autowired
    private DownloadService downloadService;

    @Autowired
    private ImageProxyService imageProxyService;

    @Autowired
    private HistoryCoverService historyCoverService;

    @Autowired
    private LocalCoverService localCoverService;

    @PostMapping("/parse")
    public ResponseEntity<?> parseVideo(@RequestBody Map<String, String> payload) {
        String url = payload.get("url");
        if (url == null || url.isEmpty()) {
            return ResponseEntity.badRequest().body("缺少视频链接");
        }

        try {
            Map<String, Object> result = parserService.parse(url);
            return ResponseEntity.ok(result);
        } catch (HttpSessionExpiredException e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(e.getMessage());
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("解析错误: " + e.getMessage());
        }
    }

    @GetMapping("/settings")
    public ResponseEntity<AppSettings> getSettings() {
        return ResponseEntity.ok(settingsManager.getSettings());
    }

    @PostMapping("/settings")
    public ResponseEntity<String> updateSettings(@RequestBody AppSettings settings) {
        if (settings.getDownloadDirectory() == null || settings.getDownloadDirectory().isEmpty()) {
            return ResponseEntity.badRequest().body("目录不能为空");
        }
        settingsManager.saveSettings(settings);
        return ResponseEntity.ok("Settings saved successfully.");
    }

    @PostMapping("/settings/clear-cache")
    public ResponseEntity<?> clearCache() {
        try {
            playwrightService.forceCloseAndClearCache();
            return ResponseEntity.ok(downloadService.clearHistory());
        } catch (Exception e) {
            return ResponseEntity.status(500).body("Error: " + e.getMessage());
        }
    }

    @GetMapping("/browse")
    public ResponseEntity<?> browseCategory(
            @RequestParam String category,
            @RequestParam(defaultValue = "1") int page) {
        if (category == null || category.trim().isEmpty()) {
            return ResponseEntity.badRequest().body("缺少分类参数");
        }
        try {
            return ResponseEntity.ok(browseService.fetchCategory(category, page));
        } catch (HttpSessionExpiredException e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(e.getMessage());
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("获取分类失败: " + e.getMessage());
        }
    }

    @GetMapping("/search")
    public ResponseEntity<?> search(
            @RequestParam(required = false, defaultValue = "") String query,
            @RequestParam(required = false, defaultValue = "") String type,
            @RequestParam(required = false, defaultValue = "") String genre,
            @RequestParam(name = "tags[]", required = false) List<String> tags,
            @RequestParam(required = false, defaultValue = "") String sort,
            @RequestParam(required = false, defaultValue = "") String date,
            @RequestParam(required = false, defaultValue = "") String duration,
            @RequestParam(defaultValue = "1") int page) {
        try {
            return ResponseEntity.ok(browseService.fetchSearch(
                    query,
                    type,
                    genre,
                    tags == null ? List.of() : tags,
                    sort,
                    date,
                    duration,
                    page
            ));
        } catch (HttpSessionExpiredException e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(e.getMessage());
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("搜索失败: " + e.getMessage());
        }
    }

    @GetMapping("/search/options")
    public ResponseEntity<?> searchOptions() {
        return ResponseEntity.ok(browseService.fetchSearchOptions());
    }

    /**
     * 图片防盗链代理，避免前端直接 img src 报 403 Forbidden
     */
    @GetMapping("/proxy/image")
    public ResponseEntity<StreamingResponseBody> proxyImage(@RequestParam String url) {
        try {
            ImageProxyService.ImageResponse image = imageProxyService.fetchImage(url);

            StreamingResponseBody responseBody = outputStream -> {
                outputStream.write(image.bytes());
            };

            HttpHeaders headers = new HttpHeaders();
            headers.add(HttpHeaders.CONTENT_TYPE, image.contentType() != null ? image.contentType() : "image/jpeg");

            return new ResponseEntity<>(responseBody, headers, HttpStatus.OK);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/proxy/history-cover")
    public ResponseEntity<StreamingResponseBody> proxyHistoryCover(
            @RequestParam String url,
            @RequestParam(required = false) String thumbnail) {
        try {
            ImageProxyService.ImageResponse image = historyCoverService.fetchCover(url, thumbnail);

            StreamingResponseBody responseBody = outputStream -> {
                outputStream.write(image.bytes());
            };

            HttpHeaders headers = new HttpHeaders();
            headers.add(HttpHeaders.CONTENT_TYPE, image.contentType() != null ? image.contentType() : "image/jpeg");
            headers.add(HttpHeaders.CACHE_CONTROL, "public, max-age=86400");

            return new ResponseEntity<>(responseBody, headers, HttpStatus.OK);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/local-cover/{taskId}")
    public ResponseEntity<byte[]> localCover(@PathVariable String taskId) {
        try {
            java.nio.file.Path cached = localCoverService.getCoverPath(taskId);
            if (cached != null) {
                byte[] bytes = java.nio.file.Files.readAllBytes(cached);
                HttpHeaders headers = new HttpHeaders();
                headers.add(HttpHeaders.CONTENT_TYPE, "image/jpeg");
                headers.add(HttpHeaders.CACHE_CONTROL, "public, max-age=86400");
                return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
            }

            byte[] bytes = localCoverService.getOrFetch(taskId, null, null);
            HttpHeaders headers = new HttpHeaders();
            headers.add(HttpHeaders.CONTENT_TYPE, "image/jpeg");
            headers.add(HttpHeaders.CACHE_CONTROL, "public, max-age=86400");
            return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 视频流代理，支持 HTTP Range (206) 以便前端视频播放器可以拖动进度条
     */
    @GetMapping("/proxy/video")
    public ResponseEntity<StreamingResponseBody> proxyVideo(
            @RequestParam String url,
            @RequestHeader(value = "Range", required = false) String rangeHeader) {
        try {
            HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
            connection.setRequestMethod("GET");
            connection.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)");
            connection.setRequestProperty("Referer", "https://hanime1.me/");
            
            // 关键：转发前端播放器的 Range 请求头到目标服务器
            if (rangeHeader != null) {
                connection.setRequestProperty("Range", rangeHeader);
            }

            int responseCode = connection.getResponseCode();
            String contentType = connection.getContentType();
            long contentLength = connection.getContentLengthLong();

            HttpHeaders headers = new HttpHeaders();
            headers.add(HttpHeaders.CONTENT_TYPE, contentType != null ? contentType : "video/mp4");
            
            // 如果目标服务器支持 Range 并返回了 206
            if (responseCode == HttpStatus.PARTIAL_CONTENT.value()) {
                String contentRange = connection.getHeaderField("Content-Range");
                if (contentRange != null) headers.add("Content-Range", contentRange);
            }

            StreamingResponseBody responseBody = outputStream -> {
                try (InputStream is = connection.getInputStream()) {
                    byte[] buffer = new byte[1024 * 64]; // 64K buffer for video
                    int bytesRead;
                    while ((bytesRead = is.read(buffer)) != -1) {
                        outputStream.write(buffer, 0, bytesRead);
                    }
                } catch (Exception e) {
                    // Client disconnected
                }
            };

            return new ResponseEntity<>(responseBody, headers, HttpStatus.valueOf(responseCode));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
