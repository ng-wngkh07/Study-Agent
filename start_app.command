#!/bin/zsh
set -eu

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
URL="http://127.0.0.1:8000/"
LOG_DIR="$PROJECT_DIR/data/runtime"
LOG_FILE="$LOG_DIR/web.log"

if [[ ! -x "$PYTHON" ]]; then
  echo "Khong tim thay moi truong .venv. Xem huong dan cai dat trong README.md."
  exit 1
fi

mkdir -p "$LOG_DIR"

"$PROJECT_DIR/scripts/service.sh" start

echo "Ung dung dang chay tai $URL"
open "$URL"
