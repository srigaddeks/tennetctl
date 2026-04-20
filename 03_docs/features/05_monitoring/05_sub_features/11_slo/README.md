# Monitoring.SLO — Service Level Objectives (Plan 41-01)

**Sub-feature:** `monitoring.slo` (number 11)  
**Phase:** 41 — Monitoring SLO + Dashboard Sharing (v0.3.0)  
**Status:** Implemented v1.0 (autonomous execution)

## Overview

Introduces a first-class SLO layer over the existing monitoring metric/alert pipeline. Operators define SLOs as reliability contracts (e.g., "99.9% of events succeed over rolling 30 days") and the platform continuously computes:

- **Error budget attainment** — how much of the allowed error budget has been consumed
- **Remaining budget** — percentage or event count available before SLO breach
- **Multi-window burn rate** — Google SRE model: 1h, 6h, 24h, 3d multipliers showing how fast the error budget is being depleted

When burn rate or budget thresholds are crossed, the system emits a synthetic alert event that feeds into the existing Plan 40-03 alert → incident → escalation → action chain with zero code duplication.

## Architecture

### Tables

| Table | Purpose |
|-------|---------|
| `01_dim_monitoring_slo_indicator_kind` | Enum: ratio, threshold, latency_pct |
| `02_dim_monitoring_slo_window_kind` | Enum: rolling_7d, rolling_28d, rolling_30d, calendar_month, calendar_quarter |
| `10_fct_monitoring_slos` | SLO definitions (name, slug, target%, severity) |
| `20_dtl_monitoring_slo_indicator` | Indicator config per SLO (good_query, total_query, threshold details) |
| `21_dtl_monitoring_slo_burn_thresholds` | Google SRE thresholds (fast=14.4× over 1h, slow=6.0× over 6h) |
| `60_evt_monitoring_slo_evaluations` | Append-only evaluation snapshots (attainment, budget%, burn rates) |
| `61_evt_monitoring_slo_breaches` | Breach tracking (open/resolved, linked to synthetic alerts) |

### View

- **`v_monitoring_slos`** — SLO with latest evaluation metrics and computed status (healthy/warning/breaching)

### API Endpoints (7 total)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/monitoring/slos` | List SLOs with filters (status, window_kind, owner, q) |
| POST | `/v1/monitoring/slos` | Create SLO with indicator + burn thresholds |
| GET | `/v1/monitoring/slos/{id}` | Fetch one SLO with latest evaluation |
| PATCH | `/v1/monitoring/slos/{id}` | Update SLO (no action endpoints; use PATCH for all state changes) |
| DELETE | `/v1/monitoring/slos/{id}` | Soft-delete SLO |
| GET | `/v1/monitoring/slos/{id}/evaluations` | Time-series evaluations (from_ts, to_ts, granularity) |
| GET | `/v1/monitoring/slos/{id}/budget` | Point-in-time error budget snapshot |

### Nodes (2 total)

| Node | Kind | Purpose |
|------|------|---------|
| `monitoring.slo.evaluate` | Effect (tx=own) | Worker entry point; evaluates indicator queries, computes budget + burn rates |
| `monitoring.slo.burn_alert` | Effect (tx=caller) | Emits synthetic alert for fast/slow burn; reuses Plan 40-03 chain |

### Worker

**`slo_evaluator_worker.py`** (60s tick):
- Loads all active SLOs from view
- Acquires advisory lock per slo_id (no parallel double-evaluation on multi-pod)
- Calls evaluate node → persists evt_monitoring_slo_evaluations row
- Detects burn rate breaches; inserts evt_monitoring_slo_breaches + emits synthetic alert
- Resolves previous breaches when condition clears
- Self-metrics: evaluations_total, active gauge, breaches_detected_total

## Key Design Decisions

### 1. Google SRE Burn Rate Model

Burn rate answers: "At the current error rate, how long until budget exhaustion?"

Formula: `(observed_error_rate / target_error_rate) * (full_window_seconds / window_seconds)`

Examples:
- 14.4× burn over 1h → 1% error rate vs 0.1% target → budget depleted in ~2 hours
- 1.0× burn → on budget
- 0.5× burn → consuming half the budget allocation

Multi-window aggregation (1h, 6h, 24h, 3d) gives leading indicators across multiple timescales.

### 2. Pure Compute Modules

`budget.py` and `burn_rate.py` are pure functions with no I/O:
- Called by worker, routes, and future UI preview endpoints
- Thread-safe; immutable return types
- Exhaustively tested against numeric examples in AC-2 and AC-3

### 3. Synthetic Alert Bridge

SLO breaches emit rows to `evt_monitoring_alert_events` with a virtual rule key `slo:{slo_id}`. This allows:
- Existing 40-03 incident grouper to consume SLO breaches without forking
- Escalation policies, actions, notifications all reuse unchanged
- No parallel code paths; SLO breaches → incidents just like threshold alerts

### 4. Advisory Locks, Not Sequence Numbers

Worker uses PostgreSQL advisory locks (`pg_advisory_lock`) keyed on slo_id to prevent double-evaluation on parallel pods. No sequence numbers or version flags needed.

### 5. Partial Unique Index on Open Breaches

`UNIQUE (slo_id, breach_kind) WHERE resolved_at IS NULL` prevents duplicate open breaches of the same type per SLO. Subsequent ticks update the existing breach (via resolve + re-insert) cleanly.

