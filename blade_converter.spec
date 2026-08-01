# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for Laravel Blade Converter.

Build with:
    pyinstaller blade_converter.spec

Produces a single-folder (onedir) build in dist/LaravelBladeConverter/
which starts fastest and is the recommended distributable. For a
single-file executable instead, pass --onefile when regenerating this
spec, or add `--onefile` handling manually (see BUILD.md).
"""

import sys
from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH)

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LaravelBladeConverter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=(sys.platform == "darwin"),
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # set to "resources/icon.ico" (Win) / "resources/icon.icns" (macOS) if you add one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LaravelBladeConverter",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="LaravelBladeConverter.app",
        icon=None,
        bundle_identifier="in.imdevops.laravelbladeconverter",
        info_plist={
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": "True",
        },
    )
