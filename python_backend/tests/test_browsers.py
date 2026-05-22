from fastapi.testclient import TestClient

from pathlib import Path

from app.browsers import BrowserChoice, detect_browsers, executable_exists
from app.main import create_app


def test_detect_browsers_marks_supported_channels(monkeypatch):
    monkeypatch.setattr("app.browsers.executable_exists", lambda name: name in {"msedge", "chrome"})

    choices = detect_browsers()

    assert BrowserChoice("msedge", "Microsoft Edge", True) in choices
    assert BrowserChoice("chrome", "Google Chrome", True) in choices
    assert BrowserChoice("chromium", "Bundled Chromium", True) in choices


def test_browsers_endpoint_returns_choices(tmp_path):
    app = create_app(app_home=tmp_path)
    client = TestClient(app)

    response = client.get("/api/browsers")

    assert response.status_code == 200
    body = response.json()
    assert body["defaultChannel"] in {"msedge", "chrome", "chromium"}
    assert any(choice["channel"] == "chromium" for choice in body["choices"])


def test_executable_exists_checks_known_windows_paths(monkeypatch, tmp_path):
    edge = tmp_path / "Microsoft" / "Edge" / "Application" / "msedge.exe"
    edge.parent.mkdir(parents=True)
    edge.write_text("", encoding="utf-8")
    monkeypatch.setattr("app.browsers.shutil.which", lambda _name: None)
    monkeypatch.setattr("app.browsers.windows_browser_roots", lambda: [tmp_path])

    assert executable_exists("msedge.exe")
