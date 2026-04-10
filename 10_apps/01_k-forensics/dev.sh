#!/usr/bin/env bash
# k-forensics dev — starts backend gateway + frontend in background with log files
#
# Usage (run from anywhere):
#   10_apps/01_k-forensics/dev.sh start    # default — start everything
#   10_apps/01_k-forensics/dev.sh stop     # stop backend + frontend
#   10_apps/01_k-forensics/dev.sh restart  # stop then start
#   10_apps/01_k-forensics/dev.sh status   # show what's running
#   10_apps/01_k-forensics/dev.sh logs backend   # tail backend log
#   10_apps/01_k-forensics/dev.sh logs frontend  # tail frontend log
#
# Ports:
#   k-forensics backend  → 8100
#   k-forensics frontend → 3100
#   tennetctl backend    → 58000 (must be running first)

set -euo pipefail

KF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${KF_DIR}/../.." && pwd)"
LOG_DIR="${ROOT_DIR}/08_logs/k-forensics"
PID_DIR="${LOG_DIR}/.pids"

BACKEND_LOG="${LOG_DIR}/backend.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"
BACKEND_PID="${PID_DIR}/backend.pid"
FRONTEND_PID="${PID_DIR}/frontend.pid"

KF_BACKEND_PORT=8100
KF_FRONTEND_PORT=3100
KF_TENNETCTL_API_URL="${KF_TENNETCTL_API_URL:-http://localhost:58000}"

# ── helpers ──────────────────────────────────────────────────────────────────

c_red()    { printf '\033[31m%s\033[0m' "$*"; }
c_green()  { printf '\033[32m%s\033[0m' "$*"; }
c_yellow() { printf '\033[33m%s\033[0m' "$*"; }
c_blue()   { printf '\033[34m%s\033[0m' "$*"; }

log()  { printf '%s %s\n' "$(c_blue '[kf-dev]')" "$*"; }
warn() { printf '%s %s\n' "$(c_yellow '[kf-dev]')" "$*" >&2; }
die()  { printf '%s %s\n' "$(c_red '[kf-dev]')" "$*" >&2; exit 1; }

is_running() {
  local pid_file="$1"
  [[ -f "${pid_file}" ]] || return 1
  local pid
  pid="$(cat "${pid_file}")"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

stop_pid() {
  local label="$1"
  local pid_file="$2"
  if is_running "${pid_file}"; then
    local pid
    pid="$(cat "${pid_file}")"
    log "stopping ${label} (pid ${pid})"
    kill -TERM -- "-${pid}" 2>/dev/null || kill -TERM "${pid}" 2>/dev/null || true
    pkill -TERM -P "${pid}" 2>/dev/null || true
    for _ in 1 2 3 4 5 6 7 8; do
      kill -0 "${pid}" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "${pid}" 2>/dev/null; then
      warn "${label} did not exit; sending SIGKILL"
      pkill -KILL -P "${pid}" 2>/dev/null || true
      kill -KILL "${pid}" 2>/dev/null || true
    fi
    rm -f "${pid_file}"
  else
    log "${label} not running"
  fi
}

kill_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti :"${port}" 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    log "port ${port} in use by pid(s) ${pids} — killing"
    echo "${pids}" | xargs kill -TERM 2>/dev/null || true
    sleep 1
    pids="$(lsof -ti :"${port}" 2>/dev/null || true)"
    [[ -n "${pids}" ]] && echo "${pids}" | xargs kill -KILL 2>/dev/null || true
  fi
}

reset_logs() {
  rm -rf "${LOG_DIR}"
  mkdir -p "${LOG_DIR}" "${PID_DIR}"
  : > "${BACKEND_LOG}"
  : > "${FRONTEND_LOG}"
}

# ── commands ─────────────────────────────────────────────────────────────────

