#!/usr/bin/env bash
# Build MAALTECH Polish Editor for Linux (x64) – one-file binary + installable package
set -euo pipefail
cd "$(dirname "$0")"

APP_NAME="PolishEditor"
VERSION="1.1.2"
DIST_DIR="dist"
PKG_DIR="linux-package"
OUTPUT_TGZ="dist/MAALTECH-Polish-Editor-v${VERSION}-linux-x64.tar.gz"

echo "[1/5] Preparing build environment..."
if [ ! -d ".venv-build" ]; then
    python3 -m venv .venv-build
fi
# shellcheck disable=SC1091
source .venv-build/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt

echo "[2/5] Generating application icon..."
python tools/generate_icon.py || true

echo "[3/5] Building standalone Linux binary with PyInstaller..."
python -m PyInstaller --noconfirm --clean PolishEditor-linux.spec

if [ ! -f "${DIST_DIR}/${APP_NAME}" ]; then
    echo "ERROR: Expected binary ${DIST_DIR}/${APP_NAME} was not produced."
    exit 1
fi

echo "[4/5] Validating the packaged background-removal engine..."
# Self-test does not require a display
if ! "${DIST_DIR}/${APP_NAME}" --self-test-background; then
    if [ -f "PolishEditor_background_self_test.log" ]; then
        cat PolishEditor_background_self_test.log
    fi
    echo "ERROR: Background self-test failed. Aborting package creation."
    exit 1
fi

echo "[5/5] Creating installable Linux package (tarball + install script)..."
rm -rf "${PKG_DIR}"
mkdir -p "${PKG_DIR}/bin" \
         "${PKG_DIR}/share/icons/hicolor/256x256/apps" \
         "${PKG_DIR}/share/applications" \
         "${PKG_DIR}/share/doc/maaltech-polish-editor"

# Binary
cp "${DIST_DIR}/${APP_NAME}" "${PKG_DIR}/bin/"
chmod +x "${PKG_DIR}/bin/${APP_NAME}"

# Icon (PNG preferred on Linux)
if [ -f "assets/maaltech_mascot_icon.png" ]; then
    cp assets/maaltech_mascot_icon.png \
       "${PKG_DIR}/share/icons/hicolor/256x256/apps/maaltech_mascot_icon.png"
fi

# Desktop entry template (install.sh rewrites Exec with absolute path)
cat > "${PKG_DIR}/share/applications/MAALTECH-Polish-Editor.desktop" << 'EOF'
[Desktop Entry]
Version=1.1.2
Type=Application
Name=MAALTECH Polish Editor
GenericName=Image Polish Editor
Comment=Natural-looking local image refinement, face-aware polishing and background removal
Exec=PolishEditor %F
Icon=maaltech_mascot_icon
Terminal=false
Categories=Graphics;Photography;ImageProcessing;
MimeType=image/jpeg;image/png;image/webp;image/bmp;image/tiff;image/x-tiff;
Keywords=polish;skin;background;remover;ai;local;
StartupNotify=true
StartupWMClass=PolishEditor
EOF

# Docs
cp README.md "${PKG_DIR}/share/doc/maaltech-polish-editor/" 2>/dev/null || true
if [ -f CHANGELOG.md ]; then
    cp CHANGELOG.md "${PKG_DIR}/share/doc/maaltech-polish-editor/"
fi

# install.sh – places files into ~/.local (no root required)
cat > "${PKG_DIR}/install.sh" << 'INSTALL_EOF'
#!/usr/bin/env bash
# Install MAALTECH Polish Editor into the current user's ~/.local hierarchy
set -euo pipefail

PREFIX="${HOME}/.local"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing MAALTECH Polish Editor to ${PREFIX} ..."

mkdir -p "${PREFIX}/bin" \
         "${PREFIX}/share/icons/hicolor/256x256/apps" \
         "${PREFIX}/share/applications" \
         "${PREFIX}/share/doc/maaltech-polish-editor"

install -m 755 "${SCRIPT_DIR}/bin/PolishEditor" "${PREFIX}/bin/PolishEditor"

if [ -f "${SCRIPT_DIR}/share/icons/hicolor/256x256/apps/maaltech_mascot_icon.png" ]; then
    install -m 644 \
        "${SCRIPT_DIR}/share/icons/hicolor/256x256/apps/maaltech_mascot_icon.png" \
        "${PREFIX}/share/icons/hicolor/256x256/apps/maaltech_mascot_icon.png"
fi

# Desktop file with absolute Exec path so it works from any launcher
cat > "${PREFIX}/share/applications/MAALTECH-Polish-Editor.desktop" << DESKTOP_EOF
[Desktop Entry]
Version=1.1.2
Type=Application
Name=MAALTECH Polish Editor
GenericName=Image Polish Editor
Comment=Natural-looking local image refinement, face-aware polishing and background removal
Exec=${PREFIX}/bin/PolishEditor %F
Icon=maaltech_mascot_icon
Terminal=false
Categories=Graphics;Photography;ImageProcessing;
MimeType=image/jpeg;image/png;image/webp;image/bmp;image/tiff;image/x-tiff;
Keywords=polish;skin;background;remover;ai;local;
StartupNotify=true
StartupWMClass=PolishEditor
DESKTOP_EOF
chmod 644 "${PREFIX}/share/applications/MAALTECH-Polish-Editor.desktop"

if [ -d "${SCRIPT_DIR}/share/doc/maaltech-polish-editor" ]; then
    cp -a "${SCRIPT_DIR}/share/doc/maaltech-polish-editor/." \
          "${PREFIX}/share/doc/maaltech-polish-editor/"
fi

# Update desktop database if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${PREFIX}/share/applications" 2>/dev/null || true
fi

echo
echo "Installation complete."
echo "  Binary : ${PREFIX}/bin/PolishEditor"
echo "  Desktop: ${PREFIX}/share/applications/MAALTECH-Polish-Editor.desktop"
echo
echo "You can launch the app from your application menu or by running:"
echo "  PolishEditor"
echo
echo "Make sure ${PREFIX}/bin is on your PATH (it usually is for ~/.local)."
echo
echo "To uninstall later, run the companion uninstall.sh or remove the files above."
INSTALL_EOF
chmod +x "${PKG_DIR}/install.sh"

# uninstall helper
cat > "${PKG_DIR}/uninstall.sh" << 'UNINSTALL_EOF'
#!/usr/bin/env bash
set -euo pipefail
PREFIX="${HOME}/.local"
rm -f "${PREFIX}/bin/PolishEditor"
rm -f "${PREFIX}/share/applications/MAALTECH-Polish-Editor.desktop"
rm -f "${PREFIX}/share/icons/hicolor/256x256/apps/maaltech_mascot_icon.png"
rm -rf "${PREFIX}/share/doc/maaltech-polish-editor"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${PREFIX}/share/applications" 2>/dev/null || true
fi
echo "MAALTECH Polish Editor has been removed from ${PREFIX}."
UNINSTALL_EOF
chmod +x "${PKG_DIR}/uninstall.sh"

# Create the final tarball
mkdir -p dist
tar -czf "${OUTPUT_TGZ}" -C "${PKG_DIR}" .
echo
echo "Build complete."
echo "  Portable binary : ${DIST_DIR}/${APP_NAME}"
echo "  Linux package   : ${OUTPUT_TGZ}"
echo
echo "To install on a target Linux machine:"
echo "  tar -xzf MAALTECH-Polish-Editor-v${VERSION}-linux-x64.tar.gz"
echo "  ./install.sh"
echo
echo "Or run the binary directly from dist/PolishEditor"
