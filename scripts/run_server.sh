#!/bin/zsh
set -eu
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/data/runtime"
exec "$PROJECT_DIR/.venv/bin/python" run.py serve --host 127.0.0.1 --port 8000 >> "$PROJECT_DIR/data/runtime/web.log" 2>&1
