#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv-build
source .venv-build/bin/activate
pip install --upgrade pip
pip install -r requirements-build.txt

# Generate icon if needed (already produces the PNG source)
python tools/generate_icon.py || true

# Simple one-file or onedir build (adjust as needed)
pyinstaller --noconfirm --clean \
    --name PolishEditor \
    --windowed \
    --add-data "assets:assets" \
    --collect-all customtkinter \
    --collect-all tkinterdnd2 \
    --collect-all onnxruntime \
    --collect-all rembg \
    --hidden-import=PIL._tkinter_finder \
    Polish_Editor.py

echo "Built: dist/PolishEditor (or dist/PolishEditor/)"
echo "Test with: ./dist/PolishEditor --self-test-background"