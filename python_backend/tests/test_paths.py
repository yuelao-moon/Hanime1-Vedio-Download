import sys

from app.paths import static_dir


def test_static_dir_uses_pyinstaller_unpack_root(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert static_dir() == tmp_path / "src" / "main" / "resources" / "static"
