package com.wangver.hanime.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.wangver.hanime.model.AppSettings;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SettingsManagerTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @TempDir
    Path tempDir;

    @Test
    void prefersSettingsJsonAndPersistsUpdates() throws Exception {
        Path settingsFile = tempDir.resolve("settings.json");
        Path legacyFile = tempDir.resolve("config.json");
        Files.writeString(settingsFile, "{\"downloadDirectory\":\"D:/Media/Hanime\"}");

        SettingsManager manager = new SettingsManager(settingsFile, legacyFile, objectMapper);
        manager.init();

        assertEquals("D:/Media/Hanime", manager.getSettings().getDownloadDirectory());

        AppSettings updated = new AppSettings();
        updated.setDownloadDirectory("E:/Archive/Hanime");
        manager.saveSettings(updated);

        AppSettings persisted = objectMapper.readValue(settingsFile.toFile(), AppSettings.class);
        assertEquals("E:/Archive/Hanime", persisted.getDownloadDirectory());
    }

    @Test
    void migratesLegacyConfigWhenSettingsFileIsMissing() throws Exception {
        Path settingsFile = tempDir.resolve("settings.json");
        Path legacyFile = tempDir.resolve("config.json");
        Files.writeString(legacyFile, "{\"downloadDirectory\":\"F:/Legacy/Hanime\"}");

        SettingsManager manager = new SettingsManager(settingsFile, legacyFile, objectMapper);
        manager.init();

        assertEquals("F:/Legacy/Hanime", manager.getSettings().getDownloadDirectory());
        assertTrue(Files.exists(settingsFile));

        AppSettings migrated = objectMapper.readValue(settingsFile.toFile(), AppSettings.class);
        assertEquals("F:/Legacy/Hanime", migrated.getDownloadDirectory());
    }

    @Test
    void defaultsParallelDownloadsToThreeAndPersistsUpdates() throws Exception {
        Path settingsFile = tempDir.resolve("settings.json");
        Path legacyFile = tempDir.resolve("config.json");

        SettingsManager manager = new SettingsManager(settingsFile, legacyFile, objectMapper);
        manager.init();

        assertEquals(3, manager.getSettings().getMaxConcurrentDownloads());

        AppSettings updated = manager.getSettings();
        updated.setMaxConcurrentDownloads(5);
        manager.saveSettings(updated);

        AppSettings persisted = objectMapper.readValue(settingsFile.toFile(), AppSettings.class);
        assertEquals(5, persisted.getMaxConcurrentDownloads());
    }
}
