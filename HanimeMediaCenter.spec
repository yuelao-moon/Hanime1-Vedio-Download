# -*- mode: python ; coding: utf-8 -*-

import importlib.util

if importlib.util.find_spec('curl_cffi') is None:
    raise RuntimeError(
        'curl_cffi is required for packaged Cloudflare cookie requests. '
        'Build with python_backend\\.venv\\Scripts\\pyinstaller.exe or install requirements first.'
    )


a = Analysis(
    ['python_backend\\desktop.py'],
    pathex=['python_backend'],
    binaries=[],
    datas=[('src/main/resources/static', 'src/main/resources/static')],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='HanimeMediaCenter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
