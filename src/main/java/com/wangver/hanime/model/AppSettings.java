package com.wangver.hanime.model;

public class AppSettings {
    public static final int DEFAULT_MAX_CONCURRENT_DOWNLOADS = 3;
    public static final int MIN_MAX_CONCURRENT_DOWNLOADS = 1;
    public static final int MAX_MAX_CONCURRENT_DOWNLOADS = 12;

    private String downloadDirectory;
    private int maxConcurrentDownloads;

    public AppSettings() {
        // Default download directory: "Downloads" folder in user's home path
        this.downloadDirectory = System.getProperty("user.home") + "/Downloads/Hanime";
        this.maxConcurrentDownloads = DEFAULT_MAX_CONCURRENT_DOWNLOADS;
    }

    public String getDownloadDirectory() {
        return downloadDirectory;
    }

    public void setDownloadDirectory(String downloadDirectory) {
        this.downloadDirectory = downloadDirectory;
    }

    public int getMaxConcurrentDownloads() {
        if (maxConcurrentDownloads < MIN_MAX_CONCURRENT_DOWNLOADS) {
            return DEFAULT_MAX_CONCURRENT_DOWNLOADS;
        }
        return Math.min(maxConcurrentDownloads, MAX_MAX_CONCURRENT_DOWNLOADS);
    }

    public void setMaxConcurrentDownloads(int maxConcurrentDownloads) {
        if (maxConcurrentDownloads < MIN_MAX_CONCURRENT_DOWNLOADS) {
            this.maxConcurrentDownloads = DEFAULT_MAX_CONCURRENT_DOWNLOADS;
            return;
        }
        this.maxConcurrentDownloads = Math.min(maxConcurrentDownloads, MAX_MAX_CONCURRENT_DOWNLOADS);
    }
}
