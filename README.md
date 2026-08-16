# MAALTECH Polish Editor

Polish Editor turns the MAALTECH `Polish_Editor.py` image routine project into a Windows desktop application.

It includes drag-and-drop loading, before/after previews, adjustable polish and texture controls, face detection, optional background removal, transparent-PNG preservation, and background processing so the interface remains responsive.

## Usage Method 1: Run from source on Windows

1. Install 64-bit Python 3.11 or newer from (https://www.python.org/downloads/). During installation, select **Add Python to PATH**.
2. Double-click `run_app.bat`.

The first launch creates a private Python environment and installs the required packages. Later launches reuse it.

## Usage Method 2: Build the Windows EXE and installer

1. Install 64-bit Python 3.11 or newer (https://www.python.org/downloads/).
2. Install [Inno Setup 7](https://jrsoftware.org/isinfo.php) if you want the installer. The portable EXE can be built without it.
3. Double-click `build_windows.bat`.

Build outputs:

- `dist\PolishEditor.exe` — standalone portable application.
- `installer\output\PolishEditorSetup.exe` — per-user Windows installer with Start menu/uninstall entries.

The build script runs `PolishEditor.exe --self-test-background` before creating
the installer. If rembg or a native ONNX dependency was omitted from the frozen
EXE, the build stops and writes `PolishEditor_background_self_test.log`.

If Inno Setup was installed after the portable EXE was built, run `build_installer.bat` to create only the installer.

The generated EXE and installer are unsigned development builds. Windows SmartScreen may show an "unknown publisher" notice until the release is signed with a trusted Windows code-signing certificate.

## Use the application

1. Open or drop a supported JPG, PNG, WebP, BMP, or TIFF image.
2. Adjust polish strength and texture retention.
3. Leave **Limit processing to detected faces** enabled for portraits. The fallback option can process visible skin tones when a frontal face is not detected.
4. Under **Background**, choose **Keep** or **Remove**. Remove produces transparency and automatically suggests PNG when saving.
5. Select **Polish image**, compare the Before and After views, and then select **Save as…**.

All image processing happens locally and images are never uploaded. Background removal uses the `u2net_human_seg` model. Rembg downloads that model on the first background-removal run and caches it on the computer; later runs can work offline. The official rembg documentation describes this first-use model download behavior.

## Developer notes

- Main GUI: `src/app.py`
- Processing engine: `src/processing.py`
- Mascot icon source: `assets/maaltech_mascot_icon.png`
- Icon generator: `tools/generate_icon.py`
- PyInstaller configuration: `PolishEditor.spec`
- Inno Setup installer: `installer/PolishEditor.iss`
- Test command: `python -m pytest tests`

`build_windows.bat` automatically regenerates `assets/app.ico` from the bundled
MAALTECH mascot source before building. To regenerate only the icon, run:

```bat
python tools\generate_icon.py
```

You can also supply replacement square PNG artwork without editing the script:

```bat
python tools\generate_icon.py --source assets\replacement.png
```

The output remains an automated image effect. Face and skin-tone detection can vary with pose, lighting, and camera color processing, so the Before/After preview should be reviewed before saving.

## Linux & ChromeOS

The application runs on Linux (including the ChromeOS Linux container / Crostini).

### Run from source

1. Install system packages (Debian/Ubuntu/ChromeOS):

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip python3-tk \
     libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1
   ```

2. Allow file execution permissions:

```bash
   chmod +x run_app.sh
   ./run_app.sh
```
