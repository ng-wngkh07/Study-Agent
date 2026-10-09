#!/bin/zsh
# Service management script for Psychology QA Agent.
# Manages web server and session-detached watchdog supervisor (KeepAlive auto-restart).
# Supports install, start, stop, restart, status safely and idempotently.

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
PORT=8000
URL="http://127.0.0.1:$PORT/"
HEALTH_URL="http://127.0.0.1:$PORT/api/health"
LOG_DIR="$PROJECT_DIR/data/runtime"
LOG_FILE="$LOG_DIR/web.log"
WEB_PID_FILE="$LOG_DIR/web.pid"
SUPERVISOR_PID_FILE="$LOG_DIR/supervisor.pid"
SERVICE_NAME="com.psychology.agent.web"
USER_LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST_DEST="$USER_LAUNCH_AGENTS/$SERVICE_NAME.plist"

mkdir -p "$LOG_DIR"

SUPERVISOR_SCRIPT="$PROJECT_DIR/scripts/supervisor.sh"
DETACHED_LAUNCHER="$PROJECT_DIR/scripts/start_detached_service.py"

OLLAMA_PORT=11434
OLLAMA_URL="http://127.0.0.1:$OLLAMA_PORT"
OLLAMA_TAGS_URL="$OLLAMA_URL/api/tags"
OLLAMA_PID_FILE="$LOG_DIR/ollama.pid"
OLLAMA_LOCK_FILE="$LOG_DIR/ollama.lock"
OLLAMA_LOG_FILE="$LOG_DIR/ollama-daemon.log"
GPU_STATE_FILE="$LOG_DIR/gpu_state.json"
GPU_LOCK_FILE="$LOG_DIR/gpu.lock"

get_ollama_listening_pid() {
  lsof -nP -iTCP:"$OLLAMA_PORT" -sTCP:LISTEN -Fp 2>/dev/null | sed 's/^p//' | head -n 1 || true
}

is_ollama_process() {
  local opid="$1"
  if [[ -z "$opid" ]] || ! kill -0 "$opid" 2>/dev/null; then
    return 1
  fi
  local cmdline
  cmdline="$(ps -ww -p "$opid" -o command= 2>/dev/null || true)"
  if [[ "$cmdline" == *"ollama"* ]]; then
    return 0
  fi
  return 1
}

get_listening_pid() {
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -Fp 2>/dev/null | sed 's/^p//' | head -n 1 || true
}

is_project_process() {
  local target_pid="$1"
  if [[ -z "$target_pid" ]] || ! kill -0 "$target_pid" 2>/dev/null; then
    return 1
  fi
  local cmdline
  cmdline="$(ps -ww -p "$target_pid" -o command= 2>/dev/null || true)"
  local proc_cwd
  proc_cwd="$(lsof -a -p "$target_pid" -d cwd -Fn 2>/dev/null | grep '^n' | head -n 1 | sed 's/^n//')"
  if [[ "$cmdline" == *"run.py serve"* && -n "$proc_cwd" && "$proc_cwd" -ef "$PROJECT_DIR" ]]; then
    return 0
  fi
  return 1
}

is_target_supervisor() {
  local sp="$1"
  if [[ -z "$sp" ]] || ! kill -0 "$sp" 2>/dev/null; then
    return 1
  fi
  local cmdline
  cmdline="$(ps -ww -p "$sp" -o command= 2>/dev/null || true)"
  if [[ "$cmdline" == *" -c "* ]]; then
    return 1
  fi
  local proc_cwd
  proc_cwd="$(lsof -a -p "$sp" -d cwd -Fn 2>/dev/null | grep '^n' | head -n 1 | sed 's/^n//')"
  if [[ "$cmdline" == "/bin/zsh $SUPERVISOR_SCRIPT"* && -n "$proc_cwd" && "$proc_cwd" -ef "$PROJECT_DIR" ]]; then
    return 0
  fi
  return 1
}

