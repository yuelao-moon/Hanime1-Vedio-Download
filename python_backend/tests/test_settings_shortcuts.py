from __future__ import annotations

from python_backend.app.settings import AppSettings


def test_settings_include_navigation_shortcuts():
    settings = AppSettings.from_dict({
        "shortcutBack": "Alt+ArrowLeft",
        "shortcutForward": "Alt+ArrowRight",
    })

    assert settings.shortcutBack == "Alt+ArrowLeft"
    assert settings.shortcutForward == "Alt+ArrowRight"
    assert settings.to_dict()["shortcutBack"] == "Alt+ArrowLeft"
