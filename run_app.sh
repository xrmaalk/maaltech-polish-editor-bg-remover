#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Optional: first-time system deps reminder
echo "If you hit missing libraries, install: python3-tk libgl1 libglib2.0-0 (Debian/Ubuntu/ChromeOS)"

python Polish_Editor.py "$@"