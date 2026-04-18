# Phase 35 Plan 03 — SUMMARY

**Plan:** 35-03 System Health dashboard
**Status:** ✅ Complete
**Date:** 2026-04-18

## What shipped
- Backend `/health` enhanced from a 3-line "healthy" to a structured subsystem report covering app version, DB connectivity, pool depth, modules (enabled + available), vault state, catalog counts, and NATS config
- Lifespan stashes the catalog upsert report on `app.state.catalog_report` so /health can surface it without re-scanning
- Frontend `/system/health` page with 5 cards (Database, Vault, Catalog, NATS, Modules) — auto-refresh every 30s, manual Refresh button, per-subsystem status Badge
- Type `SystemHealthReport` + hook `useSystemHealth`

## Files
- **Modified**
  - `backend/main.py` — added `Request` import, `_APP_VERSION`, `_nats_url_host`, rewrote `/health`, stashed catalog_report in lifespan
  - `frontend/src/types/api.ts` — `SystemHealthReport` type
- **Created**
  - `frontend/src/features/system/hooks/use-system-health.ts`
  - `frontend/src/app/(dashboard)/system/health/page.tsx` (240 lines)

## Verification
- `from backend import main` — imports clean
- `npx tsc --noEmit` — clean
- `npx next build` — success, `/system/health` registered (static)

## Decisions
- `/health` always returns 200 with per-subsystem `ok` flags — never 503. Reason: admin UI needs to load even when one subsystem is degraded; the UI uses Badge tone to convey severity.
- NATS status limited to `configured` + `url_host` — no live probe. Live probe requires awaiting the NATS client, which can hang and would need a timeout wrapper. v0.3.0 alerting will revisit.
- Vault `ok` derived from `hasattr(app.state, "vault")` — a coarse check sufficient for admin visibility; deeper probe (root key hash match + decrypt test) is overkill for this surface.
- Pool stats via `pool.get_size()` / `pool.get_idle_size()` — asyncpg native methods, no new dep.
- Version stored as `_APP_VERSION = "0.2.x"` constant at module level. Future: pull from pyproject.toml or package metadata once versioning gets formal.
- Catalog card shows `unreported` Badge when `catalog_report` is missing (e.g. boot failed). Reason: absence of data is diagnostic signal, not an error.

## Deferred
- Live NATS probe (v0.3.0)
- Worker lag metrics (monitoring module deep integration)
- Migration history browser — 🟢 severity
- Per-module deep health endpoints
- Apisix status card (would ride on Phase 33 sync worker data)