cmd_start() {
  reset_logs

  if ! curl -sf "${KF_TENNETCTL_API_URL}/healthz" > /dev/null 2>&1; then
    die "tennetctl backend not reachable at ${KF_TENNETCTL_API_URL} — start it first with ./11_infra/dev.sh start"
  fi
  log "tennetctl backend healthy at ${KF_TENNETCTL_API_URL}"

  # Backend
  kill_port "${KF_BACKEND_PORT}"
  log "starting k-forensics backend on http://localhost:${KF_BACKEND_PORT}"
  (
    cd "${KF_DIR}/04_backend"
    KF_TENNETCTL_API_URL="${KF_TENNETCTL_API_URL}" \
    ALLOWED_ORIGINS="http://localhost:${KF_FRONTEND_PORT},http://127.0.0.1:${KF_FRONTEND_PORT}" \
    nohup "${KF_DIR}/04_backend/.venv/bin/python" -m uvicorn 01_core.app:app \
      --app-dir "${KF_DIR}/04_backend" \
      --host 0.0.0.0 \
      --port "${KF_BACKEND_PORT}" \
      --reload \
      --reload-dir "${KF_DIR}/04_backend" \
      >> "${BACKEND_LOG}" 2>&1 &
    echo $! > "${BACKEND_PID}"
  )
  sleep 1
  if is_running "${BACKEND_PID}"; then
    log "backend started (pid $(cat "${BACKEND_PID}")) → logs: ${BACKEND_LOG}"
  else
    die "backend failed to start — tail ${BACKEND_LOG}"
  fi

  # Frontend
  kill_port "${KF_FRONTEND_PORT}"
  log "starting k-forensics frontend on http://localhost:${KF_FRONTEND_PORT}"
  (
    cd "${KF_DIR}/06_frontend"
    NEXT_PUBLIC_API_URL="http://localhost:${KF_BACKEND_PORT}" \
    nohup npm run dev -- --port "${KF_FRONTEND_PORT}" \
      >> "${FRONTEND_LOG}" 2>&1 &
    echo $! > "${FRONTEND_PID}"
  )
  sleep 1
  if is_running "${FRONTEND_PID}"; then
    log "frontend started (pid $(cat "${FRONTEND_PID}")) → logs: ${FRONTEND_LOG}"
  else
    die "frontend failed to start — tail ${FRONTEND_LOG}"
  fi

  log "$(c_green 'all up')"
  log "  backend  → http://localhost:${KF_BACKEND_PORT}/healthz"
  log "  frontend → http://localhost:${KF_FRONTEND_PORT}"
  log "  upstream → http://localhost:58000/docs"
  log "  logs     → ${LOG_DIR}/"
}

cmd_stop() {
  stop_pid backend  "${BACKEND_PID}"
  stop_pid frontend "${FRONTEND_PID}"
}

cmd_restart() {
  cmd_stop
  cmd_start
}

cmd_status() {
  if is_running "${BACKEND_PID}";  then log "backend  $(c_green 'UP')   pid $(cat "${BACKEND_PID}")  port ${KF_BACKEND_PORT}";  else log "backend  $(c_red 'DOWN')"; fi
  if is_running "${FRONTEND_PID}"; then log "frontend $(c_green 'UP')   pid $(cat "${FRONTEND_PID}") port ${KF_FRONTEND_PORT}"; else log "frontend $(c_red 'DOWN')"; fi
}

cmd_logs() {
  local target="${1:-}"
  case "${target}" in
    backend)  exec tail -F "${BACKEND_LOG}" ;;
    frontend) exec tail -F "${FRONTEND_LOG}" ;;
    "")       exec tail -F "${BACKEND_LOG}" "${FRONTEND_LOG}" ;;
    *)        die "unknown log target: ${target} (use backend|frontend)" ;;
  esac
}

# ── dispatch ──────────────────────────────────────────────────────────────────

main() {
  local cmd="${1:-start}"
  shift || true
  case "${cmd}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    restart) cmd_restart ;;
    status)  cmd_status ;;
    logs)    cmd_logs "${@:-}" ;;
    -h|--help|help)
      sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      ;;
    *) die "unknown command: ${cmd} (use: start|stop|restart|status|logs)" ;;
  esac
}

main "$@"
