#!/bin/zsh
# Session-detached watchdog supervisor for Psychology QA Agent.
# Runs in user session, monitoring localhost:8000 and auto-restarting if process crashes.
# Also ensures local Ollama daemon stays active if absent, without disturbing live processes.
# Bypasses macOS TCC restrictions on ~/Documents without requiring elevated privileges.

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
PORT=8000
HEALTH_URL="http://127.0.0.1:$PORT/api/health"
OLLAMA_PORT=11434
LOG_DIR="$PROJECT_DIR/data/runtime"
LOG_FILE="$LOG_DIR/web.log"
SUPERVISOR_PID_FILE="$LOG_DIR/supervisor.pid"
WEB_PID_FILE="$LOG_DIR/web.pid"
mkdir -p "$LOG_DIR"

zmodload zsh/system 2>/dev/null || true
SUPERVISOR_LOCK="$LOG_DIR/supervisor.lock"
touch "$SUPERVISOR_LOCK"
if ! zsystem flock -t 0 -f lock_fd "$SUPERVISOR_LOCK" 2>/dev/null; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') [Supervisor] Khóa giám sát viên đang được tiến trình khác giữ. Bỏ qua khởi động trùng." >> "$LOG_FILE"
  exit 0
fi

echo $$ > "$SUPERVISOR_PID_FILE"

cleanup() {
  if [[ -f "$SUPERVISOR_PID_FILE" ]] && [[ "$(cat "$SUPERVISOR_PID_FILE" 2>/dev/null || true)" == "$$" ]]; then
    rm -f "$SUPERVISOR_PID_FILE" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 0' INT TERM

while true; do
  # 1. Check if web server is healthy
  if ! curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
    PORT_PID="$(lsof -nP -iTCP:$PORT -sTCP:LISTEN -Fp 2>/dev/null | sed 's/^p//' | head -n 1 || true)"
    if [[ -z "$PORT_PID" ]]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') [Supervisor] Web server down (no listener on $PORT). Restarting..." >> "$LOG_FILE"
      cd "$PROJECT_DIR"
      "$PYTHON" run.py serve --host 127.0.0.1 --port "$PORT" >> "$LOG_FILE" 2>&1 &
      NEW_PID=$!
      echo "$NEW_PID" > "$WEB_PID_FILE"
    else
      # Port occupied: check if project process
      CMDLINE="$(ps -ww -p "$PORT_PID" -o command= 2>/dev/null || true)"
      if [[ "$CMDLINE" != *"run.py serve"* ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [Supervisor] Cảnh báo: Cổng $PORT đang bị chiếm bởi PID ngoại lai $PORT_PID. Không khởi chạy đè." >> "$LOG_FILE"
      fi
    fi
  fi

  # 2. Check Ollama daemon presence without restarting if already healthy
  OLLAMA_PID="$(lsof -nP -iTCP:$OLLAMA_PORT -sTCP:LISTEN -Fp 2>/dev/null | sed 's/^p//' | head -n 1 || true)"
  if [[ -z "$OLLAMA_PID" ]]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [Supervisor] Ollama daemon vắng mặt trên cổng $OLLAMA_PORT. Đang khởi chạy tự động..." >> "$LOG_FILE"
    "$PROJECT_DIR/scripts/service.sh" ensure-ollama >> "$LOG_FILE" 2>&1 || true
  fi

  sleep 3
done
