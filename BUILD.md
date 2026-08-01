# Building Desktop Executables

This app is a normal Python/PySide6 program (`main.py`), not natively an
`.exe`/`.app`/`.AppImage`. To turn it into a double-clickable desktop app
(what most people mean by "make it an APK/EXE for desktop"), you package it
with **PyInstaller**. A ready-made spec file (`blade_converter.spec`) is
included, and it has already been build-tested.

> There is no such thing as a desktop `.apk` — `.apk` is the Android package
> format. If you actually want an Android/mobile build, that requires a full
> rewrite (Kivy/BeeWare/etc.); PySide6 desktop apps cannot be packaged as
> `.apk`. This guide produces native **Windows (.exe)**, **macOS (.app)** and
> **Linux (binary/AppImage)** desktop builds instead.

## 1. Prerequisites

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

Build **on the target OS** — a Windows `.exe` must be built on Windows, a
macOS `.app` must be built on macOS, etc. PyInstaller does not cross-compile.

## 2. Build with the provided spec

```bash
pyinstaller blade_converter.spec
```

Output:
- **Windows/Linux:** `dist/LaravelBladeConverter/` (folder build — fastest startup, recommended)
- **macOS:** `dist/LaravelBladeConverter/` **and** `dist/LaravelBladeConverter.app`

Run it:
```bash
# Windows
dist\LaravelBladeConverter\LaravelBladeConverter.exe

# macOS
open dist/LaravelBladeConverter.app

# Linux
./dist/LaravelBladeConverter/LaravelBladeConverter
```

## 3. Single-file build (optional)

A one-folder build starts faster; a one-file `.exe`/binary is easier to
share as a single artifact but is slower to start (it unpacks to a temp
dir every launch):

```bash
pyinstaller --onefile --windowed --name LaravelBladeConverter main.py
```

## 4. Adding an app icon

Drop an icon into `resources/` and point the spec at it:
- Windows: `resources/icon.ico`
- macOS: `resources/icon.icns`

Then edit `blade_converter.spec`:
```python
icon="resources/icon.ico",   # in the EXE(...) block
```
and for macOS also set `icon="resources/icon.icns"` in the `BUNDLE(...)` block.

## 5. Windows installer (optional, polish)

Wrap the `dist/LaravelBladeConverter/` folder with
[Inno Setup](https://jrsoftware.org/isinfo.php) or
[NSIS](https://nsis.sourceforge.io/) to produce a proper `Setup.exe` with
Start Menu shortcuts and an uninstaller.

## 6. macOS notarization (optional, for distributing outside the App Store)

Unsigned `.app` bundles will be blocked by Gatekeeper on other Macs. To
distribute publicly you'll need an Apple Developer ID, then:
```bash
codesign --deep --force --sign "Developer ID Application: Your Name" dist/LaravelBladeConverter.app
xcrun notarytool submit dist/LaravelBladeConverter.app.zip --keychain-profile "notary-profile" --wait
```

## 7. Linux AppImage (optional)

```bash
pip install pyinstaller
pyinstaller blade_converter.spec
# then wrap dist/LaravelBladeConverter/ with linuxdeploy / appimagetool
```

## 8. Automating builds with GitHub Actions

`.github/workflows/build.yml` (included in this repo) builds Windows,
macOS, and Linux artifacts automatically whenever you push a version tag
(e.g. `v1.0.0`), and attaches them to the GitHub Release. See that file for
details — you don't need to run anything locally if you just push a tag.
