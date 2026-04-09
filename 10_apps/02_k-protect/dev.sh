#!/usr/bin/env bash
set -euo pipefail

# k-protect dev launcher — starts backend (8200) + checks tennetctl is running
# Prerequisites: tennetctl backend must be running on :58000
# Usage: ./dev.sh
# Stop: Ctrl+C

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== k-protect dev ==="

# ── Check tennetctl backend ──────────────────────────────────────────────────
echo "Checking tennetctl backend..."
if ! curl -sf http://localhost:58000/healthz > /dev/null 2>&1; then
    echo "ERROR: tennetctl not running on port 58000. Start it first."
    echo "  cd $(dirname "$SCRIPT_DIR") && ./dev.sh"
    exit 1
fi
echo "tennetctl OK"

# ── Backend ──────────────────────────────────────────────────────────────────
echo "Starting k-protect backend on port 8200..."
cd "$SCRIPT_DIR/04_backend"

export KP_TENNETCTL_API_URL="http://localhost:58000"
export KP_KBIO_API_URL="http://localhost:8100"
export ALLOWED_ORIGINS="http://localhost:3200,http://127.0.0.1:3200"

if [ ! -d ".venv" ]; then
    echo "Creating Python venv..."
    python3 -m venv .venv
    .venv/bin/pip install -e ".[dev]" 2>/dev/null || .venv/bin/pip install -e .
fi

.venv/bin/python -m uvicorn 01_core.app:app \
    --host 0.0.0.0 --port 8200 --reload \
    --reload-dir . \
    &
BACKEND_PID=$!

# ── Cleanup ──────────────────────────────────────────────────────────────────
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo ""
echo "  k-protect backend  http://localhost:8200"
echo "  k-protect healthz  http://localhost:8200/healthz"
echo "  tennetctl upstream http://localhost:58000/docs"
echo ""
echo "Press Ctrl+C to stop"
wait