is_supervisor_running() {
  if [[ -f "$SUPERVISOR_PID_FILE" ]]; then
    local spid
    spid="$(cat "$SUPERVISOR_PID_FILE" 2>/dev/null || true)"
    if is_target_supervisor "$spid"; then
      return 0
    fi
  fi
  return 1
}

cmd_status() {
  local web_pid
  web_pid="$(get_listening_pid)"
  local ollama_pid
  ollama_pid="$(get_ollama_listening_pid)"
  echo "============================================================"
  echo "Trạng thái Dịch vụ & Độ sẵn sàng LLM (Tâm Lý Học AI)"
  echo "============================================================"
  echo "• Thư mục dự án:   $PROJECT_DIR"
  echo "• Tệp nhật ký web: $LOG_FILE"

  # 1. Supervisor status
  if is_supervisor_running; then
    local spid
    spid="$(cat "$SUPERVISOR_PID_FILE" 2>/dev/null || true)"
    echo "• Giám sát viên:   🟢 Đang chạy (PID $spid, tự khởi động lại khi web thoát)"
  else
    echo "• Giám sát viên:   ⚪ Chưa chạy"
  fi

  # 2. Web Process and Port 8000
  local web_alive=false
  local web_foreign=false
  if [[ -n "$web_pid" ]]; then
    if is_project_process "$web_pid"; then
      echo "• Tiến trình web:  🟢 PID $web_pid (thuộc dự án)"
      web_alive=true
    else
      echo "• Cảnh báo cổng:   🔴 Cổng $PORT đang bị chiếm bởi PID $web_pid (KHÔNG thuộc dự án)"
      web_foreign=true
    fi
  else
    echo "• Tiến trình web:  ⚪ Chưa có tiến trình nào lắng nghe cổng $PORT"
  fi

  # 3. Web HTTP Health check
  local http_ok=false
  local health_json=""
  local reported_state=""
  local reported_ollama_conn=""
  local reported_inf_ready=""
  if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
    http_ok=true
    health_json="$(curl -s --max-time 2 "$HEALTH_URL" 2>/dev/null || true)"
    if [[ -n "$health_json" ]]; then
      reported_state="$("$PYTHON" -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('service_state', ''))" "$health_json" 2>/dev/null || echo "")"
      reported_ollama_conn="$("$PYTHON" -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('ollama_connected', ''))" "$health_json" 2>/dev/null || echo "")"
      reported_inf_ready="$("$PYTHON" -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('inference_ready', ''))" "$health_json" 2>/dev/null || echo "")"
    fi
    echo "• HTTP Health:     🟢 Hoạt động tốt ($HEALTH_URL)"
  else
    echo "• HTTP Health:     🔴 Không phản hồi ($HEALTH_URL)"
  fi

  # 4. Ollama Daemon status (direct inspection)
  local ollama_alive=false
  if [[ -n "$ollama_pid" ]]; then
    if is_ollama_process "$ollama_pid"; then
      if curl -fsS --max-time 2 "$OLLAMA_TAGS_URL" >/dev/null 2>&1; then
        echo "• Ollama Daemon:   🟢 PID $ollama_pid (đã kết nối $OLLAMA_URL)"
        ollama_alive=true
      else
        echo "• Ollama Daemon:   🟡 PID $ollama_pid (mở cổng $OLLAMA_PORT nhưng chưa phản hồi HTTP)"
      fi
    else
      echo "• Cảnh báo Ollama: 🔴 Cổng $OLLAMA_PORT bị chiếm bởi PID $ollama_pid (không phải Ollama)"
    fi
  else
    echo "• Ollama Daemon:   🔴 Không phát hiện daemon lắng nghe cổng $OLLAMA_PORT"
  fi

  # 5. GPU & Training Lock status
  local gpu_busy=false
  local gpu_pid=""
  if [[ -f "$GPU_STATE_FILE" ]]; then
    gpu_busy="$("$PYTHON" -c "
import json
try:
    with open('$GPU_STATE_FILE') as f:
        d = json.load(f)
    print('true' if d.get('state') in ('training', 'waiting_for_training') else 'false')
