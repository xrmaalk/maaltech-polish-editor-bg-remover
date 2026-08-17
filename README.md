# MAALTECH Polish Editor v1.1.2

Natural-looking local image refinement for portraits and product shots.  
Face-aware skin polish, adjustable texture retention, optional AI background removal, and transparent PNG/WebP output — all processed on your machine.

**Supported platforms**

- Windows 10 / 11 (x64) – portable EXE + Inno Setup installer  
- Linux (Ubuntu / Debian / Fedora and ChromeOS Crostini) x64 – portable binary + user-local install package

## Features

- Drag-and-drop image loading
- Before / After preview
- Adjustable polish strength and texture retention
- Face detection with optional skin-tone fallback
- Optional background removal (`u2net_human_seg` via rembg)
- Transparent PNG / WebP preservation
- Fully offline after the first background-removal model download
- Responsive UI (processing runs in a background thread)

## Quick start – run from source

### Windows

1. Install 64-bit Python 3.11 or newer from https://www.python.org/downloads/  
   (tick **Add Python to PATH** during installation).
2. Double-click `run_app.bat`.

The first launch creates a private virtual environment and installs dependencies.

### Linux / ChromeOS (Crostini)

1. Install system packages (Debian / Ubuntu / ChromeOS example):

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip python3-tk \
     libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1
   ```

2. Make the launcher executable and start the app:

   ```bash
   chmod +x run_app.sh
   ./run_app.sh
   ```

## Build installers

### Windows

Prerequisites:

- 64-bit Python 3.11+
- [Inno Setup 7](https://jrsoftware.org/isinfo.php) (optional but required for the installer)

```bat
build_windows.bat
```

Outputs:

| Artifact | Location |
|----------|----------|
| Portable EXE | `dist\PolishEditor.exe` |
| Installer | `installer\output\PolishEditorSetup-v1.1.2.exe` |

The build runs a background-removal self-test before creating the installer.  
If the test fails, `PolishEditor_background_self_test.log` is written and the process stops.

If you already have the EXE and only need the installer, run `build_installer.bat`.

> The generated EXE and installer are unsigned development builds. Windows SmartScreen may show an “unknown publisher” warning until a code-signing certificate is applied.

### Linux

```bash
chmod +x build_linux.sh
./build_linux.sh
```

Outputs:

| Artifact | Location |
|----------|----------|
| Portable binary | `dist/PolishEditor` |
| Install package | `dist/MAALTECH-Polish-Editor-v1.1.2-linux-x64.tar.gz` |

#### Installing the Linux package on a target machine

```bash
tar -xzf MAALTECH-Polish-Editor-v1.1.2-linux-x64.tar.gz
./install.sh
```

This installs into `~/.local` (no root required):

- Binary → `~/.local/bin/PolishEditor`
- Desktop entry → `~/.local/share/applications/`
- Icon → `~/.local/share/icons/hicolor/256x256/apps/`

Uninstall with the included `uninstall.sh` or by deleting the files above.

## Using the application

1. Open or drop a supported JPG, PNG, WebP, BMP or TIFF image.
2. Adjust **Polish strength** and **Texture retention**.
3. Leave **Limit processing to detected faces** enabled for portraits.  
   Enable the fallback option to process visible skin tones when a frontal face is not detected.
4. Under **Background** choose **Keep** or **Remove**.  
   Remove produces transparency and automatically suggests PNG when saving.
5. Click **Polish image**, compare the Before / After views, then **Save as…**.

All processing is local. Images are never uploaded.  
Background removal uses the `u2net_human_seg` model; rembg downloads it on first use and caches it for offline runs thereafter.

## Project layout

```
Polish_Editor.py          # Application entry point
src/
  __init__.py             # __version__ = "1.1.2"
  app.py                  # CustomTkinter GUI
  processing.py           # Image engine (polish + rembg)
assets/
  maaltech_mascot_icon.png
  app.ico                 # Generated multi-resolution Windows icon
tools/
  generate_icon.py
installer/
  PolishEditor.iss        # Inno Setup script (Windows)
PolishEditor.spec         # PyInstaller (Windows)
PolishEditor-linux.spec   # PyInstaller (Linux)
build_windows.bat
build_installer.bat
build_linux.sh
run_app.bat / run_app.sh
requirements.txt
requirements-build.txt
tests/
```

## Developer notes

- Regenerate the Windows icon only:

  ```bat
  python tools\generate_icon.py
  ```

  or supply replacement artwork:

  ```bat
  python tools\generate_icon.py --source assets\replacement.png
  ```

- Run unit tests:

  ```bash
  python -m pytest tests
  ```

- The face / skin-tone detection is heuristic. Always review the Before / After preview before saving.

## License & attribution

Copyright (c) 2026 MAALTECH.  
Background removal powered by [rembg](https://github.com/danielgatis/rembg) and the `u2net_human_seg` model.
