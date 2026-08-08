# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller one-file build for Hanime Media Center."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

ROOT = Path(SPECPATH).resolve()
BACKEND = ROOT / "python_backend"
STATIC = ROOT / "src" / "main" / "resources" / "static"
ENTRY = BACKEND / "desktop.py"

if importlib.util.find_spec("curl_cffi") is None:
    raise RuntimeError(
        "curl_cffi is required for packaged Cloudflare cookie requests. "
        "Build with python_backend\\.venv\\Scripts\\pyinstaller.exe "
        "or install python_backend\\requirements.txt first."
    )

if not ENTRY.is_file():
    raise FileNotFoundError(f"Missing desktop entry: {ENTRY}")
if not STATIC.is_dir():
    raise FileNotFoundError(f"Missing frontend static dir: {STATIC}")


def merge_collect(package: str):
    datas, binaries, hiddenimports = collect_all(package)
    return list(datas), list(binaries), list(hiddenimports)


datas = [(str(STATIC), "src/main/resources/static")]
binaries = []
hiddenimports = [
    "_cffi_backend",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "curl_cffi",
    "curl_cffi.requests",
    "selectolax",
    "selectolax.parser",
    "selectolax.lexbor",
    "certifi",
    "httpx",
    "anyio",
    "anyio._backends._asyncio",
    "multipart",
]

for package in ("curl_cffi", "certifi", "selectolax"):
    pkg_datas, pkg_binaries, pkg_hidden = merge_collect(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# Ensure curl_cffi native DLLs under *.libs are bundled even if collect_all misses them.
site_packages = Path(importlib.util.find_spec("curl_cffi").origin).resolve().parent.parent
curl_libs = site_packages / "curl_cffi.libs"
if curl_libs.is_dir():
    for dll in curl_libs.glob("*.dll"):
        binaries.append((str(dll), "."))

hiddenimports += collect_submodules("playwright")
hiddenimports += collect_submodules("uvicorn")
binaries += collect_dynamic_libs("curl_cffi")
datas += collect_data_files("certifi")

# Deduplicate while preserving order.
seen_hidden = set()
hiddenimports = [name for name in hiddenimports if not (name in seen_hidden or seen_hidden.add(name))]

a = Analysis(
    [str(ENTRY)],
    pathex=[str(BACKEND)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "pytest_asyncio",
        "unittest",
        "doctest",
        "pdb",
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "test",
        "tests",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="HanimeMediaCenter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