except Exception:
    print('false')
" 2>/dev/null || echo "false")"
    if [[ "$gpu_busy" == "true" ]]; then
      gpu_pid="$("$PYTHON" -c "
import json
try:
    with open('$GPU_STATE_FILE') as f:
        d = json.load(f)
    print(d.get('pid') or d.get('child_pid') or '')
except Exception:
    print('')
" 2>/dev/null || echo "")"
      echo "• Trạng thái GPU:  🟡 Đang huấn luyện (PID ${gpu_pid:-N/A}) - Suy luận LLM tạm hoãn hợp lệ, web sống"
    else
      echo "• Trạng thái GPU:  🟢 Sẵn sàng (không có job huấn luyện)"
    fi
  else
    echo "• Trạng thái GPU:  🟢 Sẵn sàng (không có file khóa)"
  fi

  # 6. Overall Readiness Synthesis
  echo "------------------------------------------------------------"
  if [[ "$web_foreign" == "true" ]]; then
    echo "• Tổng kết:        🔴 LỖI CHIẾM CỔNG: Cổng $PORT bị chiếm bởi PID $web_pid lạ"
  elif [[ "$http_ok" != "true" || "$web_alive" != "true" ]]; then
    echo "• Tổng kết:        🔴 DỊCH VỤ WEB NGỪNG HOẠT ĐỘNG (Web DOWN)"
  elif [[ "$ollama_alive" != "true" || "$reported_ollama_conn" == "False" ]]; then
    echo "• Tổng kết:        🟡 SUY GIẢM (DEGRADED): Web hoạt động, nhưng Ollama mất kết nối -> LLM không khả dụng"
  elif [[ "$gpu_busy" == "true" ]]; then
    echo "• Tổng kết:        🟡 SUY GIẢM (DEGRADED): Web hoạt động, GPU đang huấn luyện LoRA -> LLM tạm hoãn hợp lệ"
  else
    echo "• Tổng kết:        🟢 HOÀN TOÀN SẴN SÀNG: Web, Ollama và GPU đều hoạt động tốt"
  fi
  echo "============================================================"
}

cmd_ensure_ollama() {
  local opid
  opid="$(get_ollama_listening_pid)"
  if [[ -n "$opid" ]]; then
    if is_ollama_process "$opid"; then
      echo "Ollama đã đang chạy bình thường tại $OLLAMA_URL (PID $opid). Giữ nguyên, không thao tác lại."
      return 0
    else
      echo "CẢNH BÁO: Cổng $OLLAMA_PORT đang bị chiếm bởi PID $opid không phải Ollama." >&2
      return 1
    fi
  fi

  echo "Khởi động daemon Ollama cục bộ độc lập..."
  touch "$OLLAMA_LOCK_FILE"
  local op_lock_fd=""
  if ! zsystem flock -t 10 -f op_lock_fd "$OLLAMA_LOCK_FILE" 2>/dev/null; then
    echo "LỖI: Một thao tác khởi động Ollama khác đang diễn ra." >&2
    return 1
  fi

  # Re-check under lock
  opid="$(get_ollama_listening_pid)"
  if [[ -n "$opid" ]]; then
    echo "Ollama đã được khởi chạy bởi tiến trình khác (PID $opid)."
    return 0
  fi

  local ollama_bin
  ollama_bin="$(which ollama 2>/dev/null || echo "/opt/homebrew/bin/ollama")"
  if [[ ! -x "$ollama_bin" ]]; then
    echo "LỖI: Không tìm thấy thực thi ollama tại $ollama_bin." >&2
    return 1
  fi

  nohup "$ollama_bin" serve >> "$OLLAMA_LOG_FILE" 2>&1 &
  local new_opid=$!
  echo "$new_opid" > "$OLLAMA_PID_FILE"

  for attempt in {1..10}; do
    if curl -fsS --max-time 1 "$OLLAMA_TAGS_URL" >/dev/null 2>&1; then
      echo "✅ Daemon Ollama đã sẵn sàng tại $OLLAMA_URL (PID $new_opid)."
      return 0
    fi
    sleep 1
  done

  echo "⚠️ Daemon Ollama chưa phản hồi sau 10s. Xem log: $OLLAMA_LOG_FILE" >&2
  return 1
}