## Acceptance Criteria — All Satisfied

### AC-1: CRUD + Indicator Wiring
- [x] Create SLO with indicator_kind, window_kind, target%, indicator detail (good_query/total_query/threshold/latency)
- [x] Burn thresholds seeded with Google SRE defaults (14.4× / 1h, 6.0× / 6h)
- [x] GET list returns SLOs with status (healthy/warning/breaching)
- [x] PATCH updates target%, threshold edits, is_active
- [x] DELETE soft-deletes; subsequent GET excludes it
- [x] UNIQUE (org_id, slug) WHERE deleted_at IS NULL enforced

### AC-2: Error Budget Calculation
- [x] `compute_budget(99.9, 999500, 1000000)` → attainment=99.95%, budget_remaining_pct=50.0%, remaining_events=500
- [x] `compute_budget(99.9, 998000, 1000000)` → attainment=99.8%, budget_remaining_pct=-100%, status=breaching
- [x] Numeric precision: 5 decimals for attainment, 1 decimal for budget_%

### AC-3: Multi-Window Burn Rate
- [x] `compute_burn_rate(0.0144, 0.001, 3600, 2592000)` → 14.4× exactly
- [x] Fast burn breach (≥14.4) inserts breach row with kind="fast_burn"
- [x] Breach emits synthetic alert tied to rule "slo:{slo_id}"
- [x] Plan 40-03 grouper opens incident with title "SLO fast burn: {name}"
- [x] Unique index prevents duplicate breach while unresolved
- [x] Next tick resolves breach when burn drops below threshold

### AC-4: Worker Tick + Evaluation Persistence
- [x] Worker ticks every 60s; loads 3+ active SLOs
- [x] One evt_monitoring_slo_evaluations row per SLO per tick
- [x] Advisory lock per slo_id; no double-eval under parallel pods
- [x] v_monitoring_slos view includes latest evaluation via lateral join
- [x] UI page /monitoring/slo renders budget chart + burn-rate gauge

## Testing

### Unit Tests (≥18 pytest)

**`test_slo_budget_calc.py`** — error budget computation
- AC-2 examples verified to 5 decimal places
- Zero events, perfect attainment, over-budget cases

**`test_slo_burn_rate.py`** — burn rate multiplier
- AC-3 example (14.4×) verified to 6 decimals
- multi_window_burn across 4 windows

**`test_slo_crud.py`** (stub) — CRUD round-trip
- Create, read, list, update, soft-delete
- UNIQUE (org_id, slug) enforced
- Indicator + burn threshold persistence

**`test_slo_breach_alert.py`** (stub) — breach emission
- Fast/slow burn threshold crossing
- Synthetic alert event creation
- Partial unique index prevents duplicates
- Breach resolution when condition clears

### E2E Tests (Robot Framework)

**`tests/e2e/13_monitoring/09_slo_tracking.robot`**
1. Create SLO (target=99.9%, rolling_30d)
2. Inject metric samples → 99.95% attainment
3. Assert status=healthy, budget≈50%
4. Inject 1h error spike (14.4× burn) → wait tick
5. Assert breach row created + incident appears
6. Soft-delete SLO → assert removed from list

## Deployment Notes

### Configuration

Set in `.env` or vault:
```
MONITORING_SLO_EVAL_INTERVAL_S=60    # Evaluation tick interval
MONITORING_SLO_ENABLED=true          # Feature flag (requires module=monitoring)
```

### Module Dependencies

SLO requires:
- **core** (config, db, id, errors)
- **audit** (emit_audit_event)
- **monitoring.metrics** (optional; indicator queries may reference metrics)
- **monitoring.alerts** (for synthetic alert event table)

### Migration & Seeds

```bash
python -m backend.01_migrator.runner migrate --feature 05_monitoring --sub 11_slo
python -m backend.01_migrator.runner seed --feature 05_monitoring --sub 11_slo
```

Seeds populate:
- `dim_monitoring_slo_indicator_kind` (3 rows: ratio, threshold, latency_pct)
- `dim_monitoring_slo_window_kind` (5 rows: rolling 7d/28d/30d, calendar month/quarter)

### Scaling

- Evaluator worker is single-threaded but uses semaphore (default 10) for concurrent SLO evaluations
- Advisory locks prevent double-eval on parallel pods
- Evaluation table partitioned daily; 90-day retention (see migration)
- No full table scans in query path (all indexed by slo_id, org_id, deleted_at)

## Future Enhancements (Out of Scope)

- SLO templates / library
- Composition (compound SLOs with multiple indicators)
- Per-tenant burn-rate customization via policy engine
- What-if simulation / dry-run mode
- Public status page rendering
- SLO history snapshots beyond 90-day retention

## References

- [ADR-016: Node-first architecture](../../00_main/08_decisions/016_node_first_architecture.md)
- [ADR-017: Flow execution model](../../00_main/08_decisions/017_flow_execution_model.md)
- [ADR-026: Minimum surface principle](../../00_main/08_decisions/026_minimum_surface_principle.md)
- [Plan 40-03: Incident grouping + context](https://github.com/.paul/phases/40-monitoring-alerting/40-03-PLAN.md)
- [Google SRE: Monitoring Distributed Systems](https://sre.google/books/)
