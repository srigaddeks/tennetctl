#!/usr/bin/env bash
# k-forensics dev — starts backend gateway + frontend with hot reload
# Prerequisites: tennetctl backend must be running on :58000 (run ./dev.sh from project root)
# Usage: ./dev.sh
# Stop: Ctrl+C

set -e
cd "$(dirname "$0")"

# ── Config ──────────────────────────────────────────────────────────────────
KF_BACKEND_PORT=8100
KF_FRONTEND_PORT=3100
KF_TENNETCTL_API_URL="${KF_TENNETCTL_API_URL:-http://localhost:58000}"

# ── Check tennetctl backend ─────────────────────────────────────────────────
if ! curl -sf "${KF_TENNETCTL_API_URL}/healthz" > /dev/null 2>&1; then
  echo "⚠  tennetctl backend not reachable at ${KF_TENNETCTL_API_URL}"
  echo "   Start it first:  cd $(dirname "$0")/../.. && ./dev.sh"
  exit 1
fi
echo "✓  tennetctl backend healthy at ${KF_TENNETCTL_API_URL}"

# ── Backend (gateway) ──────────────────────────────────────────────────────
echo "▶  k-forensics backend  → http://localhost:${KF_BACKEND_PORT}"
KF_TENNETCTL_API_URL="${KF_TENNETCTL_API_URL}" \
ALLOWED_ORIGINS="http://localhost:${KF_FRONTEND_PORT},http://127.0.0.1:${KF_FRONTEND_PORT}" \
  04_backend/.venv/bin/python -m uvicorn 01_core.app:app \
    --app-dir 04_backend \
    --host 0.0.0.0 \
    --port "${KF_BACKEND_PORT}" \
    --reload \
    --reload-dir 04_backend \
    &
BACKEND_PID=$!

# ── Frontend ─────────────────────────────────────────────────────────────────
echo "▶  k-forensics frontend → http://localhost:${KF_FRONTEND_PORT}"
cd 06_frontend
NEXT_PUBLIC_API_URL="http://localhost:${KF_BACKEND_PORT}" \
  npm run dev -- --port "${KF_FRONTEND_PORT}" \
  &
FRONTEND_PID=$!
cd ..

# ── Cleanup ──────────────────────────────────────────────────────────────────
trap "echo ''; echo 'stopping...'; kill ${BACKEND_PID} ${FRONTEND_PID} 2>/dev/null; wait" INT TERM

echo ""
echo "  gateway  http://localhost:${KF_BACKEND_PORT}/healthz"
echo "  frontend http://localhost:${KF_FRONTEND_PORT}"
echo "  upstream http://localhost:58000/docs"
echo ""
echo "Ctrl+C to stop both"
wait
