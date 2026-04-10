#!/usr/bin/env bash
# =============================================================================
# dev_all.sh — start every service for local development
#
# Services:
#   tennetctl   backend  :58000  frontend  :53000
#   k-forensics backend  :8100
#   k-protect   backend  :8200
#   kbio demo-web        :3200
#   k-protect   frontend :3300
#
# Usage:
#   ./dev_all.sh            # start all
#   ./dev_all.sh stop       # stop all (leaves docker infra running)
#   ./dev_all.sh restart    # stop then start
#   ./dev_all.sh status     # show what's running
#   ./dev_all.sh logs       # tail all logs
#   ./dev_all.sh logs kf    # tail one service (tc|kf|kp|demo|kpfe)
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT}/08_logs"
PID_DIR="${LOG_DIR}/.pids"

# ── colours ───────────────────────────────────────────────────────────────────
c_red()   { printf '\033[31m%s\033[0m' "$*"; }
c_green() { printf '\033[32m%s\033[0m' "$*"; }
c_yellow(){ printf '\033[33m%s\033[0m' "$*"; }
c_blue()  { printf '\033[34m%s\033[0m' "$*"; }
c_bold()  { printf '\033[1m%s\033[0m'  "$*"; }

log()  { printf '%s %s\n' "$(c_blue '[dev_all]')" "$*"; }
warn() { printf '%s %s\n' "$(c_yellow '[dev_all]')" "$*" >&2; }
die()  { printf '%s %s\n' "$(c_red '[dev_all]')" "$*" >&2; exit 1; }

