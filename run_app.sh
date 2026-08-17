#!/usr/bin/env bash
# Development launcher for MAALTECH Polish Editor on Linux / ChromeOS
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt

echo "If the UI fails to start, install system packages:"
echo "  sudo apt install -y python3-tk libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1"
echo

exec python Polish_Editor.py "$@"
