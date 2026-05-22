from pathlib import Path

from app.paths import app_home
from app.settings import AppSettings, SettingsStore


def test_settings_defaults_and_clamps_values(tmp_path: Path):
    settings = AppSettings(maxConcurrentDownloads=99, gopeedConnections=999, gopeedPort=70000, browserChannel="firefox", pageCacheLimit=999)

    assert settings.maxConcurrentDownloads == 12
    assert settings.gopeedConnections == 128
    assert settings.gopeedPort == 9999
    assert settings.browserChannel == "msedge"
    assert settings.pageCacheLimit == 200


def test_settings_store_persists_json(tmp_path: Path):
    store = SettingsStore(tmp_path)
    settings = store.load()
    settings.downloadDirectory = str(tmp_path / "downloads")
    settings.maxConcurrentDownloads = 5
    settings.browserChannel = "chrome"
    settings.pageCacheLimit = 33

    store.save(settings)
    loaded = SettingsStore(tmp_path).load()

    assert loaded.downloadDirectory == str(tmp_path / "downloads")
    assert loaded.maxConcurrentDownloads == 5
    assert loaded.browserChannel == "chrome"
    assert loaded.pageCacheLimit == 33
    assert (tmp_path / "settings.json").exists()


def test_app_home_can_be_overridden_by_environment(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HANIME_APP_HOME", str(tmp_path / "isolated"))

    resolved = app_home()

    assert resolved == tmp_path / "isolated"
    assert resolved.exists()