# ── pid helpers ───────────────────────────────────────────────────────────────
is_running() {
  local pf="$1"
  [[ -f "$pf" ]] || return 1
  local pid; pid="$(cat "$pf")"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

stop_pid() {
  local label="$1" pf="$2"
  if is_running "$pf"; then
    local pid; pid="$(cat "$pf")"
    log "stopping $label (pid $pid)"
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
    pkill -TERM -P "$pid" 2>/dev/null || true
    for _ in $(seq 1 10); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.3
    done
    kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" 2>/dev/null || true
    rm -f "$pf"
  else
    log "$label not running"
  fi
}

wait_port() {
  local port="$1" label="$2"
  for _ in $(seq 1 30); do
    curl -sf "http://localhost:${port}/healthz" -o /dev/null 2>/dev/null && return 0
    curl -sf "http://localhost:${port}" -o /dev/null 2>/dev/null && return 0
    sleep 0.5
  done
  warn "$label did not respond on :$port after 15s — check logs"
}

launch() {
  local label="$1" pf="$2" lf="$3"
  shift 3
  is_running "$pf" && { log "$label already running"; return; }
  log "starting $label"
  # Run the remainder as a backgrounded subshell
  ( "$@" >> "$lf" 2>&1 & echo $! > "$pf" )
}

# ── starters ─────────────────────────────────────────────────────────────────

start_tc_be() {
  local dev_env="${ROOT}/.dev.env"
  [[ -f "$dev_env" ]] && source "$dev_env"
  [[ -n "${DATABASE_URL:-}" ]] || die "DATABASE_URL not set. Source .dev.env or export DATABASE_URL=..."

  local pf="${PID_DIR}/tc_be.pid" lf="${LOG_DIR}/tc_be.log"
  is_running "$pf" && { log "tennetctl backend already running"; return; }
  log "starting tennetctl backend → :58000"
  (
    cd "${ROOT}/04_backend"
    DATABASE_URL="${DATABASE_URL}" \
    ALLOWED_ORIGINS="http://localhost:53000,http://localhost:3200,http://localhost:3300" \
    TENNETCTL_ENV=dev \
    nohup "${ROOT}/.venv/bin/python" -m uvicorn app:app \
      --app-dir 01_core --host 0.0.0.0 --port 58000 --reload \
      >> "$lf" 2>&1 &
    echo $! > "$pf"
  )
}

start_tc_fe() {
  local pf="${PID_DIR}/tc_fe.pid" lf="${LOG_DIR}/tc_fe.log"
  is_running "$pf" && { log "tennetctl frontend already running"; return; }
  log "starting tennetctl frontend → :53000"
  (
    cd "${ROOT}/06_frontend"
    nohup npm run dev -- --port 53000 \
      >> "$lf" 2>&1 &
    echo $! > "$pf"
  )
}

start_kf_be() {
  local pf="${PID_DIR}/kf_be.pid" lf="${LOG_DIR}/kf_be.log"
  is_running "$pf" && { log "k-forensics backend already running"; return; }
  log "starting k-forensics backend → :8100"
  (
    cd "${ROOT}/10_apps/01_k-forensics/04_backend"
    KF_TENNETCTL_API_URL="http://localhost:58000" \
    ALLOWED_ORIGINS="http://localhost:3200,http://localhost:3300,http://localhost:53000" \
    nohup .venv/bin/python -m uvicorn 01_core.app:app \
      --app-dir . --host 0.0.0.0 --port 8100 --reload --reload-dir . \
      >> "$lf" 2>&1 &
    echo $! > "$pf"
  )
}

start_kp_be() {
  local pf="${PID_DIR}/kp_be.pid" lf="${LOG_DIR}/kp_be.log"
  is_running "$pf" && { log "k-protect backend already running"; return; }
  log "starting k-protect backend → :8200"
  (
    cd "${ROOT}/10_apps/02_k-protect/04_backend"
    KP_TENNETCTL_API_URL="http://localhost:58000" \
    KP_KBIO_API_URL="http://localhost:8100" \
    ALLOWED_ORIGINS="http://localhost:3200,http://localhost:3300,http://localhost:53000" \
    PYTHONPATH="${ROOT}/10_apps/01_k-forensics/04_backend" \
    nohup .venv/bin/python -m uvicorn 01_core.app:app \
      --host 0.0.0.0 --port 8200 --reload --reload-dir . \
      >> "$lf" 2>&1 &
    echo $! > "$pf"
  )
}

start_demo() {
  local pf="${PID_DIR}/demo.pid" lf="${LOG_DIR}/demo.log"
  is_running "$pf" && { log "kbio demo-web already running"; return; }
  log "starting kbio demo-web → :3200"
  (
    cd "${ROOT}/10_apps/01_k-forensics/05_sdk/packages/demo-web"
    nohup npm run dev \
      >> "$lf" 2>&1 &
    echo $! > "$pf"
  )
}

start_kp_fe() {
  local pf="${PID_DIR}/kp_fe.pid" lf="${LOG_DIR}/kp_fe.log"
  is_running "$pf" && { log "k-protect frontend already running"; return; }
  log "starting k-protect frontend → :3300"
  (
    cd "${ROOT}/10_apps/02_k-protect/05_frontend"
    nohup npm run dev \
      >> "$lf" 2>&1 &
    echo $! > "$pf"
  )
}

# ── commands ──────────────────────────────────────────────────────────────────

cmd_start() {
  mkdir -p "${LOG_DIR}" "${PID_DIR}"

  log "ensuring docker infra (postgres, valkey, qdrant)…"
  ( cd "${ROOT}/11_infra" && docker compose up -d postgres valkey minio nats qdrant >/dev/null )
  for _ in $(seq 1 30); do
    docker exec tennetctl-postgres pg_isready -U tennetctl_admin -d tennetctl >/dev/null 2>&1 && break
    sleep 1
  done
  log "postgres ready"

  # tennetctl backend must be up before anything else
  start_tc_be
  log "waiting for tennetctl backend (:58000)…"
  wait_port 58000 "tennetctl backend"

  # k-forensics backend must be up before kprotect + demo-web
  start_kf_be
  log "waiting for k-forensics backend (:8100)…"
  wait_port 8100 "k-forensics backend"

  # now start the rest
  start_tc_fe
  start_kp_be
  start_demo
  start_kp_fe

  log ""
  log "  $(c_green 'tennetctl')   backend  → http://localhost:58000/docs"
  log "  $(c_green 'tennetctl')   frontend → http://localhost:53000"
  log "  $(c_green 'k-forensics') backend  → http://localhost:8100/docs"
  log "  $(c_green 'k-protect')   backend  → http://localhost:8200/docs"
  log "  $(c_green 'kbio demo')            → http://localhost:3200"
  log "  $(c_green 'k-protect')   frontend → http://localhost:3300"
  log ""
  log "  logs    → ./dev_all.sh logs [tc|kf|kp|demo|kpfe]"
  log "  stop    → ./dev_all.sh stop"
  log "  status  → ./dev_all.sh status"
}

cmd_stop() {
  stop_pid "tennetctl backend"    "${PID_DIR}/tc_be.pid"
  stop_pid "tennetctl frontend"   "${PID_DIR}/tc_fe.pid"
  stop_pid "k-forensics backend"  "${PID_DIR}/kf_be.pid"
  stop_pid "k-protect backend"    "${PID_DIR}/kp_be.pid"
  stop_pid "kbio demo-web"        "${PID_DIR}/demo.pid"
  stop_pid "k-protect frontend"   "${PID_DIR}/kp_fe.pid"
  log "all stopped"
}

cmd_restart() {
  cmd_stop
  cmd_start
}

cmd_status() {
  local ids=("tc_be:tennetctl backend:58000"
             "tc_fe:tennetctl frontend:53000"
             "kf_be:k-forensics backend:8100"
             "kp_be:k-protect backend:8200"
             "demo:kbio demo-web:3200"
             "kp_fe:k-protect frontend:3300")
  echo ""
  for entry in "${ids[@]}"; do
    local id label port
    id="${entry%%:*}"; rest="${entry#*:}"; label="${rest%:*}"; port="${rest##*:}"
    local pf="${PID_DIR}/${id}.pid"
    if is_running "$pf"; then
      printf '  %-28s %s  pid %-6s  :%s\n' "$label" "$(c_green 'UP  ')" "$(cat "$pf")" "$port"
    else
      printf '  %-28s %s\n' "$label" "$(c_red 'DOWN')"
    fi
  done
  echo ""
}

cmd_logs() {
  mkdir -p "${LOG_DIR}"
  local target="${1:-}"
  case "$target" in
    tc)   exec tail -F "${LOG_DIR}/tc_be.log"  "${LOG_DIR}/tc_fe.log" ;;
    kf)   exec tail -F "${LOG_DIR}/kf_be.log" ;;
    kp)   exec tail -F "${LOG_DIR}/kp_be.log"  "${LOG_DIR}/kp_fe.log" ;;
    demo) exec tail -F "${LOG_DIR}/demo.log" ;;
    kpfe) exec tail -F "${LOG_DIR}/kp_fe.log" ;;
    "")   exec tail -F "${LOG_DIR}/tc_be.log" "${LOG_DIR}/tc_fe.log" \
                       "${LOG_DIR}/kf_be.log" "${LOG_DIR}/kp_be.log" \
                       "${LOG_DIR}/demo.log"  "${LOG_DIR}/kp_fe.log" ;;
    *)    die "unknown target: $target  (use: tc|kf|kp|demo|kpfe)" ;;
  esac
}

# ── dispatch ──────────────────────────────────────────────────────────────────
case "${1:-start}" in
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  restart) cmd_restart ;;
  status)  cmd_status ;;
  logs)    cmd_logs "${2:-}" ;;
  *) die "usage: dev_all.sh [start|stop|restart|status|logs [tc|kf|kp|demo|kpfe]]" ;;
esac