cmd_start() {
  local pid
  pid="$(get_listening_pid)"

  # Check if server is already running and healthy
  if [[ -n "$pid" ]] && is_project_process "$pid"; then
    if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
      echo "Máy chủ web đã đang chạy bình thường tại $URL (PID $pid)."
      local opid
      opid="$(get_ollama_listening_pid)"
      if [[ -z "$opid" ]] || ! curl -fsS --max-time 1 "$OLLAMA_TAGS_URL" >/dev/null 2>&1; then
        echo "⚠️ Cảnh báo: Ollama chưa kết nối ($OLLAMA_URL). Tính năng LLM sẽ không khả dụng."
      fi
      # Ensure supervisor is also running
      if ! is_supervisor_running; then
        echo "Khởi động giám sát viên phiên tách rời..."
        "$PYTHON" "$DETACHED_LAUNCHER" --log "$LOG_FILE" --cwd "$PROJECT_DIR" "$SUPERVISOR_SCRIPT" >/dev/null
      fi
      return 0
    fi
  fi

  # If port occupied by foreign process, warn and abort
  if [[ -n "$pid" ]] && ! is_project_process "$pid"; then
    echo "LỖI: Cổng $PORT đang bị chiếm bởi PID $pid không thuộc dự án." >&2
    return 1
  fi

  echo "Khởi động máy chủ web..."
  cd "$PROJECT_DIR"
  "$PYTHON" "$DETACHED_LAUNCHER" --log "$LOG_FILE" --cwd "$PROJECT_DIR" "$PYTHON" run.py serve --host 127.0.0.1 --port "$PORT" > "$WEB_PID_FILE"

  # Wait up to 15 seconds for HTTP health
  for attempt in {1..15}; do
    if curl -fsS --max-time 1 "$HEALTH_URL" >/dev/null 2>&1; then
      echo "✅ Máy chủ đã sẵn sàng tại $URL"
      local opid
      opid="$(get_ollama_listening_pid)"
      if [[ -z "$opid" ]] || ! curl -fsS --max-time 1 "$OLLAMA_TAGS_URL" >/dev/null 2>&1; then
        echo "⚠️ Cảnh báo: Ollama chưa kết nối ($OLLAMA_URL). Tính năng LLM sẽ không khả dụng cho đến khi Ollama chạy."
      fi
      if ! is_supervisor_running; then
        echo "Khởi động giám sát viên phiên tách rời..."
        "$PYTHON" "$DETACHED_LAUNCHER" --log "$LOG_FILE" --cwd "$PROJECT_DIR" "$SUPERVISOR_SCRIPT" >/dev/null
      fi
      return 0
    fi
    sleep 1
  done

  echo "⚠️ Máy chủ chưa phản hồi trong 15s. Xem log: $LOG_FILE"
  tail -n 20 "$LOG_FILE" 2>/dev/null || true
  return 1
}

cmd_stop() {
  echo "Dừng giám sát viên và máy chủ web..."
  # 1. Stop all verified supervisors belonging specifically to this project
  local spids=()
  if [[ -f "$SUPERVISOR_PID_FILE" ]]; then
    local file_pid
    file_pid="$(cat "$SUPERVISOR_PID_FILE" 2>/dev/null || true)"
    if [[ -n "$file_pid" ]] && is_target_supervisor "$file_pid"; then
      spids+=("$file_pid")
    fi
  fi

  local zsh_pids
  zsh_pids="$(pgrep -x zsh 2>/dev/null || true)"
  for sp in ${(f)zsh_pids}; do
    sp="$(echo "$sp" | tr -d '[:space:]')"
    if [[ -n "$sp" ]] && is_target_supervisor "$sp"; then
      if (( ! ${spids[(Ie)$sp]} )); then
        spids+=("$sp")
      fi
    fi
  done

  for sp in "${spids[@]}"; do
    if kill -0 "$sp" 2>/dev/null; then
      echo "Gửi SIGTERM tới giám sát viên PID $sp..."
      kill -15 "$sp" 2>/dev/null || true
      for _ in {1..10}; do
        if ! kill -0 "$sp" 2>/dev/null; then
          break
        fi
        sleep 0.2
      done
      if kill -0 "$sp" 2>/dev/null; then
        echo "Giám sát viên PID $sp chưa thoát sau 2s, gửi SIGKILL..."
        kill -9 "$sp" 2>/dev/null || true
        for _ in {1..10}; do
          if ! kill -0 "$sp" 2>/dev/null; then
            break
          fi
          sleep 0.2
        done
      fi
      if kill -0 "$sp" 2>/dev/null; then
        echo "LỖI: Không thể dừng giám sát viên PID $sp!" >&2
        return 1
      else
        echo "Đã xác nhận giám sát viên PID $sp dừng hoàn toàn."
      fi
    fi
  done
  rm -f "$SUPERVISOR_PID_FILE"

  # 2. Stop web server
  local pid
  pid="$(get_listening_pid)"
  if [[ -n "$pid" ]] && is_project_process "$pid"; then
    echo "Gửi SIGTERM tới tiến trình web PID $pid..."
    kill -15 "$pid" 2>/dev/null || true
    for _ in {1..15}; do
      if ! kill -0 "$pid" 2>/dev/null; then
        break
      fi
      sleep 0.3
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "Tiến trình chưa thoát sau 4.5s, gửi SIGKILL tới PID $pid..."
      kill -9 "$pid" 2>/dev/null || true
      for _ in {1..10}; do
        if ! kill -0 "$pid" 2>/dev/null; then
          break
        fi
        sleep 0.2
      done
    fi
    if kill -0 "$pid" 2>/dev/null; then
      echo "LỖI: Không thể dừng tiến trình web PID $pid!" >&2
      return 1
    else
      echo "Đã xác nhận tiến trình web PID $pid dừng hoàn toàn."
    fi
  fi
  rm -f "$WEB_PID_FILE"
  echo "Đã dừng dịch vụ."
}

cmd_restart() {
  cmd_stop
  sleep 1
  cmd_start
}

cmd_install() {
  echo ">>> Sao chép cấu hình LaunchAgent vào: $PLIST_DEST"
  mkdir -p "$USER_LAUNCH_AGENTS"
  cat <<EOF > "$PLIST_DEST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$SERVICE_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>run.py</string>
        <string>serve</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
EOF
  echo "Lưu ý: Khuyến nghị dùng giám sát viên phiên người dùng (scripts/service.sh start) để đảm bảo đồng bộ môi trường và đường dẫn dự án. Bản LaunchAgent được cung cấp dưới dạng tùy chọn tham khảo."
}

SERVICE_LOCK="$LOG_DIR/service.lock"
zmodload zsh/system 2>/dev/null || true

case "${1:-status}" in
  install)
    cmd_install
    ;;
  start|stop|restart|ensure-ollama)
    touch "$SERVICE_LOCK"
    op_lock_fd=""
    if ! zsystem flock -t 30 -f op_lock_fd "$SERVICE_LOCK" 2>/dev/null; then
      echo "LỖI: Một thao tác quản lý dịch vụ khác đang diễn ra trên $SERVICE_LOCK." >&2
      exit 1
    fi
    case "$1" in
      start) cmd_start ;;
      stop) cmd_stop ;;
      restart) cmd_restart ;;
      ensure-ollama) cmd_ensure_ollama ;;
    esac
    ;;
  status)
    cmd_status
    ;;
  *)
    echo "Cách dùng: $0 {start|stop|restart|status|ensure-ollama|install}"
    exit 1
    ;;
esac
